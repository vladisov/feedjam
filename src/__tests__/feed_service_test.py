from unittest.mock import patch
<<<<<<<< Updated upstream:src/tests/feed_service_test.py
from model.source import Source
from repository.source_storage import SourceStorage
========
import feedparser
from __tests__.test_app import override_get_db
from __tests__.test_app import client
from model.schema.feed_schema import SubscriptionCreateAPI, SubscriptionSchema
>>>>>>>> Stashed changes:src/__tests__/feed_service_test.py
from service.data_extractor import DataExtractor
from service.feed_service import FeedService
from model.subscription import Subscription

from repository.feed_storage import FeedStorage
from repository.subscription_storage import SubscriptionStorage
from tests.test_app import override_get_db
import feedparser


def _create_subscription(subscription: SubscriptionCreateAPI):
    response = client.post(
        "/subscribe/",
        json=subscription.dict(),
    )
    return SubscriptionSchema(**response.json())


def _create_hn_feed_items(feed_service: FeedService,
                          user_id=1, filename="src/__tests__/test_data/hn_best_example.xml"):
    subscription_response = _create_subscription(subscription=SubscriptionCreateAPI(
        resource_url='https://hnrss.org/best', user_id=user_id))

    with open(filename, 'r', encoding='utf-8') as file:
        hn_feed_data = file.read()

    with patch.object(feedparser, 'parse', return_value=feedparser.parse(hn_feed_data)):
        items = feed_service.fetch_and_save_feed_items(
            subscription_response.id)

        return items, subscription_response


def test_fetch_feed(cleanup):
    db = next(override_get_db())
    feed_storage = FeedStorage(db)
    subscription_storage = SubscriptionStorage(db)
    source_storage = SourceStorage(db)
    data_extractor = DataExtractor("dummy")
    service = FeedService(feed_storage, subscription_storage,
                          source_storage, data_extractor)
    _, _ = _create_hn_feed_items(service)

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

    _, _ = _create_hn_feed_items(
        service, user_id, filename="src/__tests__/test_data/hn_best_example_short.xml")
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

    _, _ = _create_hn_feed_items(
        service, user_id, filename="src/__tests__/test_data/hn_best_example.xml")
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
