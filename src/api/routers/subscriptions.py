"""Subscription API endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends

from api.exceptions import EntityNotFoundException
from schemas import SubscriptionOut
from schemas.subscriptions import SubscriptionCreateIn
from service.subscription_service import SubscriptionService
from tasks.scheduler import fetch_subscription, generate_user_feed
from utils.dependencies import get_current_user_id, get_subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


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
    # Verify the subscription belongs to the user
    sub = subscription_service.get(subscription_id)
    if not sub or sub.user_id != user_id:
        raise EntityNotFoundException("Subscription", subscription_id)
    if not subscription_service.delete(subscription_id):
        raise EntityNotFoundException("Subscription", subscription_id)
    return {"status": "ok"}
