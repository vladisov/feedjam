
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from repository.db import Base


class UserFeed(Base):
    __tablename__ = "user_feeds"
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))

    user_feed_items = relationship('UserFeedItem')


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
    description = Column(String,)
    article_url = Column(String,)
    comments_url = Column(String,)
    points = Column(Integer, server_default="0")
    views = Column(Integer, server_default="0")

    feed_item_id = Column(Integer, ForeignKey('feed_items.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    user_feed_id = Column(Integer, ForeignKey(
        'user_feeds.id'))
    state_id = Column(Integer, ForeignKey('user_feed_item_states.id'))

    state = relationship("UserFeedItemState")
