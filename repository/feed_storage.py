from typing import List
from model.model import FeedItem
from model.schema.feed_schema import FeedItemCreate, FeedItemSchema, SourceSchema
from sqlalchemy.orm import Session


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

    def add_feed_items(self, source: SourceSchema,
                       feed_items: List[FeedItemCreate]):
        if not source.is_active:
            return
        for item in feed_items:
            self.add_feed_item(item)

    def get_feed_items(self, source_id: int, skip: int = 0, limit: int = 100) -> List[FeedItemSchema]:
        return self.db.query(FeedItem).filter(FeedItem.source_id == source_id).offset(skip).limit(limit).all()
