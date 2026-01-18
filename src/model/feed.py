from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.db import Base

# Association table for Feed <-> FeedItem many-to-many
feed_feeditem_association = Table(
    "feed_feeditem",
    Base.metadata,
    Column("feed_id", Integer, ForeignKey("feeds.id"), primary_key=True),
    Column("feeditem_id", Integer, ForeignKey("feed_items.id"), primary_key=True),
)


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    feed_items: Mapped[list["FeedItem"]] = relationship(
        secondary=feed_feeditem_association,
        back_populates="feeds",
    )


class FeedItem(Base):
    __tablename__ = "feed_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(1024))
    link: Mapped[str] = mapped_column(String(2048))
    source_name: Mapped[str] = mapped_column(String(255))
    local_id: Mapped[str | None] = mapped_column(String(255), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    article_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    comments_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    points: Mapped[int] = mapped_column(default=0)
    views: Mapped[int] = mapped_column(default=0)
    num_comments: Mapped[int] = mapped_column(default=0)
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    published: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    feeds: Mapped[list["Feed"]] = relationship(
        secondary=feed_feeditem_association,
        back_populates="feed_items",
    )
