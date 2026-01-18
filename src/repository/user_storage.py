"""User repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from model.user import User
from schemas import UserIn, UserOut


class UserStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> UserOut | None:
        """Get a user by ID."""
        stmt = select(User).where(User.id == user_id)
        user = self.db.execute(stmt).scalar_one_or_none()
        return UserOut.model_validate(user) if user else None

    def get_by_handle(self, handle: str) -> UserOut | None:
        """Get a user by handle."""
        stmt = select(User).where(User.handle == handle)
        user = self.db.execute(stmt).scalar_one_or_none()
        return UserOut.model_validate(user) if user else None

    def get_all(self, skip: int = 0, limit: int = 100) -> list[UserOut]:
        """Get all users with pagination."""
        stmt = select(User).offset(skip).limit(limit)
        users = self.db.execute(stmt).scalars().all()
        return [UserOut.model_validate(u) for u in users]

    def get_active(self) -> list[UserOut]:
        """Get all active users."""
        stmt = select(User).where(User.is_active == True)
        users = self.db.execute(stmt).scalars().all()
        return [UserOut.model_validate(u) for u in users]

    def create(self, user: UserIn) -> UserOut:
        """Create a new user."""
        db_user = User(handle=user.handle)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return UserOut.model_validate(db_user)
