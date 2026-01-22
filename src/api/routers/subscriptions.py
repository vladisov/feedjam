"""Subscription API endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from api.exceptions import EntityNotFoundException
from schemas import SubscriptionOut
from schemas.subscriptions import FeedPreviewOut, SubscriptionBatchIn, SubscriptionCreateIn
from service.subscription_service import SubscriptionService
from tasks.scheduler import fetch_subscription, generate_user_feed
from utils.dependencies import get_current_user_id, get_subscription_service
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _verify_subscription_ownership(
    subscription_id: int,
    user_id: int,
    subscription_service: SubscriptionService,
) -> None:
    """Verify a subscription belongs to the user."""
    owner_id = subscription_service.get_owner_id(subscription_id)
    if owner_id is None or owner_id != user_id:
        raise EntityNotFoundException("Subscription", subscription_id)


@router.post("", response_model=SubscriptionOut)
def create_subscription(
    subscription: SubscriptionCreateIn,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Create a new subscription and immediately fetch its items."""
    result = subscription_service.create_for_user(subscription, user_id)

    # Immediately fetch items and regenerate user feed in background
    background_tasks.add_task(fetch_subscription, result.id)
    background_tasks.add_task(generate_user_feed, user_id)

    return result


@router.post("/batch", response_model=list[SubscriptionOut])
def batch_subscribe(
    batch: SubscriptionBatchIn,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Create multiple subscriptions at once (used during onboarding)."""
    results = []
    for url in batch.urls:
        try:
            sub_in = SubscriptionCreateIn(resource_url=url)
            result = subscription_service.create_for_user(sub_in, user_id)
            results.append(result)
            background_tasks.add_task(fetch_subscription, result.id)
        except Exception as e:
            logger.warning("Failed to subscribe to %s: %s", url, e)

    if results:
        background_tasks.add_task(generate_user_feed, user_id)

    return results


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(
    user_id: int = Depends(get_current_user_id),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Get all subscriptions for the authenticated user."""
    return subscription_service.get_by_user(user_id)


@router.delete("/{subscription_id}")
def delete_subscription(
    subscription_id: int,
    user_id: int = Depends(get_current_user_id),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Delete a subscription."""
    _verify_subscription_ownership(subscription_id, user_id, subscription_service)
    subscription_service.delete(subscription_id, user_id=user_id)
    return {"status": "ok"}


@router.get("/preview", response_model=FeedPreviewOut)
def preview_feed(
    url: str = Query(..., description="Feed URL to preview"),
    _user_id: int = Depends(get_current_user_id),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Preview a feed URL before subscribing. Returns detected source type, name, and sample items."""
    return subscription_service.preview_feed(url)


@router.post("/{subscription_id}/refetch")
def refetch_subscription(
    subscription_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Manually trigger a refetch for a subscription."""
    _verify_subscription_ownership(subscription_id, user_id, subscription_service)

    background_tasks.add_task(fetch_subscription, subscription_id)
    background_tasks.add_task(generate_user_feed, user_id)

    return {"status": "ok", "message": "Refetch triggered"}
