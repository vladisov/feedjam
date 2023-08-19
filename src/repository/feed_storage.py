from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from model.feed import Feed, FeedItem, feed_feeditem_association
from model.schema.feed_schema import FeedItemCreate, FeedItemSchema, SourceSchema
from model.schema.feed_schema import UserFeedCreate, UserFeedSchema
from model.user_feed import UserFeed, UserFeedItem, UserFeedItemState
from model.subscription import Subscription

from utils.logger import get_logger

logger = get_logger(__name__)


class FeedStorage:
    def __init__(self, db: Session):
        self.db = db

    def _add_feed_item(self, feed_item_create: FeedItemCreate, feed: Feed) -> None:
        existing_item = self.db.query(FeedItem).filter(
            FeedItem.link == feed_item_create.link).first()
        if existing_item:
            logger.info("Feed item %s already exists, skipping.",
                        feed_item_create.link)
            return

        feed_item = FeedItem(**feed_item_create.dict())
        # add to feed somehow here
        feed.feed_items.append(feed_item)

        self.db.add(feed_item)

    def get_active_user_feed(self, user_id: int) -> Optional[UserFeedSchema]:
        db_user_feed = self.db.query(UserFeed).options(joinedload(UserFeed.user_feed_items)).filter(
            and_(UserFeed.user_id == user_id, UserFeed.is_active)
        ).first()
        return UserFeedSchema.from_orm(db_user_feed) if db_user_feed else None

    def deactivate_user_feed(self, user_feed_id: int) -> None:
        user_feed = self.db.query(UserFeed).filter(
            UserFeed.id == user_feed_id).first()
        if user_feed:
            user_feed.is_active = False
            self.db.commit()
        else:
            logger.info("User feed %s not found.", user_feed_id)

    def save_feed_items(self,
                        source: SourceSchema,
                        feed_items: List[FeedItemCreate]):
        feed = self.get_or_create_feed(source)
        for item in feed_items:
            self._add_feed_item(item, feed)
        self.db.commit()

    def get_or_create_feed(self, source: SourceSchema) -> Feed:
        feed = self.db.query(Feed).filter(Feed.source_id == source.id).first()
        if not feed:
            feed = Feed(source_id=source.id)
            self.db.add(feed)
            self.db.commit()
            self.db.refresh(feed)
        return feed

    def save_user_feed(self, user_feed: UserFeedCreate):
        new_user_feed = UserFeed(
            user_id=user_feed.user_id, is_active=user_feed.is_active, user_feed_items=[]
        )

        self.db.add(new_user_feed)
        self.db.flush()

        for user_feed_item in user_feed.user_feed_items:
            new_user_feed_item_data = user_feed_item.dict()
            new_user_feed_item_data.update({
                'user_feed_id': new_user_feed.id,
                'state': UserFeedItemState(**user_feed_item.state.dict())
            })
            new_user_feed_item = UserFeedItem(**new_user_feed_item_data)
            self.db.add(new_user_feed_item)

        self.db.commit()
        return new_user_feed.id

    def get_user_feed(self, user_id: int) -> UserFeedSchema:
        user_feed = self.db.query(UserFeed).options(joinedload(
            UserFeed.user_feed_items)).filter(and_(UserFeed.user_id == user_id, UserFeed.is_active)).first()

        if user_feed:
            return UserFeedSchema.from_orm(user_feed)
        raise Exception("No feed found for this user.")

    def get_feed_items_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[FeedItemSchema]:
        subscriptions = self.db.query(Subscription).filter(
            Subscription.user_id == user_id).all()
        source_ids = [subscription.source_id for subscription in subscriptions]

        feed_items = self.get_feed_items_by_source_ids(source_ids, skip, limit)
        return feed_items

    def get_feed_items_by_source_ids(self, source_ids: List[int], skip: int = 0,
                                     limit: int = 100) -> List[FeedItemSchema]:
        # feed_items = self.db.query(FeedItem).join(Feed).filter(
        #     Feed.source_id.in_(source_ids)
        feed_items = self.db.query(FeedItem) \
            .join(feed_feeditem_association, FeedItem.id == feed_feeditem_association.c.feeditem_id) \
            .join(Feed, feed_feeditem_association.c.feed_id == Feed.id) \
            .filter(Feed.source_id.in_(source_ids)) \
            .offset(skip) \
            .limit(limit) \
            .all()

        return feed_items

    def mark_as_read(self, user_id: int, user_feed_item_id: int):
        user_feed_item = self.db.query(UserFeedItem).filter(and_(UserFeedItem.id == user_feed_item_id,
                                                                 UserFeedItem.user_id == user_id)).first()
        if user_feed_item:
            user_feed_item.state.read = True
            self.db.commit()
            return True
        logger.info("User feed item %s not found.", user_feed_item_id)
        return False
