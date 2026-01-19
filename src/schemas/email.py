"""Email-related schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InboundEmailPayload(BaseModel):
    """Payload from Cloudflare Email Worker webhook."""

    to: str
    from_address: str
    from_name: str | None = None
    subject: str
    html: str | None = None
    text: str | None = None
    date: datetime | None = None


class InboundEmailResponse(BaseModel):
    """Response from inbound email webhook."""

    status: str
    message: str
    feed_item_id: int | None = None


class InboxAddressOut(BaseModel):
    """Output schema for user's inbox address."""

    model_config = ConfigDict(from_attributes=True)

    inbox_address: str
    email_token: str
