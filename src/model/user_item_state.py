"""Persistent user state for feed items.

This tracks user engagement (liked, read, starred, etc.) independently
of feed regeneration. Unlike UserFeedItem state which is ephemeral,
this persists across feed regenerations.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.db import Base

if TYPE_CHECKING:
    from model.feed import FeedItem


class UserItemState(Base):
    __tablename__ = "user_item_states"
    __table_args__ = (
        Index("ix_user_item_states_user_item", "user_id", "feed_item_id", unique=True),
        Index("ix_user_item_states_user_liked", "user_id", "liked"),
        Index("ix_user_item_states_user_starred", "user_id", "starred"),
        Index("ix_user_item_states_user_read", "user_id", "read"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    feed_item_id: Mapped[int] = mapped_column(ForeignKey("feed_items.id"))

    read: Mapped[bool] = mapped_column(default=False)
    liked: Mapped[bool] = mapped_column(default=False)
    disliked: Mapped[bool] = mapped_column(default=False)
    starred: Mapped[bool] = mapped_column(default=False)
    hidden: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    feed_item: Mapped["FeedItem"] = relationship()
