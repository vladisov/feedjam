"""Feed API endpoints."""

from fastapi import APIRouter, Depends

from api.exceptions import EntityNotFoundException
from schemas import UserFeedOut
from service.feed_service import FeedService
from utils.dependencies import get_feed_service

router = APIRouter(prefix="/feed", tags=["feeds"])


@router.get("/{user_id}", response_model=UserFeedOut)
def get_feed(
    user_id: int,
    feed_service: FeedService = Depends(get_feed_service),
):
    """Get the active feed for a user."""
    user_feed = feed_service.get_user_feed(user_id)
    if not user_feed:
        raise EntityNotFoundException("Feed", user_id)
    return user_feed


@router.post("/{user_id}/mark-read/{item_id}")
def mark_item_read(
    user_id: int,
    item_id: int,
    feed_service: FeedService = Depends(get_feed_service),
):
    """Mark a feed item as read."""
    success = feed_service.mark_read(user_id, item_id)
    if not success:
        raise EntityNotFoundException("FeedItem", item_id)
    return {"status": "ok"}
