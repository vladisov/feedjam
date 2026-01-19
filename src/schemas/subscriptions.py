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


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""

    is_active: bool | None = None
    last_run: datetime | None = None


class SubscriptionOut(BaseModel):
    """Output schema for subscription responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    source_id: int
    source_name: str | None = None
    is_active: bool
    created_at: datetime
    last_run: datetime | None = None
