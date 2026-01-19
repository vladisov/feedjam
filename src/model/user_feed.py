from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.db import Base


class UserFeed(Base):
    __tablename__ = "user_feeds"
    __table_args__ = (
        Index("ix_user_feeds_user_active", "user_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user_feed_items: Mapped[list["UserFeedItem"]] = relationship(back_populates="user_feed")


class UserFeedItemState(Base):
    __tablename__ = "user_feed_item_states"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hide: Mapped[bool] = mapped_column(default=False)
    read: Mapped[bool] = mapped_column(default=False)
    star: Mapped[bool] = mapped_column(default=False)
    like: Mapped[bool] = mapped_column(default=False)
    dislike: Mapped[bool] = mapped_column(default=False)


class UserFeedItem(Base):
    __tablename__ = "user_feed_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    feed_item_id: Mapped[int] = mapped_column(ForeignKey("feed_items.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user_feed_id: Mapped[int] = mapped_column(ForeignKey("user_feeds.id"), index=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("user_feed_item_states.id"))

    # Denormalized fields for quick access
    title: Mapped[str] = mapped_column(String(1024))
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    source_name: Mapped[str | None] = mapped_column(String(255), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    article_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    comments_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    points: Mapped[int] = mapped_column(default=0)
    views: Mapped[int] = mapped_column(default=0)
    rank_score: Mapped[float] = mapped_column(default=0.0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    state: Mapped["UserFeedItemState"] = relationship()
    user_feed: Mapped["UserFeed"] = relationship(back_populates="user_feed_items")
