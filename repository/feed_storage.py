import logging
from typing import List, Optional

from sqlalchemy import and_
from model.model import Feed, FeedItem, UserFeed, UserFeedItem, UserFeedItemState
from model.schema.feed_schema import FeedItemCreate, FeedItemSchema, FeedSchema, SourceSchema
from model.schema.feed_schema import UserFeedCreate, UserFeedItemSchema, UserFeedSchema
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


class FeedStorage:
    def __init__(self, db: Session):
        self.db = db

    def _add_feed_item(self, feed_item_create: FeedItemCreate, feed: Feed) -> None:
        existing_item = self.db.query(FeedItem).filter(
            FeedItem.link == feed_item_create.link).first()
        if existing_item:
            logger.info(
                f'Feed item {feed_item_create.link} already exists, skipping.')
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
            logger.info(f'User feed {user_feed_id} not found.')

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
            user_id=user_feed.user_id, is_active=user_feed.is_active, user_feed_items=[], feeds=[])

        self.db.add(new_user_feed)
        self.db.flush()

        # Now, create UserFeedItem instances for each item in user_feed.user_feed_items
        for user_feed_item in user_feed.user_feed_items:
            new_user_feed_item = UserFeedItem(
                user_id=user_feed.user_id,
                feed_item_id=user_feed_item.feed_item_id,
                state=UserFeedItemState(hide=False, read=False, star=False,
                                        like=False, dislike=False)
            )

            new_user_feed_item.user_feed_id = new_user_feed.id
            self.db.add(new_user_feed_item)

        self.db.commit()
        return new_user_feed.id

    def get_user_feed(self, user_id: int) -> UserFeedSchema:
        user_feed = self.db.query(UserFeed).options(joinedload(
            UserFeed.user_feed_items)).filter(and_(UserFeed.user_id == user_id, UserFeed.is_active)).first()

        if user_feed:
            data = {
                "id": user_feed.id,
                "user_id": user_feed.user_id,
                "created_at": user_feed.created_at,
                "updated_at": user_feed.updated_at,
                "is_active": user_feed.is_active,
                "user_feed_items": [
                    UserFeedItemSchema(
                        id=item.id,
                        created_at=item.created_at,
                        updated_at=item.updated_at,
                        summary=item.summary,
                        source_name=item.source_name,
                        feed_item_id=item.feed_item_id,
                        user_id=item.user_id,
                        state=item.state.__dict__
                    )
                    for item in user_feed.user_feed_items
                ],
            }
            return UserFeedSchema(**data)
        else:
            raise Exception("No feed found for this user.")

    def get_feed_items(self, source_id: int, skip: int = 0, limit: int = 100) -> List[FeedItemSchema]:
        feed: Optional[Feed] = self.db.query(Feed).filter(
            Feed.source_id == source_id).first()

        if feed is None:
            return []

        feed_items = self.db.query(FeedItem).filter(
            FeedItem.feeds.contains(feed)).offset(skip).limit(limit).all()

        return feed_items

    def mark_as_read(self, user_id: int, user_feed_item_id: int):
        user_feed_item = self.db.query(UserFeedItem).filter(and_(UserFeedItem.id == user_feed_item_id,
                                                                 UserFeedItem.user_id == user_id)).first()
        if user_feed_item:
            user_feed_item.state.read = True
            self.db.commit()
            return True
        else:
            logger.info(f'User feed item {user_feed_item_id} not found.')
        return False
