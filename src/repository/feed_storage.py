"""Feed repository."""

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

    def get_active_user_feed(self, user_id: int) -> UserFeedOut | None:
        """Alias for get_user_feed."""
        return self.get_user_feed(user_id)

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

    def toggle_like(self, user_id: int, item_id: int) -> tuple[bool, str | None, bool]:
        """Toggle like state for a feed item.

        Returns: (success, source_name, new_like_state)
        """
        item = self._get_user_feed_item(user_id, item_id)
        if not item:
            return False, None, False
        # If currently disliked, remove dislike first
        if item.state.dislike:
            item.state.dislike = False
        item.state.like = not item.state.like
        self.db.commit()
        return True, item.source_name, item.state.like

    def toggle_dislike(self, user_id: int, item_id: int) -> tuple[bool, str | None, bool]:
        """Toggle dislike state for a feed item.

        Returns: (success, source_name, new_dislike_state)
        """
        item = self._get_user_feed_item(user_id, item_id)
        if not item:
            return False, None, False
        # If currently liked, remove like first
        if item.state.like:
            item.state.like = False
        item.state.dislike = not item.state.dislike
        self.db.commit()
        return True, item.source_name, item.state.dislike

    def toggle_star(self, user_id: int, item_id: int) -> tuple[bool, bool]:
        """Toggle star (save for later) state for a feed item.

        Returns: (success, new_star_state)
        """
        item = self._get_user_feed_item(user_id, item_id)
        if not item:
            return False, False
        item.state.star = not item.state.star
        self.db.commit()
        return True, item.state.star

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
        """Add a feed item to a feed (skip if exists)."""
        stmt = select(FeedItem).where(FeedItem.link == item.link)
        if self.db.execute(stmt).scalar_one_or_none():
            return  # Already exists

        feed_item = FeedItem(**item.model_dump())
        feed.feed_items.append(feed_item)
        self.db.add(feed_item)

    def _get_items_by_sources(
        self, source_ids: list[int], skip: int = 0, limit: int = 100
    ) -> list[FeedItem]:
        """Get feed items by source IDs."""
        if not source_ids:
            return []

        stmt = (
            select(FeedItem)
            .join(feed_feeditem_association, FeedItem.id == feed_feeditem_association.c.feeditem_id)
            .join(Feed, feed_feeditem_association.c.feed_id == Feed.id)
            .where(Feed.source_id.in_(source_ids))
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
