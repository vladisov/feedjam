from datetime import datetime
from unittest.mock import patch
from model.source import Source
from repository.source_storage import SourceStorage
from service.data_extractor import DataExtractor
from service.feed_service import FeedService
from model.subscription import Subscription

from repository.feed_storage import FeedStorage
from repository.subscription_storage import SubscriptionStorage
from tests.test_app import override_get_db
import feedparser


def _create_hn_feed_items(feed_service: FeedService,
                          subscription_storage: SubscriptionStorage,
                          source_storage: SourceStorage,
                          user_id=1, filename="tests/test_data/hn_best_example.xml"):
    subscription_id = 1
    source = Source(id=1, name="hackernews", resource_url="https://hnrss.org/best",
                    created_at=datetime.now(), is_active=True)
    subscription = Subscription(
        id=subscription_id, source_id=1, user_id=user_id)
    with open(filename, 'r') as file:
        hn_feed_data = file.read()

    with patch.object(subscription_storage, 'get_subscription') as mock_get_subscription, \
            patch.object(source_storage, 'get_source') as mock_get_source, \
            patch.object(feedparser, 'parse', return_value=feedparser.parse(hn_feed_data)):

        mock_get_subscription.return_value = subscription
        mock_get_source.return_value = source

        items = feed_service.fetch_and_save_feed_items(subscription_id)
        mock_get_subscription.assert_called_once_with(subscription_id)

        return items, subscription


def test_fetch_feed(cleanup):
    db = next(override_get_db())
    feed_storage = FeedStorage(db)
    subscription_storage = SubscriptionStorage(db)
    source_storage = SourceStorage(db)
    data_extractor = DataExtractor("dummy")
    service = FeedService(feed_storage, subscription_storage,
                          source_storage, data_extractor)
    _, subscription = _create_hn_feed_items(
        service, subscription_storage, source_storage)

    items = service.get_feed_items(1, 0, 100)
    assert len(items) == 30
    assert items[0].title is not None
    assert items[29].title is not None


def test_generate_and_save_user_feed(cleanup):
    db = next(override_get_db())
    feed_storage = FeedStorage(db)
    subscription_storage = SubscriptionStorage(db)
    data_extractor = DataExtractor("dummy")
    source_storage = SourceStorage(db)

    service = FeedService(feed_storage, subscription_storage,
                          source_storage, data_extractor)
    user_id = 1

    _, _ = _create_hn_feed_items(service, subscription_storage, source_storage,
                                 user_id, filename="tests/test_data/hn_best_example_short.xml")
    feed_items = service.get_feed_items(user_id, 0, 100)

    service.generate_and_save_user_feed(user_id)

    saved_user_feed = feed_storage.get_user_feed(
        user_id)

    # Check that the saved feed matches the generated feed
    feed_items.sort(key=lambda x: x.id)
    assert saved_user_feed.user_id == user_id
    assert len(saved_user_feed.user_feed_items) == len(feed_items)
    for i in range(len(feed_items)):
        assert saved_user_feed.user_feed_items[i].feed_item_id == feed_items[i].id
        assert saved_user_feed.user_feed_items[i].user_id == user_id

    _, _ = _create_hn_feed_items(service, subscription_storage, source_storage,
                                 user_id, filename="tests/test_data/hn_best_example.xml")
    feed_items_upd = service.get_feed_items(user_id, 0, 100)

    service.generate_and_save_user_feed(user_id)

    saved_user_feed = feed_storage.get_user_feed(user_id)

    # Check that the saved feed matches the generated feed
    feed_items_upd.sort(key=lambda x: x.id)
    assert saved_user_feed.user_id == user_id
    assert len(saved_user_feed.user_feed_items) == len(feed_items_upd)
    for i in range(len(feed_items_upd)):
        assert saved_user_feed.user_feed_items[i].feed_item_id == feed_items_upd[i].id
        assert saved_user_feed.user_feed_items[i].user_id == user_id
