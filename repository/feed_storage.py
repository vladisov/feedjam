from typing import List
from model.model import FeedItem, UserFeed, UserFeedItem, UserFeedItemState
from model.schema.feed_schema import FeedItemCreate, FeedItemSchema, SourceSchema
from model.schema.feed_schema import UserFeedCreate, UserFeedItemSchema, UserFeedSchema
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload


class FeedStorage:
    def __init__(self, db: Session):
        self.db = db

    def add_feed_item(self, feed_item_create: FeedItemCreate) -> None:

        existing_item = self.db.query(FeedItem).filter(
            FeedItem.link == feed_item_create.link).first()
        if existing_item:
            print(
                f'Feed item {feed_item_create.link} already exists, skipping.')
            return

        feed_item = FeedItem(**feed_item_create.dict())

        self.db.add(feed_item)
        self.db.commit()

    def save_feed_items(self,
                        source: SourceSchema,
                        feed_items: List[FeedItemCreate]):
        for item in feed_items:
            self.add_feed_item(item)

    def save_user_feed(self, user_feed: UserFeedCreate):
        new_user_feed = UserFeed(
            user_id=user_feed.user_id, is_active=user_feed.is_active)

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
            UserFeed.user_feed_items)).filter(UserFeed.user_id == user_id).first()

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
        return self.db.query(FeedItem).filter(FeedItem.source_id == source_id).offset(skip).limit(limit).all()
