"""User like history repository."""

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from model.user_like_history import UserLikeHistory


class LikeHistoryStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user(self, user_id: int) -> list[UserLikeHistory]:
        """Get all like history for a user."""
        stmt = select(UserLikeHistory).where(UserLikeHistory.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def get_or_create(self, user_id: int, source_name: str) -> UserLikeHistory:
        """Get or create a like history entry for a user and source."""
        stmt = select(UserLikeHistory).where(
            and_(
                UserLikeHistory.user_id == user_id,
                UserLikeHistory.source_name == source_name,
            )
        )
        history = self.db.execute(stmt).scalar_one_or_none()

        if not history:
            history = UserLikeHistory(
                user_id=user_id,
                source_name=source_name,
                like_count=0,
                dislike_count=0,
            )
            self.db.add(history)
            self.db.commit()
            self.db.refresh(history)

        return history

    def increment_like(self, user_id: int, source_name: str) -> None:
        """Increment like count for a source."""
        history = self.get_or_create(user_id, source_name)
        history.like_count += 1
        self.db.commit()

    def decrement_like(self, user_id: int, source_name: str) -> None:
        """Decrement like count for a source."""
        history = self.get_or_create(user_id, source_name)
        if history.like_count > 0:
            history.like_count -= 1
        self.db.commit()

    def increment_dislike(self, user_id: int, source_name: str) -> None:
        """Increment dislike count for a source."""
        history = self.get_or_create(user_id, source_name)
        history.dislike_count += 1
        self.db.commit()

    def decrement_dislike(self, user_id: int, source_name: str) -> None:
        """Decrement dislike count for a source."""
        history = self.get_or_create(user_id, source_name)
        if history.dislike_count > 0:
            history.dislike_count -= 1
        self.db.commit()

    def get_source_affinity_map(self, user_id: int) -> dict[str, float]:
        """Get source affinities as a source_name -> affinity map.

        Affinity is calculated as (likes - dislikes) / total.
        Returns values in range [-1.0, 1.0].
        """
        histories = self.get_by_user(user_id)
        affinities = {}
        for h in histories:
            total = h.like_count + h.dislike_count
            if total > 0:
                affinities[h.source_name] = (h.like_count - h.dislike_count) / total
        return affinities
