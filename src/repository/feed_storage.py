"""Feed repository."""

from datetime import datetime, timedelta

from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from model.feed import Feed, FeedItem, feed_feeditem_association
from model.source import Source
from model.subscription import Subscription
from model.user_feed import UserFeed, UserFeedItem
from model.user_item_state import UserItemState
from schemas import FeedItemIn
from schemas.feeds import ItemState, UserFeedIn, UserFeedItemOut, UserFeedOut
from utils.logger import get_logger

logger = get_logger(__name__)


def _get_source_type_map(db: Session, source_names: list[str]) -> dict[str, str]:
    """Get a mapping of source_name -> source_type for the given source names."""
    if not source_names:
        return {}
    stmt = select(Source.name, Source.source_type).where(Source.name.in_(source_names))
    results = db.execute(stmt).all()
    return dict(results)


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
        """Get the active user feed with state from persistent UserItemState."""
        # Get the active feed
        feed_stmt = (
            select(UserFeed)
            .where(and_(UserFeed.user_id == user_id, UserFeed.is_active == True))
            .order_by(UserFeed.created_at.desc())
            .limit(1)
        )
        user_feed = self.db.execute(feed_stmt).scalar_one_or_none()
        if not user_feed:
            return None

        # Get items with persistent state (LEFT JOIN to handle items without state)
        items_stmt = (
            select(UserFeedItem, UserItemState)
            .outerjoin(
                UserItemState,
                and_(
                    UserItemState.user_id == UserFeedItem.user_id,
                    UserItemState.feed_item_id == UserFeedItem.feed_item_id,
                ),
            )
            .where(UserFeedItem.user_feed_id == user_feed.id)
            .order_by(UserFeedItem.rank_score.desc())
        )
        results = self.db.execute(items_stmt).all()

        # Batch fetch source types for all items
        source_names = list({item.source_name for item, _ in results if item.source_name})
        source_type_map = _get_source_type_map(self.db, source_names)

        # Build response with mapped state and source_type
        feed_items = [
            self._build_user_feed_item_out(
                item, state, source_type_map.get(item.source_name, "rss")
            )
            for item, state in results
        ]

        return UserFeedOut(
            id=user_feed.id,
            user_id=user_feed.user_id,
            is_active=user_feed.is_active,
            created_at=user_feed.created_at,
            updated_at=user_feed.updated_at,
            user_feed_items=feed_items,
        )

    def _build_user_feed_item_out(
        self, item: UserFeedItem, state: UserItemState | None, source_type: str = "rss"
    ) -> UserFeedItemOut:
        """Build UserFeedItemOut with state from persistent UserItemState."""
        item_state = ItemState(
            read=state.read if state else False,
            like=state.liked if state else False,
            dislike=state.disliked if state else False,
            star=state.starred if state else False,
            hide=state.hidden if state else False,
        )
        return UserFeedItemOut(
            id=item.id,
            feed_item_id=item.feed_item_id,
            user_id=item.user_id,
            title=item.title,
            description=item.description or "",
            source_name=item.source_name,
            source_type=source_type,
            article_url=item.article_url,
            comments_url=item.comments_url,
            points=item.points,
            views=item.views,
            summary=item.summary,
            rank_score=item.rank_score,
            state=item_state,
            published=item.published,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def save_user_feed(self, user_feed: UserFeedIn) -> int:
        """Save a new user feed. State comes from persistent UserItemState on read."""
        new_user_feed = UserFeed(
            user_id=user_feed.user_id,
            is_active=user_feed.is_active,
        )
        self.db.add(new_user_feed)
        self.db.flush()

        for item in user_feed.user_feed_items:
            item_data = item.model_dump(exclude={"state", "source_type"})
            item_data["user_feed_id"] = new_user_feed.id
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

    def deactivate_all_user_feeds(self, user_id: int) -> int:
        """Deactivate all active feeds for a user. Returns count of deactivated feeds."""
        stmt = (
            update(UserFeed)
            .where(and_(UserFeed.user_id == user_id, UserFeed.is_active == True))
            .values(is_active=False)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    # --- Private helpers ---

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
