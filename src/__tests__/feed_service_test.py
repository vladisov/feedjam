"""Feed service tests."""

from unittest.mock import patch

import feedparser

from __tests__.base import BaseTestCase
from schemas import SubscriptionIn, SubscriptionOut


class TestFeedService(BaseTestCase):
    """Test feed service functionality."""

    def _create_subscription_via_api(
        self, resource_url: str = "https://hnrss.org/best", user_id: int = 1
    ) -> SubscriptionOut:
        """Create a subscription via API."""
        subscription = SubscriptionIn(resource_url=resource_url, user_id=user_id)
        response = self.client.post("/subscriptions/", json=subscription.model_dump())
        return SubscriptionOut(**response.json())

    def _create_hn_feed_items(
        self,
        user_id: int = 1,
        filename: str = "src/__tests__/test_data/hn_best_example.xml",
    ):
        """Create feed items from test data."""
        # Create user first
        self.create_user_direct(f"user{user_id}")

        # Create subscription
        subscription = self._create_subscription_via_api(user_id=user_id)

        # Load test data
        with open(filename, encoding="utf-8") as file:
            hn_feed_data = file.read()

        # Mock feedparser to return test data
        with patch.object(feedparser, "parse", return_value=feedparser.parse(hn_feed_data)):
            items = self.feed_service.fetch_and_save_items(subscription.id)
            return items, subscription

    def test_fetch_feed(self):
        """Test fetching and saving feed items."""
        items, _ = self._create_hn_feed_items()

        feed_items = self.feed_service.get_items(1, 0, 100)
        assert len(feed_items) == 30
        assert feed_items[0].title is not None
        assert feed_items[0].source_name is not None

    def test_generate_and_save_user_feed(self):
        """Test generating user feed from feed items."""
        user_id = 1
        _, _ = self._create_hn_feed_items(
            user_id, filename="src/__tests__/test_data/hn_best_example_short.xml"
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

        # Create initial feed
        _, _ = self._create_hn_feed_items(
            user_id, filename="src/__tests__/test_data/hn_best_example_short.xml"
        )
        self.feed_service.generate_user_feed(user_id)

        # Add more items
        _, _ = self._create_hn_feed_items(
            user_id, filename="src/__tests__/test_data/hn_best_example.xml"
        )
        feed_items = self.feed_service.get_items(user_id, 0, 100)

        # Regenerate feed
        self.feed_service.generate_user_feed(user_id)
        saved_user_feed = self.feed_storage.get_user_feed(user_id)

        # Verify all items are present
        assert saved_user_feed is not None
        assert len(saved_user_feed.user_feed_items) == len(feed_items)
