"""User repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from model.user import User
from schemas import UserIn, UserOut, UserSettingsIn, UserSettingsOut


class UserStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_orm(self, user_id: int) -> User | None:
        """Get user ORM object."""
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get(self, user_id: int) -> UserOut | None:
        """Get a user by ID."""
        user = self._get_orm(user_id)
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

    def get_settings(self, user_id: int) -> UserSettingsOut | None:
        """Get user settings (with masked sensitive data)."""
        user = self._get_orm(user_id)
        if not user:
            return None
        return UserSettingsOut.from_user(user)

    def update_settings(self, user_id: int, settings: UserSettingsIn) -> UserSettingsOut | None:
        """Update user settings."""
        user = self._get_orm(user_id)
        if not user:
            return None

        if settings.openai_api_key is not None:
            # Empty string means remove the key
            user.openai_api_key = settings.openai_api_key if settings.openai_api_key else None

        self.db.commit()
        self.db.refresh(user)
        return UserSettingsOut.from_user(user)

    def get_openai_key(self, user_id: int) -> str | None:
        """Get user's OpenAI API key (for internal use only)."""
        user = self._get_orm(user_id)
        return user.openai_api_key if user else None
