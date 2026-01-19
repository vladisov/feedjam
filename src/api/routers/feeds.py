"""Feed API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from api.exceptions import EntityNotFoundException
from schemas import UserFeedOut
from schemas.feeds import SearchResultItem
from service.feed_service import FeedService
from utils.dependencies import get_current_user_id, get_feed_service

router = APIRouter(prefix="/feed", tags=["feeds"])


@router.get("", response_model=UserFeedOut)
def get_feed(
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Get the active feed for the authenticated user."""
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


@router.post("/mark-read/{item_id}")
def mark_item_read(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Mark a feed item as read."""
    success = feed_service.mark_read(user_id, item_id)
    if not success:
        raise EntityNotFoundException("FeedItem", item_id)
    return {"status": "ok"}


@router.post("/items/{item_id}/like")
def toggle_like(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Toggle like for a feed item."""
    return feed_service.toggle_like(user_id, item_id)


@router.post("/items/{item_id}/dislike")
def toggle_dislike(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Toggle dislike for a feed item."""
    return feed_service.toggle_dislike(user_id, item_id)


@router.post("/items/{item_id}/star")
def toggle_star(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Toggle star (save for later) for a feed item."""
    return feed_service.toggle_star(user_id, item_id)


@router.post("/items/{item_id}/hide")
def toggle_hide(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Toggle hide for a feed item."""
    return feed_service.toggle_hide(user_id, item_id)


@router.post("/hide-read")
def hide_read_items(
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Hide all read items for a user."""
    return feed_service.hide_read_items(user_id)


@router.post("/mark-all-read")
def mark_all_read(
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Mark all unread items as read for a user."""
    return feed_service.mark_all_read(user_id)


@router.get("/search", response_model=list[SearchResultItem])
def search_items(
    liked: bool | None = Query(None, description="Filter by liked state"),
    disliked: bool | None = Query(None, description="Filter by disliked state"),
    starred: bool | None = Query(None, description="Filter by starred state"),
    read: bool | None = Query(None, description="Filter by read state"),
    hidden: bool | None = Query(None, description="Filter by hidden state"),
    text: str | None = Query(None, description="Search text in title/summary"),
    source: str | None = Query(None, description="Filter by source name"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Search user's historical items by state filters.

    Use this for searching liked, saved, read items across all time.
    For current feed items, use GET /feed instead.
    """
    return feed_service.search_items(
        user_id=user_id,
        liked=liked,
        disliked=disliked,
        starred=starred,
        read=read,
        hidden=hidden,
        text=text,
        source=source,
        limit=limit,
        offset=offset,
    )
