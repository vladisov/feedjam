

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import relationship

from repository.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    handle = Column(String,)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    feeds = relationship("Feed", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")


feed_feeditem_association = Table(
    'feed_feeditem', Base.metadata,  # type: ignore
    Column('feed_id', Integer, ForeignKey('feeds.id')),
    Column('feeditem_id', Integer, ForeignKey('feed_items.id'))
)


class Feed(Base):
    __tablename__ = "feeds"
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())

    source_id = Column(Integer, ForeignKey("sources.id"))
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="feeds")
    source = relationship("Source", back_populates="feeds")
    feed_items = relationship(
        "FeedItem",
        secondary=feed_feeditem_association,
        back_populates="feeds",
    )


class FeedItem(Base):
    __tablename__ = "feed_items"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    title = Column(String,)
    link = Column(String,)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    published = Column(DateTime, default=func.now())
    hn_id = Column(String,)
    description = Column(String,)
    comments_link = Column(String,)
    article_url = Column(String,)
    comments_url = Column(String,)
    points = Column(Integer,)
    num_comments = Column(Integer,)

    source = relationship("Source", back_populates="feed_items")
    feeds = relationship(
        "Feed",
        secondary=feed_feeditem_association,
        back_populates="feed_items",
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    created_at = Column(DateTime, default=func.now())
    last_run = Column(DateTime,)

    user = relationship("User", back_populates="subscriptions")
    source = relationship("Source", back_populates="subscriptions")
    runs = relationship("Run", back_populates="subscription")


class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    status = Column(String, default="pending")

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    subscription = relationship("Subscription", back_populates="runs")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    resource_url = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="source")
    feed_items = relationship("FeedItem", back_populates="source")
    feeds = relationship("Feed", back_populates="source")
