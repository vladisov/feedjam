"""Feed repository."""

from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from model.feed import Feed, FeedItem, feed_feeditem_association
from model.source import Source
from model.subscription import Subscription
from model.user_feed import UserFeed, UserFeedItem, UserFeedItemState
from schemas import FeedItemIn, UserFeedOut
from schemas.feeds import UserFeedIn
from utils.logger import get_logger

logger = get_logger(__name__)


def _sanitize_string(value: str | None) -> str | None:
    """Remove NUL characters that PostgreSQL doesn't allow in text fields."""
    if value is None:
        return None
    return value.replace("\x00", "")


class FeedStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_items(self, source: Source, items: list[FeedItemIn]) -> None:
        """Save feed items for a source."""
        feed = self._get_or_create_feed(source.id)
        for item in items:
            self._add_item(item, feed)
        self.db.commit()

    def get_items_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[FeedItem]:
        """Get feed items for all sources a user is subscribed to."""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        subscriptions = self.db.execute(stmt).scalars().all()
        source_ids = [sub.source_id for sub in subscriptions]
        return self._get_items_by_sources(source_ids, skip, limit)

    def get_user_feed(self, user_id: int) -> UserFeedOut | None:
        """Get the active user feed."""
        stmt = (
            select(UserFeed)
            .options(joinedload(UserFeed.user_feed_items).joinedload(UserFeedItem.state))
            .where(and_(UserFeed.user_id == user_id, UserFeed.is_active == True))
        )
        user_feed = self.db.execute(stmt).unique().scalar_one_or_none()
        return UserFeedOut.model_validate(user_feed) if user_feed else None


    def save_user_feed(self, user_feed: UserFeedIn) -> int:
        """Save a new user feed."""
        new_user_feed = UserFeed(
            user_id=user_feed.user_id,
            is_active=user_feed.is_active,
        )
        self.db.add(new_user_feed)
        self.db.flush()

        for item in user_feed.user_feed_items:
            state = UserFeedItemState(**item.state.model_dump())
            self.db.add(state)
            self.db.flush()

            item_data = item.model_dump(exclude={"state"})
            item_data["user_feed_id"] = new_user_feed.id
            item_data["state_id"] = state.id
            new_item = UserFeedItem(**item_data)
            self.db.add(new_item)

        self.db.commit()
        return new_user_feed.id

    def deactivate_user_feed(self, user_feed_id: int) -> None:
        """Deactivate a user feed."""
        stmt = select(UserFeed).where(UserFeed.id == user_feed_id)
        user_feed = self.db.execute(stmt).scalar_one_or_none()
        if user_feed:
            user_feed.is_active = False
            self.db.commit()

    def mark_as_read(self, user_id: int, item_id: int) -> bool:
        """Mark a user feed item as read."""
        item = self._get_user_feed_item(user_id, item_id)
        if not item:
            return False
        item.state.read = True
        self.db.commit()
        return True

    def toggle_like(self, user_id: int, item_id: int) -> tuple[bool, str | None, int | None, bool]:
        """Toggle like state for a feed item.

        Returns: (success, source_name, feed_item_id, new_like_state)
        """
        item = self._get_user_feed_item(user_id, item_id)
        if not item:
            return False, None, None, False
        # If currently disliked, remove dislike first
        if item.state.dislike:
            item.state.dislike = False
        item.state.like = not item.state.like
        self.db.commit()
        return True, item.source_name, item.feed_item_id, item.state.like

    def toggle_dislike(self, user_id: int, item_id: int) -> tuple[bool, str | None, int | None, bool]:
        """Toggle dislike state for a feed item.

        Returns: (success, source_name, feed_item_id, new_dislike_state)
        """
        item = self._get_user_feed_item(user_id, item_id)
        if not item:
            return False, None, None, False
        # If currently liked, remove like first
        if item.state.like:
            item.state.like = False
        item.state.dislike = not item.state.dislike
        self.db.commit()
        return True, item.source_name, item.feed_item_id, item.state.dislike

    def toggle_star(self, user_id: int, item_id: int) -> tuple[bool, int | None, bool]:
        """Toggle star (save for later) state for a feed item.

        Returns: (success, feed_item_id, new_star_state)
        """
        item = self._get_user_feed_item(user_id, item_id)
        if not item:
            return False, None, False
        item.state.star = not item.state.star
        self.db.commit()
        return True, item.feed_item_id, item.state.star

    def toggle_hide(self, user_id: int, item_id: int) -> tuple[bool, int | None, bool]:
        """Toggle hide state for a feed item.

        Returns: (success, feed_item_id, new_hide_state)
        """
        item = self._get_user_feed_item(user_id, item_id)
        if not item:
            return False, None, False
        item.state.hide = not item.state.hide
        self.db.commit()
        return True, item.feed_item_id, item.state.hide

    def hide_read_items(self, user_id: int) -> tuple[int, list[int]]:
        """Hide all read items for a user.

        Returns: (count of items hidden, list of feed_item_ids affected)
        """
        stmt = (
            select(UserFeedItem)
            .join(UserFeedItemState)
            .join(UserFeed)
            .where(
                and_(
                    UserFeed.user_id == user_id,
                    UserFeed.is_active == True,
                    UserFeedItemState.read == True,
                    UserFeedItemState.hide == False,
                )
            )
        )
        items = self.db.execute(stmt).scalars().all()
        feed_item_ids = [item.feed_item_id for item in items]
        for item in items:
            item.state.hide = True
        self.db.commit()
        return len(items), feed_item_ids

    def mark_all_read(self, user_id: int) -> tuple[int, list[int]]:
        """Mark all unread items as read for a user.

        Returns: (count of items marked as read, list of feed_item_ids affected)
        """
        stmt = (
            select(UserFeedItem)
            .join(UserFeedItemState)
            .join(UserFeed)
            .where(
                and_(
                    UserFeed.user_id == user_id,
                    UserFeed.is_active == True,
                    UserFeedItemState.read == False,
                    UserFeedItemState.hide == False,
                )
            )
        )
        items = self.db.execute(stmt).scalars().all()
        feed_item_ids = [item.feed_item_id for item in items]
        for item in items:
            item.state.read = True
        self.db.commit()
        return len(items), feed_item_ids

    def get_item(self, user_id: int, item_id: int) -> UserFeedItem | None:
        """Get a single user feed item."""
        return self._get_user_feed_item(user_id, item_id)

    # --- Private helpers ---

    def _get_user_feed_item(self, user_id: int, item_id: int) -> UserFeedItem | None:
        """Get a user feed item by user and item ID."""
        stmt = select(UserFeedItem).where(
            and_(UserFeedItem.id == item_id, UserFeedItem.user_id == user_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def _get_or_create_feed(self, source_id: int) -> Feed:
        """Get or create a feed for a source."""
        stmt = select(Feed).where(Feed.source_id == source_id)
        feed = self.db.execute(stmt).scalar_one_or_none()
        if not feed:
            feed = Feed(source_id=source_id)
            self.db.add(feed)
            self.db.commit()
            self.db.refresh(feed)
        return feed

    def _add_item(self, item: FeedItemIn, feed: Feed) -> None:
        """Add a feed item to a feed if it doesn't already exist.

        Deduplication: prefers local_id + source_name, falls back to link.
        """
        if self._item_exists(item):
            return

        # Sanitize text fields to remove NUL characters
        item_data = item.model_dump()
        for field in ("title", "description", "summary", "link", "article_url", "comments_url"):
            if field in item_data:
                item_data[field] = _sanitize_string(item_data[field])

        feed_item = FeedItem(**item_data)
        feed.feed_items.append(feed_item)

    def _item_exists(self, item: FeedItemIn) -> bool:
        """Check if a feed item already exists in the database."""
        # Prefer local_id + source_name (more reliable for HN, Reddit, etc.)
        if item.local_id:
            stmt = select(FeedItem.id).where(
                and_(
                    FeedItem.local_id == item.local_id,
                    FeedItem.source_name == item.source_name,
                )
            )
            if self.db.execute(stmt).scalar_one_or_none():
                return True

        # Fall back to link-based deduplication
        stmt = select(FeedItem.id).where(FeedItem.link == item.link)
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def _get_items_by_sources(
        self, source_ids: list[int], skip: int = 0, limit: int = 100
    ) -> list[FeedItem]:
        """Get feed items by source IDs, ordered by published date (newest first)."""
        if not source_ids:
            return []

        stmt = (
            select(FeedItem)
            .join(feed_feeditem_association, FeedItem.id == feed_feeditem_association.c.feeditem_id)
            .join(Feed, feed_feeditem_association.c.feed_id == Feed.id)
            .where(Feed.source_id.in_(source_ids))
            .order_by(
                FeedItem.published.desc().nulls_last(),
                FeedItem.created_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_recent_items_by_user(
        self, user_id: int, hours: int = 24, limit: int = 100
    ) -> list[FeedItem]:
        """Get feed items from the last N hours for a user's subscriptions."""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        subscriptions = self.db.execute(stmt).scalars().all()
        source_ids = [sub.source_id for sub in subscriptions]

        if not source_ids:
            return []

        cutoff = datetime.now() - timedelta(hours=hours)

        stmt = (
            select(FeedItem)
            .join(feed_feeditem_association, FeedItem.id == feed_feeditem_association.c.feeditem_id)
            .join(Feed, feed_feeditem_association.c.feed_id == Feed.id)
            .where(
                Feed.source_id.in_(source_ids),
                FeedItem.created_at >= cutoff,
            )
            .order_by(FeedItem.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
