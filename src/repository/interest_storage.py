"""User interest repository."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from model.user_interest import UserInterest
from schemas import UserInterestIn, UserInterestOut


class InterestStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user(self, user_id: int) -> list[UserInterestOut]:
        """Get all interests for a user."""
        stmt = select(UserInterest).where(UserInterest.user_id == user_id)
        interests = self.db.execute(stmt).scalars().all()
        return [UserInterestOut.model_validate(i) for i in interests]

    def get(self, interest_id: int) -> UserInterestOut | None:
        """Get an interest by ID."""
        stmt = select(UserInterest).where(UserInterest.id == interest_id)
        interest = self.db.execute(stmt).scalar_one_or_none()
        return UserInterestOut.model_validate(interest) if interest else None

    def create(self, user_id: int, interest: UserInterestIn) -> UserInterestOut:
        """Create a new interest for a user."""
        db_interest = UserInterest(
            user_id=user_id,
            topic=interest.topic,
            weight=interest.weight,
        )
        self.db.add(db_interest)
        self.db.commit()
        self.db.refresh(db_interest)
        return UserInterestOut.model_validate(db_interest)

    def delete(self, interest_id: int) -> bool:
        """Delete an interest by ID."""
        stmt = delete(UserInterest).where(UserInterest.id == interest_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def delete_all_for_user(self, user_id: int) -> int:
        """Delete all interests for a user. Returns count deleted."""
        stmt = delete(UserInterest).where(UserInterest.user_id == user_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def replace_all(self, user_id: int, interests: list[UserInterestIn]) -> list[UserInterestOut]:
        """Replace all interests for a user (bulk update)."""
        # Delete existing
        self.delete_all_for_user(user_id)

        # Create new ones
        new_interests = []
        for interest in interests:
            db_interest = UserInterest(
                user_id=user_id,
                topic=interest.topic,
                weight=interest.weight,
            )
            self.db.add(db_interest)
            new_interests.append(db_interest)

        self.db.commit()

        # Refresh to get IDs and timestamps
        for interest in new_interests:
            self.db.refresh(interest)

        return [UserInterestOut.model_validate(i) for i in new_interests]

    def get_as_map(self, user_id: int) -> dict[str, float]:
        """Get user interests as a topic -> weight map."""
        interests = self.get_by_user(user_id)
        return {i.topic.lower(): i.weight for i in interests}
