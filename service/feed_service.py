from fastapi import HTTPException
from typing import List
from model.schema.feed_schema import FeedItemCreate, FeedItemSchema

from repository.feed_storage import FeedStorage
from repository.subscription_storage import SubscriptionStorage
from service.subscription.source_parser_strategy import get_parser


class FeedService:
    def __init__(self, feed_storage: FeedStorage,
                 subscription_storage: SubscriptionStorage) -> None:
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage

    def mark_read(self, user_id: int, feed_item_id: int):
        # self.feed_storage.mark_as_read(user_id, feed_item_id)
        pass

    def load_feed_from_source(self, subscription_id: int) -> List[FeedItemCreate]:
        subscription = self.subscription_storage.get_subscription(
            subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        source = subscription.source

        parser = get_parser(source)
        if not parser:
            raise HTTPException(
                status_code=400, detail="No parser for the source")

        items = parser(source)

        self.feed_storage.add_feed_items(source, items)
        return items

    def get_feed_items(self, source_id: int, skip: int = 0, limit: int = 100) -> List[FeedItemSchema]:
        return self.feed_storage.get_feed_items(source_id, skip, limit)

    def get_user_feed(self, user_id: int) -> List[FeedItemSchema]:
        subscriptions = self.subscription_storage.get_user_subscriptions(
            user_id)
        feed_items = []
        for sub in subscriptions:
            feed_items += self.get_feed_items(sub.source.id, 0, 100)
        return feed_items
