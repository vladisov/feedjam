"""Feed service - handles feed fetching and generation."""

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

    def mark_read(self, user_id: int, item_id: int) -> bool:
        """Mark a feed item as read."""
        item = self.feed_storage.get_item(user_id, item_id)
        if not item:
            return False

        # Update ephemeral state
        result = self.feed_storage.mark_as_read(user_id, item_id)

        # Sync to persistent state
        if result and item.feed_item_id:
            self.user_item_state_storage.set_read(user_id, item.feed_item_id, True)

        return result

    def fetch_and_save_items(self, subscription_id: int) -> list[FeedItemIn]:
        """Fetch and save feed items for a subscription."""
        subscription = self.subscription_storage.get(subscription_id)
        if not subscription:
            raise EntityNotFoundException("Subscription", subscription_id)

        source = self.source_storage.get(subscription.source_id)
        if not source:
            raise EntityNotFoundException("Source", subscription.source_id)

        parser = get_parser_for_source(source)
        if not parser:
            raise ParserNotFoundException(source.source_type or "unknown")

        items = parser.parse(source)

        # Batch process items with LLM (summarize, extract topics, score quality)
        if config.ENABLE_SUMMARIZATION and items:
            try:
                items = self.content_processor.process_items_smart(items)
            except Exception as e:
                logger.warning(f"Failed to process items: {e}")

        self.feed_storage.save_items(source, items)
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

        items = [self._feed_item_to_user_feed_item(item, user_id) for item in recent_items]
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

        new_feed = UserFeedIn(
            user_id=user_id,
            is_active=True,
            user_feed_items=items,
        )

        self.feed_storage.save_user_feed(new_feed)

        if active_feed:
            self.feed_storage.deactivate_user_feed(active_feed.id)

    def toggle_like(self, user_id: int, item_id: int) -> dict:
        """Toggle like for a feed item and update like history."""
        success, source_name, feed_item_id, is_liked = self.feed_storage.toggle_like(user_id, item_id)
        if not success:
            raise EntityNotFoundException("FeedItem", item_id)

        # Update like history
        if source_name:
            if is_liked:
                self.like_history_storage.increment_like(user_id, source_name)
            else:
                self.like_history_storage.decrement_like(user_id, source_name)

        # Sync to persistent state
        if feed_item_id:
            self.user_item_state_storage.set_liked(user_id, feed_item_id, is_liked)

        return {"liked": is_liked}

    def toggle_dislike(self, user_id: int, item_id: int) -> dict:
        """Toggle dislike for a feed item and update like history."""
        success, source_name, feed_item_id, is_disliked = self.feed_storage.toggle_dislike(user_id, item_id)
        if not success:
            raise EntityNotFoundException("FeedItem", item_id)

        # Update like history
        if source_name:
            if is_disliked:
                self.like_history_storage.increment_dislike(user_id, source_name)
            else:
                self.like_history_storage.decrement_dislike(user_id, source_name)

        # Sync to persistent state
        if feed_item_id:
            self.user_item_state_storage.set_disliked(user_id, feed_item_id, is_disliked)

        return {"disliked": is_disliked}

    def toggle_star(self, user_id: int, item_id: int) -> dict:
        """Toggle star (save for later) for a feed item."""
        success, feed_item_id, is_starred = self.feed_storage.toggle_star(user_id, item_id)
        if not success:
            raise EntityNotFoundException("FeedItem", item_id)

        if feed_item_id:
            self.user_item_state_storage.set_starred(user_id, feed_item_id, is_starred)

        return {"starred": is_starred}

    def toggle_hide(self, user_id: int, item_id: int) -> dict:
        """Toggle hide for a feed item."""
        success, feed_item_id, is_hidden = self.feed_storage.toggle_hide(user_id, item_id)
        if not success:
            raise EntityNotFoundException("FeedItem", item_id)

        if feed_item_id:
            self.user_item_state_storage.set_hidden(user_id, feed_item_id, is_hidden)

        return {"hidden": is_hidden}

    def hide_read_items(self, user_id: int) -> dict:
        """Hide all read items for a user."""
        count, feed_item_ids = self.feed_storage.hide_read_items(user_id)

        # Sync to persistent state
        if feed_item_ids:
            self.user_item_state_storage.bulk_set_hidden(user_id, feed_item_ids)

        return {"hidden_count": count}

    def mark_all_read(self, user_id: int) -> dict:
        """Mark all unread items as read for a user."""
        count, feed_item_ids = self.feed_storage.mark_all_read(user_id)

        # Sync to persistent state
        if feed_item_ids:
            self.user_item_state_storage.bulk_set_read(user_id, feed_item_ids)

        return {"read_count": count}

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

    def _get_new_items(
        self, user_id: int, seen_ids: set[int]
    ) -> list[UserFeedItemIn]:
        """Get new feed items not already seen."""
        all_items = self.get_items(user_id)
        new_items = [item for item in all_items if item.id not in seen_ids]
        return [self._feed_item_to_user_feed_item(item, user_id) for item in new_items]

    def _feed_item_to_user_feed_item(self, item: FeedItem, user_id: int) -> UserFeedItemIn:
        """Convert a FeedItem model to UserFeedItemIn schema."""
        return UserFeedItemIn(
            feed_item_id=item.id,
            user_id=user_id,
            title=item.title,
            source_name=item.source_name,
            state=ItemState(),
            description=item.description or "",
            article_url=item.article_url,
            comments_url=item.comments_url,
            points=item.points,
            views=item.views,
            summary=item.summary,
        )
