"""Feed service - handles feed fetching and generation."""

import time

from sqlalchemy import select

from api.exceptions import EntityNotFoundException, ParserNotFoundException
from model.feed import FeedItem
from repository.feed_storage import FeedStorage
from repository.like_history_storage import LikeHistoryStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from repository.user_item_state_storage import UserItemStateStorage
from schemas import FeedItemIn, ItemState, UserFeedOut
from schemas.feeds import UserFeedIn, UserFeedItemIn
from service.content_processor import ContentProcessor
from service.parser import get_parser_for_source
from service.ranking_service import RankingService
from utils import config
from utils.logger import get_logger

logger = get_logger(__name__)


class FeedService:
    def __init__(
        self,
        feed_storage: FeedStorage,
        subscription_storage: SubscriptionStorage,
        source_storage: SourceStorage,
        content_processor: ContentProcessor,
        ranking_service: RankingService,
        like_history_storage: LikeHistoryStorage,
        user_item_state_storage: UserItemStateStorage,
    ) -> None:
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
        self.source_storage = source_storage
        self.content_processor = content_processor
        self.ranking_service = ranking_service
        self.like_history_storage = like_history_storage
        self.user_item_state_storage = user_item_state_storage

    def mark_read(self, user_id: int, feed_item_id: int) -> bool:
        """Mark a feed item as read."""
        # Validate feed_item exists
        if not self._feed_item_exists(feed_item_id):
            return False
        self.user_item_state_storage.set_read(user_id, feed_item_id, True)
        return True

    def _feed_item_exists(self, feed_item_id: int) -> bool:
        """Check if a feed item exists."""
        stmt = select(FeedItem.id).where(FeedItem.id == feed_item_id)
        result = self.feed_storage.db.execute(stmt).scalar_one_or_none()
        return result is not None

    def fetch_and_save_items(self, subscription_id: int) -> list[FeedItemIn]:
        """Fetch and save feed items for a subscription."""
        subscription = self.subscription_storage.get(subscription_id)
        if not subscription:
            raise EntityNotFoundException("Subscription", subscription_id)

        source = self.source_storage.get(subscription.source_id)
        if not source:
            raise EntityNotFoundException("Source", subscription.source_id)

        logger.info(
            f"Fetching items: user={subscription.user_id} subscription={subscription_id} "
            f"source={source.name} type={source.source_type} url={source.resource_url}"
        )

        parser = get_parser_for_source(source)
        if not parser:
            logger.error(f"No parser found for source type: {source.source_type}")
            raise ParserNotFoundException(source.source_type or "unknown")

        parser_name = parser.__class__.__name__
        logger.info(f"Selected parser: {parser_name} for source: {source.name}")

        start_time = time.time()
        try:
            items = parser.parse(source)
        except Exception as e:
            logger.error(f"Parser {parser_name} failed for {source.name}: {e}", exc_info=True)
            raise

        parse_duration = time.time() - start_time
        logger.info(
            f"Parser {parser_name} returned {len(items)} items "
            f"in {parse_duration:.2f}s for source: {source.name}"
        )

        # Batch process items with LLM (summarize, extract topics, score quality)
        if config.ENABLE_SUMMARIZATION and items:
            try:
                process_start = time.time()
                items = self.content_processor.process_items_smart(items)
                process_duration = time.time() - process_start
                logger.info(
                    f"Content processing completed: {len(items)} items "
                    f"in {process_duration:.2f}s for source: {source.name}"
                )
            except Exception as e:
                logger.warning(f"Content processing failed for {source.name}: {e}")

        self.feed_storage.save_items(source, items)
        logger.info(f"Saved {len(items)} items to storage for source: {source.name}")

        return items

    def get_items(self, user_id: int, skip: int = 0, limit: int = 100):
        """Get feed items for a user."""
        return self.feed_storage.get_items_by_user(user_id, skip, limit)

    def get_user_feed(self, user_id: int) -> UserFeedOut | None:
        """Get the active user feed."""
        return self.feed_storage.get_user_feed(user_id)

    def get_daily_digest(self, user_id: int, top_n: int = 5) -> list[UserFeedItemIn]:
        """Get top N items from the last 24 hours, ranked by interests.

        Returns a digest of the best items across all subscribed sources.
        """
        recent_items = self.feed_storage.get_recent_items_by_user(user_id, hours=24, limit=100)

        if not recent_items:
            return []

        # Fetch user states for all items in batch
        feed_item_ids = [item.id for item in recent_items]
        states_map = self.user_item_state_storage.get_states_batch(user_id, feed_item_ids)

        def get_item_state(feed_item_id: int) -> ItemState:
            state = states_map.get(feed_item_id)
            if not state:
                return ItemState()
            return ItemState(
                read=state.read,
                like=state.liked,
                dislike=state.disliked,
                star=state.starred,
                hide=state.hidden,
            )

        items = [
            self._feed_item_to_user_feed_item(item, user_id, get_item_state(item.id))
            for item in recent_items
        ]
        ranked = self.ranking_service.compute_rank_scores(user_id, items)
        return ranked[:top_n]

    def generate_user_feed(self, user_id: int) -> None:
        """Generate and save a new user feed."""
        active_feed = self.feed_storage.get_user_feed(user_id)

        # Preserve unread items from active feed
        items = self._get_unread_items(active_feed)

        # Get IDs to exclude: active feed items + all historically read items
        seen_ids = self._get_seen_item_ids(active_feed, user_id)

        # Add new items (excluding already-seen items)
        items += self._get_new_items(user_id, seen_ids)

        # Apply personalized ranking
        items = self.ranking_service.compute_rank_scores(user_id, items)

        # Deactivate ALL existing feeds first to prevent race conditions
        self.feed_storage.deactivate_all_user_feeds(user_id)

        new_feed = UserFeedIn(
            user_id=user_id,
            is_active=True,
            user_feed_items=items,
        )

        self.feed_storage.save_user_feed(new_feed)

    def toggle_like(self, user_id: int, feed_item_id: int) -> dict:
        """Toggle like for a feed item and update like history."""
        is_liked, source_name = self.user_item_state_storage.toggle_liked(user_id, feed_item_id)
        if source_name:
            self._update_like_history(user_id, source_name, is_liked, is_like=True)
        return {"liked": is_liked}

    def toggle_dislike(self, user_id: int, feed_item_id: int) -> dict:
        """Toggle dislike for a feed item and update like history."""
        is_disliked, source_name = self.user_item_state_storage.toggle_disliked(
            user_id, feed_item_id
        )
        if source_name:
            self._update_like_history(user_id, source_name, is_disliked, is_like=False)
        return {"disliked": is_disliked}

    def toggle_star(self, user_id: int, feed_item_id: int) -> dict:
        """Toggle star (save for later) for a feed item."""
        is_starred = self.user_item_state_storage.toggle_starred(user_id, feed_item_id)
        return {"starred": is_starred}

    def toggle_hide(self, user_id: int, feed_item_id: int) -> dict:
        """Toggle hide for a feed item.

        Hide acts as a negative signal for ranking (decreases source affinity).
        """
        is_hidden, source_name = self.user_item_state_storage.toggle_hidden(user_id, feed_item_id)
        if source_name:
            self._update_like_history(user_id, source_name, is_hidden, is_like=False)
        return {"hidden": is_hidden}

    def _update_like_history(
        self, user_id: int, source_name: str, is_active: bool, *, is_like: bool
    ) -> None:
        """Update like history for a source."""
        storage = self.like_history_storage
        if is_like:
            method = storage.increment_like if is_active else storage.decrement_like
        else:
            method = storage.increment_dislike if is_active else storage.decrement_dislike
        method(user_id, source_name)

    def hide_read_items(self, user_id: int) -> dict:
        """Hide all read items for a user."""
        # Get feed_item_ids from active feed
        active_ids = self.user_item_state_storage.get_active_feed_item_ids(user_id)
        # Filter to read but not hidden
        to_hide = self.user_item_state_storage.get_read_unhidden_item_ids(user_id, active_ids)
        # Bulk hide
        if to_hide:
            self.user_item_state_storage.bulk_set_hidden(user_id, to_hide)
        return {"hidden_count": len(to_hide)}

    def mark_all_read(self, user_id: int) -> dict:
        """Mark all unread items as read for a user."""
        # Get feed_item_ids from active feed
        active_ids = self.user_item_state_storage.get_active_feed_item_ids(user_id)
        # Filter to unread and not hidden
        to_read = self.user_item_state_storage.get_unread_unhidden_item_ids(user_id, active_ids)
        # Bulk mark read
        if to_read:
            self.user_item_state_storage.bulk_set_read(user_id, to_read)
        return {"read_count": len(to_read)}

    def search_items(
        self,
        user_id: int,
        liked: bool | None = None,
        disliked: bool | None = None,
        starred: bool | None = None,
        read: bool | None = None,
        hidden: bool | None = None,
        text: str | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """Search user's historical items by state filters.

        When state filters (liked, starred, etc.) are used, searches
        persistent UserItemState. Otherwise searches active feed.
        """
        return self.user_item_state_storage.search(
            user_id=user_id,
            liked=liked,
            disliked=disliked,
            starred=starred,
            read=read,
            hidden=hidden,
            text=text,
            source=source,
            limit=limit,
            offset=offset,
        )

    def _get_unread_items(self, active_feed: UserFeedOut | None) -> list[UserFeedItemIn]:
        """Get unread items from the active feed."""
        if not active_feed:
            return []

        return [
            UserFeedItemIn(
                feed_item_id=item.feed_item_id,
                user_id=item.user_id,
                title=item.title,
                source_name=item.source_name or "",
                state=item.state,
                description=item.description,
                comments_url=item.comments_url,
                article_url=item.article_url,
                points=item.points,
                summary=item.summary,
                views=item.views,
            )
            for item in active_feed.user_feed_items
            if not item.state.read
        ]

    def _get_seen_item_ids(self, active_feed: UserFeedOut | None, user_id: int) -> set[int]:
        """Get IDs of items to exclude from new feed.

        Combines:
        - All items in active feed (read + unread)
        - All historically read items from persistent state
        """
        seen_ids = set()

        # Items in current active feed
        if active_feed:
            seen_ids.update(item.feed_item_id for item in active_feed.user_feed_items)

        # Historically read items (persistent)
        seen_ids.update(self.user_item_state_storage.get_read_item_ids(user_id))

        return seen_ids

    def _get_new_items(self, user_id: int, seen_ids: set[int]) -> list[UserFeedItemIn]:
        """Get new feed items not already seen."""
        all_items = self.get_items(user_id)
        new_items = [item for item in all_items if item.id not in seen_ids]
        return [self._feed_item_to_user_feed_item(item, user_id) for item in new_items]

    def _feed_item_to_user_feed_item(
        self,
        item: FeedItem,
        user_id: int,
        state: ItemState | None = None,
    ) -> UserFeedItemIn:
        """Convert a FeedItem model to UserFeedItemIn schema."""
        return UserFeedItemIn(
            feed_item_id=item.id,
            user_id=user_id,
            title=item.title,
            source_name=item.source_name,
            state=state or ItemState(),
            description=item.description or "",
            article_url=item.article_url,
            comments_url=item.comments_url,
            points=item.points,
            views=item.views,
            summary=item.summary,
            created_at=item.created_at,
        )
