"""Repository for persistent user item state."""

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from model.feed import FeedItem
from model.user_item_state import UserItemState


class UserItemStateStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, user_id: int, feed_item_id: int) -> UserItemState:
        """Get or create a user item state record."""
        state = self.get_state(user_id, feed_item_id)
        if not state:
            state = UserItemState(user_id=user_id, feed_item_id=feed_item_id)
            self.db.add(state)
            self.db.flush()
        return state

    def set_read(self, user_id: int, feed_item_id: int, value: bool = True) -> None:
        """Mark item as read."""
        state = self.get_or_create(user_id, feed_item_id)
        state.read = value
        self.db.commit()

    def set_liked(self, user_id: int, feed_item_id: int, value: bool) -> None:
        """Set liked state (also clears disliked if liking)."""
        state = self.get_or_create(user_id, feed_item_id)
        if value:
            state.disliked = False
        state.liked = value
        self.db.commit()

    def set_disliked(self, user_id: int, feed_item_id: int, value: bool) -> None:
        """Set disliked state (also clears liked if disliking)."""
        state = self.get_or_create(user_id, feed_item_id)
        if value:
            state.liked = False
        state.disliked = value
        self.db.commit()

    def set_starred(self, user_id: int, feed_item_id: int, value: bool) -> None:
        """Set starred state."""
        state = self.get_or_create(user_id, feed_item_id)
        state.starred = value
        self.db.commit()

    def set_hidden(self, user_id: int, feed_item_id: int, value: bool) -> None:
        """Set hidden state."""
        state = self.get_or_create(user_id, feed_item_id)
        state.hidden = value
        self.db.commit()

    def toggle_liked(self, user_id: int, feed_item_id: int) -> tuple[bool, str | None]:
        """Toggle liked state. Returns (new_liked_state, source_name).

        Like clears hidden (mutually exclusive) since liking is a positive signal.
        """
        state = self.get_or_create(user_id, feed_item_id)
        state.liked = not state.liked
        if state.liked:
            # Like clears hidden (mutually exclusive)
            state.hidden = False
        self.db.commit()
        source_name = self._get_source_name(feed_item_id)
        return state.liked, source_name

    def toggle_disliked(self, user_id: int, feed_item_id: int) -> tuple[bool, str | None]:
        """Toggle disliked state. Returns (new_disliked_state, source_name)."""
        state = self.get_or_create(user_id, feed_item_id)
        if state.liked:
            state.liked = False
        state.disliked = not state.disliked
        self.db.commit()
        source_name = self._get_source_name(feed_item_id)
        return state.disliked, source_name

    def toggle_starred(self, user_id: int, feed_item_id: int) -> bool:
        """Toggle starred state. Returns new_starred_state."""
        state = self.get_or_create(user_id, feed_item_id)
        state.starred = not state.starred
        self.db.commit()
        return state.starred

    def toggle_hidden(self, user_id: int, feed_item_id: int) -> tuple[bool, str | None]:
        """Toggle hidden state. Returns (new_hidden_state, source_name).

        Hide acts as a negative signal for ranking. When hiding, clears liked.
        When unhiding, also marks the item as unread to give it a fresh start.
        """
        state = self.get_or_create(user_id, feed_item_id)
        state.hidden = not state.hidden
        if state.hidden:
            # Hide clears liked (mutually exclusive)
            state.liked = False
        else:
            # When unhiding, mark as unread so item appears fresh
            state.read = False
        self.db.commit()
        source_name = self._get_source_name(feed_item_id)
        return state.hidden, source_name

    def _get_source_name(self, feed_item_id: int) -> str | None:
        """Get source_name for a feed item."""
        stmt = select(FeedItem.source_name).where(FeedItem.id == feed_item_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_read_item_ids(self, user_id: int) -> set[int]:
        """Get all feed_item_ids that user has read."""
        stmt = select(UserItemState.feed_item_id).where(
            and_(UserItemState.user_id == user_id, UserItemState.read.is_(True))
        )
        return set(self.db.execute(stmt).scalars().all())

    def get_active_feed_item_ids(self, user_id: int) -> list[int]:
        """Get feed_item_ids from the user's active feed."""
        from model.user_feed import UserFeed, UserFeedItem

        stmt = (
            select(UserFeedItem.feed_item_id)
            .join(UserFeed)
            .where(and_(UserFeed.user_id == user_id, UserFeed.is_active == True))
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_read_unhidden_item_ids(self, user_id: int, feed_item_ids: list[int]) -> list[int]:
        """Get feed_item_ids that are read but not hidden."""
        if not feed_item_ids:
            return []
        stmt = select(UserItemState.feed_item_id).where(
            and_(
                UserItemState.user_id == user_id,
                UserItemState.feed_item_id.in_(feed_item_ids),
                UserItemState.read == True,
                UserItemState.hidden == False,
            )
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_unread_unhidden_item_ids(self, user_id: int, feed_item_ids: list[int]) -> list[int]:
        """Get feed_item_ids that are unread and not hidden.

        Items without UserItemState are considered unread.
        """
        if not feed_item_ids:
            return []
        # Get items that ARE read or hidden
        stmt = select(UserItemState.feed_item_id).where(
            and_(
                UserItemState.user_id == user_id,
                UserItemState.feed_item_id.in_(feed_item_ids),
                (UserItemState.read == True) | (UserItemState.hidden == True),
            )
        )
        excluded = set(self.db.execute(stmt).scalars().all())
        return [fid for fid in feed_item_ids if fid not in excluded]

    def bulk_set_read(self, user_id: int, feed_item_ids: list[int]) -> None:
        """Mark multiple items as read."""
        self._bulk_set_field(user_id, feed_item_ids, "read")

    def bulk_set_hidden(self, user_id: int, feed_item_ids: list[int]) -> None:
        """Mark multiple items as hidden."""
        self._bulk_set_field(user_id, feed_item_ids, "hidden")

    def _bulk_set_field(self, user_id: int, feed_item_ids: list[int], field: str) -> None:
        """Set a field to True for multiple items."""
        for feed_item_id in feed_item_ids:
            state = self.get_or_create(user_id, feed_item_id)
            setattr(state, field, True)
        self.db.commit()

    def search(
        self,
        user_id: int,
        liked: bool | None = None,
        disliked: bool | None = None,
        starred: bool | None = None,
        read: bool | None = None,
        hidden: bool | None = None,
        text: str | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Search user's historical items by state filters.

        Returns dicts with FeedItem fields plus user state.
        """
        stmt = (
            select(FeedItem, UserItemState)
            .join(UserItemState, UserItemState.feed_item_id == FeedItem.id)
            .where(UserItemState.user_id == user_id)
        )

        # Apply state filters
        state_filters = [
            (liked, UserItemState.liked),
            (disliked, UserItemState.disliked),
            (starred, UserItemState.starred),
            (read, UserItemState.read),
            (hidden, UserItemState.hidden),
        ]
        for value, column in state_filters:
            if value is not None:
                stmt = stmt.where(column == value)

        # Apply text search
        if text:
            pattern = f"%{text.lower()}%"
            stmt = stmt.where(
                FeedItem.title.ilike(pattern)
                | FeedItem.summary.ilike(pattern)
                | FeedItem.description.ilike(pattern)
            )

        # Apply source filter
        if source:
            stmt = stmt.where(FeedItem.source_name.ilike(f"%{source}%"))

        stmt = stmt.order_by(UserItemState.updated_at.desc()).offset(offset).limit(limit)

        return [
            self._build_search_result(feed_item, state)
            for feed_item, state in self.db.execute(stmt).all()
        ]

    def _build_search_result(self, feed_item: FeedItem, state: UserItemState) -> dict:
        """Build a search result dict from FeedItem and UserItemState."""
        return {
            "id": feed_item.id,
            "feed_item_id": feed_item.id,
            "title": feed_item.title,
            "link": feed_item.link,
            "source_name": feed_item.source_name,
            "description": feed_item.description,
            "article_url": feed_item.article_url,
            "comments_url": feed_item.comments_url,
            "points": feed_item.points,
            "views": feed_item.views,
            "summary": feed_item.summary,
            "published": feed_item.published,
            "created_at": feed_item.created_at,
            "updated_at": feed_item.updated_at,
            "state": {
                "read": state.read,
                "like": state.liked,
                "dislike": state.disliked,
                "star": state.starred,
                "hide": state.hidden,
            },
        }

    def get_state(self, user_id: int, feed_item_id: int) -> UserItemState | None:
        """Get state for a specific item."""
        stmt = select(UserItemState).where(
            and_(
                UserItemState.user_id == user_id,
                UserItemState.feed_item_id == feed_item_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
