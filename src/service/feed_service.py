"""Feed service - handles feed fetching and generation."""

import logging

from api.exceptions import EntityNotFoundException, ParserNotFoundException
from repository.feed_storage import FeedStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from schemas import FeedItemIn, ItemState, UserFeedOut
from schemas.feeds import UserFeedIn, UserFeedItemIn
from service.data_extractor import DataExtractor
from service.parser.source_parser_strategy import get_parser
from utils import config

logger = logging.getLogger(__name__)


class FeedService:
    def __init__(
        self,
        feed_storage: FeedStorage,
        subscription_storage: SubscriptionStorage,
        source_storage: SourceStorage,
        data_extractor: DataExtractor,
    ) -> None:
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
        self.source_storage = source_storage
        self.data_extractor = data_extractor

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

        parser = get_parser(source)
        if not parser:
            raise ParserNotFoundException(source.name or "unknown")

        items = parser(source)

        # Optionally summarize items
        for item in items:
            try:
                if config.ENABLE_SUMMARIZATION and item.article_url:
                    title, summary = self.data_extractor.extract_and_summarize(
                        item.title, item.article_url, item.source_name
                    )
                    if title:
                        item.title = title
                    if summary:
                        item.summary = summary
            except Exception as e:
                logger.warning(f"Failed to summarize item '{item.title}': {e}")

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

        new_feed = UserFeedIn(
            user_id=user_id,
            is_active=True,
            user_feed_items=items,
        )

        self.feed_storage.save_user_feed(new_feed)

        if active_feed:
            self.feed_storage.deactivate_user_feed(active_feed.id)

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
