"""Feed and feed item schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemState(BaseModel):
    """State flags for a feed item."""

    model_config = ConfigDict(from_attributes=True)

    hide: bool = False
    read: bool = False
    star: bool = False
    like: bool = False
    dislike: bool = False


class FeedItemIn(BaseModel):
    """Input schema for creating a feed item (from parser)."""

    title: str
    link: str
    source_name: str
    description: str = ""
    num_comments: int = 0
    local_id: str | None = None
    article_url: str | None = None
    comments_url: str | None = None
    points: int | None = None
    views: int | None = None
    summary: str | None = None
    published: datetime | None = None


class FeedItemOut(BaseModel):
    """Output schema for feed item responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    link: str
    source_name: str
    description: str
    num_comments: int
    local_id: str | None = None
    article_url: str | None = None
    comments_url: str | None = None
    points: int | None = None
    views: int | None = None
    summary: str | None = None
    published: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserFeedItemIn(BaseModel):
    """Input schema for creating a user feed item."""

    feed_item_id: int
    user_id: int
    title: str
    source_name: str
    state: ItemState
    description: str = ""
    article_url: str | None = None
    comments_url: str | None = None
    points: int | None = None
    views: int | None = None
    summary: str | None = None


class UserFeedItemOut(BaseModel):
    """Output schema for user feed item responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    feed_item_id: int
    user_id: int
    title: str
    description: str
    source_name: str | None = None
    article_url: str | None = None
    comments_url: str | None = None
    points: int | None = None
    views: int | None = None
    summary: str | None = None
    state: ItemState
    created_at: datetime
    updated_at: datetime


class UserFeedIn(BaseModel):
    """Input schema for creating a user feed."""

    user_id: int
    is_active: bool = True
    user_feed_items: list[UserFeedItemIn]


class UserFeedOut(BaseModel):
    """Output schema for user feed responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user_feed_items: list[UserFeedItemOut]
