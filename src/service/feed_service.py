from typing import List, Optional
from fastapi import HTTPException
from service.data_extractor import DataExtractor
from service.parser.source_parser_strategy import get_parser
from model.schema.feed_schema import FeedItemCreate, FeedItemSchema, StateBase, UserFeedCreate
from model.schema.feed_schema import UserFeedItemCreate, UserFeedSchema
from repository.source_storage import SourceStorage
from repository.feed_storage import FeedStorage
from repository.subscription_storage import SubscriptionStorage
from utils import config


class FeedService:
    def __init__(self, feed_storage: FeedStorage,
                 subscription_storage: SubscriptionStorage,
                 source_storage: SourceStorage,
                 data_extractor: DataExtractor) -> None:
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
        self.source_storage = source_storage
        self.data_extractor = data_extractor

    def mark_read(self, user_id: int, user_feed_item_id: int) -> bool:
        return self.feed_storage.mark_as_read(user_id, user_feed_item_id)

    def fetch_and_save_feed_items(self, subscription_id: int) -> List[FeedItemCreate]:
        subscription = self.subscription_storage.get_subscription(
            subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        source = self.source_storage.get_source(subscription.source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        parser = get_parser(source)
        if not parser:
            raise HTTPException(
                status_code=400, detail="No parser for the source")

        # move to separate function
        items = parser(source)
        for item in items:
            if config.ENABLE_SUMMARIZATION:
                item.summary = self.data_extractor.extract_and_summarize(
                    item.article_url)
            else:
                item.summary = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

        self.feed_storage.save_feed_items(source, items)
        return items

    def get_feed_items(self, user_id: int, skip: int = 0, limit: int = 100) -> List[FeedItemSchema]:
        return self.feed_storage.get_feed_items_by_user(user_id, skip, limit)

    def get_user_feed(self, user_id: int) -> UserFeedSchema:
        return self.feed_storage.get_user_feed(user_id)

    def generate_and_save_user_feed(self, user_id: int) -> None:
        active_user_feed = self.feed_storage.get_active_user_feed(user_id)

        new_user_feed_items: List[UserFeedItemCreate] = self._get_unread_items_from_active_feed(
            active_user_feed)
        new_user_feed_items += self._get_new_feed_items(
            user_id, new_user_feed_items)

        new_user_feed = UserFeedCreate(
            user_id=user_id,
            is_active=True,
            user_feed_items=new_user_feed_items
        )

        self.feed_storage.save_user_feed(new_user_feed)
        if active_user_feed:
            self.feed_storage.deactivate_user_feed(active_user_feed.id)

    def _get_unread_items_from_active_feed(self, active_user_feed:
                                           Optional[UserFeedSchema]) -> List[UserFeedItemCreate]:
        if not active_user_feed:
            return []

        return [item for item in active_user_feed.user_feed_items if not item.state.read]

    def _get_new_feed_items(self, user_id: int, existing_items: List[UserFeedItemCreate]) -> List[UserFeedItemCreate]:
        existing_feed_item_ids = {item.feed_item_id for item in existing_items}

        all_items = self.get_feed_items(user_id)
        new_items = [
            item for item in all_items if item.id not in existing_feed_item_ids]

        return [UserFeedItemCreate(feed_item_id=item.id,
                                   user_id=user_id,
                                   title=item.title,
                                   source_name=item.source_name,
                                   state=StateBase(),
                                   description=item.description,
                                   comments_url=item.comments_url,
                                   article_url=item.article_url,
                                   points=item.points,
                                   summary=item.summary,
                                   views=item.views) for item in new_items]
