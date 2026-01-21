"""Subscription schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubscriptionIn(BaseModel):
    """Input schema for creating a subscription (internal use with user_id)."""

    user_id: int
    resource_url: str


class SubscriptionCreateIn(BaseModel):
    """Input schema for creating a subscription (API use without user_id)."""

    resource_url: str


class SubscriptionBatchIn(BaseModel):
    """Input schema for batch creating subscriptions."""

    urls: list[str]


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""

    is_active: bool | None = None
    last_run: datetime | None = None
    last_error: str | None = None
    item_count: int | None = None


class SubscriptionOut(BaseModel):
    """Output schema for subscription responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    source_id: int
    source_name: str | None = None
    resource_url: str | None = None
    is_active: bool
    created_at: datetime
    last_run: datetime | None = None
    last_error: str | None = None
    item_count: int = 0


class FeedPreviewItem(BaseModel):
    """Preview item returned from feed preview."""

    title: str
    link: str
    published: datetime | None = None
    description: str | None = None


class FeedPreviewOut(BaseModel):
    """Response for feed preview endpoint."""

    source_type: str
    source_name: str
    item_count: int
    items: list[FeedPreviewItem]
    error: str | None = None
