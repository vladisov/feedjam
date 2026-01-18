"""Feed API endpoints."""

from datetime import datetime

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
        # Return empty feed instead of 404
        now = datetime.now()
        return UserFeedOut(
            id=0,
            user_id=user_id,
            is_active=True,
            created_at=now,
            updated_at=now,
            user_feed_items=[],
        )
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


@router.post("/{user_id}/items/{item_id}/like")
def toggle_like(
    user_id: int,
    item_id: int,
    feed_service: FeedService = Depends(get_feed_service),
):
    """Toggle like for a feed item."""
    return feed_service.toggle_like(user_id, item_id)


@router.post("/{user_id}/items/{item_id}/dislike")
def toggle_dislike(
    user_id: int,
    item_id: int,
    feed_service: FeedService = Depends(get_feed_service),
):
    """Toggle dislike for a feed item."""
    return feed_service.toggle_dislike(user_id, item_id)
