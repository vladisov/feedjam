

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import relationship

from repository.db import Base


feed_feeditem_association = Table(
    'feed_feeditem', Base.metadata,  # type: ignore
    Column('feed_id', Integer, ForeignKey('feeds.id')),
    Column('feeditem_id', Integer, ForeignKey('feed_items.id'))
)

feed_userfeed_association = Table(
    'feed_userfeed', Base.metadata,  # type: ignore
    Column('user_feed_id', Integer, ForeignKey('user_feeds.id')),
    Column('feed_id', Integer, ForeignKey('feeds.id'))
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    handle = Column(String,)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    subscriptions = relationship("Subscription", back_populates="user")
    user_feed_items = relationship("UserFeedItem", back_populates="user")
    user_feeds = relationship("UserFeed", back_populates="user")


class Feed(Base):
    __tablename__ = "feeds"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())

    source_id = Column(Integer, ForeignKey("sources.id"))

    source = relationship("Source", back_populates="feeds")
    feed_items = relationship(
        "FeedItem",
        secondary=feed_feeditem_association,
        back_populates="feeds",
    )
    user_feeds = relationship(
        "UserFeed",
        secondary=feed_userfeed_association,
        back_populates="feeds",
    )


class UserFeed(Base):
    __tablename__ = "user_feeds"
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="user_feeds")
    feeds = relationship(
        "Feed",
        secondary=feed_userfeed_association,
        back_populates="user_feeds",
    )
    user_feed_items = relationship('UserFeedItem', back_populates='user_feed')


class UserFeedItemState(Base):
    __tablename__ = "user_feed_item_states"
    id = Column(Integer, primary_key=True, index=True)
    hide = Column(Boolean, server_default="false")
    read = Column(Boolean, server_default="false")
    star = Column(Boolean, server_default="false")
    like = Column(Boolean, server_default="false")
    dislike = Column(Boolean, server_default="false")


class UserFeedItem(Base):
    __tablename__ = "user_feed_items"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())
    summary = Column(String,)
    source_name = Column(String,)
    feed_item_id = Column(Integer, ForeignKey('feed_items.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    user_feed_id = Column(Integer, ForeignKey(
        'user_feeds.id'))
    state_id = Column(Integer, ForeignKey('user_feed_item_states.id'))

    user = relationship("User", back_populates="user_feed_items")
    feed_item = relationship("FeedItem", back_populates="user_feed_items")
    state = relationship("UserFeedItemState")
    user_feed = relationship('UserFeed', back_populates='user_feed_items')


class FeedItem(Base):
    __tablename__ = "feed_items"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    title = Column(String,)
    link = Column(String,)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())
    published = Column(DateTime, server_default=func.now())
    hn_id = Column(String,)
    description = Column(String,)
    comments_link = Column(String,)
    article_url = Column(String,)
    comments_url = Column(String,)
    points = Column(Integer,)
    num_comments = Column(Integer,)
    summary = Column(String,)

    source = relationship("Source", back_populates="feed_items")
    feeds = relationship(
        "Feed",
        secondary=feed_feeditem_association,
        back_populates="feed_items",
    )
    user_feed_items = relationship("UserFeedItem", back_populates="feed_item")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    created_at = Column(DateTime, server_default=func.now())
    last_run = Column(DateTime,)

    user = relationship("User", back_populates="subscriptions")
    source = relationship("Source", back_populates="subscriptions")
    runs = relationship("Run", back_populates="subscription")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    resource_url = Column(String, unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="source")
    feed_items = relationship("FeedItem", back_populates="source")
    feeds = relationship("Feed", back_populates="source")


class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String, default="pending")

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    subscription = relationship("Subscription", back_populates="runs")
