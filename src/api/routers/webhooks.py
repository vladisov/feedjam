"""Webhook API endpoints for external integrations."""

from fastapi import APIRouter, Depends, Header, HTTPException

from schemas.email import InboundEmailPayload, InboundEmailResponse
from service.email_service import EmailService
from utils.dependencies import get_email_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/inbound-email", response_model=InboundEmailResponse)
def receive_inbound_email(
    payload: InboundEmailPayload,
    email_service: EmailService = Depends(get_email_service),
    x_webhook_secret: str | None = Header(None),
):
    """Receive inbound email from Cloudflare Email Worker.

    Emails are converted to feed items for the recipient user.
    """
    # TODO: Validate webhook secret in production
    feed_item_id = email_service.process_inbound_email(payload)
    if feed_item_id is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to process email. Invalid recipient or unknown user.",
        )
    return InboundEmailResponse(
        status="ok",
        message="Email processed successfully",
        feed_item_id=feed_item_id,
    )
