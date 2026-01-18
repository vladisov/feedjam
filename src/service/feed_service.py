"""Feed service - handles feed fetching and generation."""

from api.exceptions import EntityNotFoundException, ParserNotFoundException
from repository.feed_storage import FeedStorage
from repository.like_history_storage import LikeHistoryStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
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
    ) -> None:
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
        self.source_storage = source_storage
        self.content_processor = content_processor
        self.ranking_service = ranking_service
        self.like_history_storage = like_history_storage

    def mark_read(self, user_id: int, item_id: int) -> bool:
        """Mark a feed item as read."""
        return self.feed_storage.mark_as_read(user_id, item_id)

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
                items = self.content_processor.process_items(items)
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

    def generate_user_feed(self, user_id: int) -> None:
        """Generate and save a new user feed."""
        active_feed = self.feed_storage.get_active_user_feed(user_id)

        # Preserve unread items from active feed
        items = self._get_unread_items(active_feed)

        # Add new items
        items += self._get_new_items(user_id, items)

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
        success, source_name, is_liked = self.feed_storage.toggle_like(user_id, item_id)
        if not success:
            raise EntityNotFoundException("FeedItem", item_id)

        # Update like history if we have a source name
        if source_name:
            if is_liked:
                self.like_history_storage.increment_like(user_id, source_name)
            else:
                self.like_history_storage.decrement_like(user_id, source_name)

        return {"liked": is_liked}

    def toggle_dislike(self, user_id: int, item_id: int) -> dict:
        """Toggle dislike for a feed item and update like history."""
        success, source_name, is_disliked = self.feed_storage.toggle_dislike(user_id, item_id)
        if not success:
            raise EntityNotFoundException("FeedItem", item_id)

        # Update like history if we have a source name
        if source_name:
            if is_disliked:
                self.like_history_storage.increment_dislike(user_id, source_name)
            else:
                self.like_history_storage.decrement_dislike(user_id, source_name)

        return {"disliked": is_disliked}

    def toggle_star(self, user_id: int, item_id: int) -> dict:
        """Toggle star (save for later) for a feed item."""
        success, is_starred = self.feed_storage.toggle_star(user_id, item_id)
        if not success:
            raise EntityNotFoundException("FeedItem", item_id)
        return {"starred": is_starred}

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

    def _get_new_items(
        self, user_id: int, existing_items: list[UserFeedItemIn]
    ) -> list[UserFeedItemIn]:
        """Get new feed items not in existing items."""
        existing_ids = {item.feed_item_id for item in existing_items}

        all_items = self.get_items(user_id)
        new_items = [item for item in all_items if item.id not in existing_ids]

        return [
            UserFeedItemIn(
                feed_item_id=item.id,
                user_id=user_id,
                title=item.title,
                source_name=item.source_name,
                state=ItemState(),
                description=item.description or "",
                comments_url=item.comments_url,
                article_url=item.article_url,
                points=item.points,
                summary=item.summary,
                views=item.views,
            )
            for item in new_items
        ]
