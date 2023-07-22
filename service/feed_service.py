from fastapi import HTTPException
from typing import List
from service.data_extractor import DataExtractor
from model.schema.feed_schema import FeedItemCreate, FeedItemSchema, StateBase, UserFeedCreate
from model.schema.feed_schema import UserFeedItemCreate, UserFeedSchema

from repository.feed_storage import FeedStorage
from repository.subscription_storage import SubscriptionStorage
from service.subscription.source_parser_strategy import get_parser


class FeedService:
    def __init__(self, feed_storage: FeedStorage,
                 subscription_storage: SubscriptionStorage,
                 data_extractor: DataExtractor) -> None:
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
        self.data_extractor = data_extractor

    def mark_read(self, user_id: int, feed_item_id: int):
        # self.feed_storage.mark_as_read(user_id, feed_item_id)
        pass

    def fetch_and_save_feed_items(self, subscription_id: int) -> List[FeedItemCreate]:
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

        self.feed_storage.save_feed_items(source, items)
        return items

    def generate_and_save_user_feed(self, user_id: int):
        items = self.get_feed_items(user_id)

        user_feed_items: List[UserFeedItemCreate] = [
            UserFeedItemCreate(feed_item_id=item.id,
                               user_id=user_id, state=StateBase())
            for item in items
        ]
        # should be more sophisticated logic, BUT LATER
        # for item in items:
        #     summary = self.data_extractor.extract_and_summarize(item.link)
        #     item.summary = summary
        #     self.feed_storage.add_feed_item(item)

        user_feed = UserFeedCreate(
            user_id=user_id, user_feed_items=user_feed_items)
        self.feed_storage.save_user_feed(user_feed)

    def get_feed_items(self, source_id: int, skip: int = 0, limit: int = 100) -> List[FeedItemSchema]:
        return self.feed_storage.get_feed_items(source_id, skip, limit)

    def get_user_feed(self, user_id: int) -> UserFeedSchema:
        return self.feed_storage.get_user_feed(user_id)
