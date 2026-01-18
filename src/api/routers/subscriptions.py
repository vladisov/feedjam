"""Subscription API endpoints."""

from fastapi import APIRouter, Depends

from schemas import SubscriptionIn, SubscriptionOut
from service.subscription_service import SubscriptionService
from utils.dependencies import get_subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/", response_model=SubscriptionOut)
def create_subscription(
    subscription: SubscriptionIn,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Create a new subscription."""
    return subscription_service.create(subscription)


@router.get("/", response_model=list[SubscriptionOut])
def list_subscriptions(
    user_id: int,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Get all subscriptions for a user."""
    return subscription_service.get_by_user(user_id)
