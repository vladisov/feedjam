from datetime import datetime
from unittest.mock import patch
from service.feed_service import FeedService
from model.model import Source, Subscription

from repository.feed_storage import FeedStorage
from repository.subscription_storage import SubscriptionStorage
from tests.test_app import override_get_db
import feedparser


def test_fetch_feed(cleanup):
    db = next(override_get_db())
    feed_storage = FeedStorage(db)
    subscription_storage = SubscriptionStorage(db)
    service = FeedService(feed_storage, subscription_storage)
    subscription_id = 1

    source = Source(id=1, name="hackernews", resource_url="https://hnrss.org/best",
                    created_at=datetime.now(), is_active=True)
    subscription = Subscription(id=subscription_id, source_id=1, user_id=1,
                                source=source)

    with open('tests/test_data/hn_best_example.xml', 'r') as file:
        hn_feed_data = file.read()

    with patch.object(subscription_storage, 'get_subscription') as mock_get_subscription, \
            patch.object(feedparser, 'parse', return_value=feedparser.parse(hn_feed_data)):

        mock_get_subscription.return_value = subscription

        items = service.fetch_feed(subscription_id)

        mock_get_subscription.assert_called_once_with(subscription_id)
        assert len(items) == 30
        assert items[0].source_id == subscription.source_id
        assert items[0].title == "Privatisation has been a costly failure in Britain"
        # assert mock_add_feed_items.call_count == 1
        assert items[29].source_id == subscription.source_id
        assert items[29].title == "Why I Hate Frameworks (2005)"

        items = service.get_feed_items(1, 0, 100)
        assert len(items) == 30
        assert items[0].source_id == subscription.source_id
        assert items[0].title == "Privatisation has been a costly failure in Britain"
        # assert mock_add_feed_items.call_count == 1
        assert items[29].source_id == subscription.source_id
        assert items[29].title == "Why I Hate Frameworks (2005)"
