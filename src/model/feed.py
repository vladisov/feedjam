

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import relationship
from repository.db import Base

feed_feeditem_association = Table(
    'feed_feeditem', Base.metadata,  # type: ignore
    Column('feed_id', Integer, ForeignKey('feeds.id')),
    Column('feeditem_id', Integer, ForeignKey('feed_items.id'))
)


class Feed(Base):
    __tablename__ = "feeds"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())

    source_id = Column(Integer, ForeignKey("sources.id"))

    feed_items = relationship(
        "FeedItem",
        secondary=feed_feeditem_association,
        back_populates="feeds",
    )


class FeedItem(Base):
    __tablename__ = "feed_items"
    id = Column(Integer, primary_key=True)
    title = Column(String,)
    link = Column(String,)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())
    published = Column(DateTime, server_default=func.now())
    local_id = Column(String,)
    description = Column(String,)
    article_url = Column(String,)
    comments_url = Column(String,)
    points = Column(Integer, server_default="0")
    views = Column(Integer, server_default="0")
    num_comments = Column(Integer,)
    summary = Column(String,)

    feeds = relationship(
        "Feed",
        secondary=feed_feeditem_association,
        back_populates="feed_items",
    )
