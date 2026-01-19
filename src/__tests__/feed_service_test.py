"""Feed service tests."""

from unittest.mock import patch

import feedparser

from __tests__.base import BaseTestCase
from schemas import SourceIn, SubscriptionOut


class TestFeedService(BaseTestCase):
    """Test feed service functionality."""

    def _create_user_and_subscription(self, user_id: int = 1) -> SubscriptionOut:
        """Create a user and subscription for testing."""
        self.create_user_direct(f"user{user_id}")
        source = self.source_storage.create(
            SourceIn(name="HN Best", resource_url="https://hnrss.org/best")
        )
        return self.subscription_storage.create(user_id, source.id)

    def _fetch_items_from_file(
        self,
        subscription: SubscriptionOut,
        filename: str = "src/__tests__/test_data/hn_best_example.xml",
    ):
        """Fetch items from test data file for a subscription."""
        with open(filename, encoding="utf-8") as file:
            feed_data = file.read()

        with patch.object(feedparser, "parse", return_value=feedparser.parse(feed_data)):
            return self.feed_service.fetch_and_save_items(subscription.id)

    def test_fetch_feed(self):
        """Test fetching and saving feed items."""
        subscription = self._create_user_and_subscription()
        self._fetch_items_from_file(subscription)

        feed_items = self.feed_service.get_items(1, 0, 100)
        assert len(feed_items) == 30
        assert feed_items[0].title is not None
        assert feed_items[0].source_name is not None

    def test_generate_and_save_user_feed(self):
        """Test generating user feed from feed items."""
        user_id = 1
        subscription = self._create_user_and_subscription(user_id)
        self._fetch_items_from_file(
            subscription, filename="src/__tests__/test_data/hn_best_example_short.xml"
        )
        feed_items = self.feed_service.get_items(user_id, 0, 100)

        # Generate user feed
        self.feed_service.generate_user_feed(user_id)
        saved_user_feed = self.feed_storage.get_user_feed(user_id)

        # Verify feed was generated
        assert saved_user_feed is not None
        assert saved_user_feed.user_id == user_id
        assert len(saved_user_feed.user_feed_items) == len(feed_items)

        # Sort and compare
        feed_items.sort(key=lambda x: x.id)
        saved_user_feed.user_feed_items.sort(key=lambda x: x.feed_item_id)

        for i, item in enumerate(saved_user_feed.user_feed_items):
            assert item.feed_item_id == feed_items[i].id
            assert item.title == feed_items[i].title
            assert item.source_name == feed_items[i].source_name
            assert item.user_id == user_id

    def test_regenerate_user_feed_preserves_unread(self):
        """Test that regenerating feed preserves unread items."""
        user_id = 1

        # Create user and subscription
        subscription = self._create_user_and_subscription(user_id)

        # Create initial feed with short xml
        self._fetch_items_from_file(
            subscription, filename="src/__tests__/test_data/hn_best_example_short.xml"
        )
        self.feed_service.generate_user_feed(user_id)

        # Add more items with full xml
        self._fetch_items_from_file(
            subscription, filename="src/__tests__/test_data/hn_best_example.xml"
        )
        feed_items = self.feed_service.get_items(user_id, 0, 100)

        # Regenerate feed
        self.feed_service.generate_user_feed(user_id)
        saved_user_feed = self.feed_storage.get_user_feed(user_id)

        # Verify all items are present
        assert saved_user_feed is not None
        assert len(saved_user_feed.user_feed_items) == len(feed_items)
