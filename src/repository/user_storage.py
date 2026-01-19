"""User repository."""

import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from model.user import User
from schemas import UserIn, UserOut, UserSettingsIn, UserSettingsOut

# Domain for inbound email addresses
INBOX_DOMAIN = "in.feedjam.app"

# Base62 alphabet for clean tokens
BASE62 = string.ascii_letters + string.digits


def _generate_email_token(length: int = 10) -> str:
    """Generate a clean base62 token for email inbox address."""
    return "".join(secrets.choice(BASE62) for _ in range(length))


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
        return self._to_user_out(user) if user else None

    def _to_user_out(self, user: User) -> UserOut:
        """Convert User ORM to UserOut with computed inbox_address."""
        inbox_address = f"{user.email_token}@{INBOX_DOMAIN}" if user.email_token else None
        return UserOut(
            id=user.id,
            handle=user.handle,
            is_active=user.is_active,
            created_at=user.created_at,
            email_token=user.email_token,
            inbox_address=inbox_address,
        )

    def get_by_handle(self, handle: str) -> UserOut | None:
        """Get a user by handle."""
        stmt = select(User).where(User.handle == handle)
        user = self.db.execute(stmt).scalar_one_or_none()
        return self._to_user_out(user) if user else None

    def get_by_email_token(self, email_token: str) -> UserOut | None:
        """Get a user by their email inbox token."""
        stmt = select(User).where(User.email_token == email_token)
        user = self.db.execute(stmt).scalar_one_or_none()
        return self._to_user_out(user) if user else None

    def get_all(self, skip: int = 0, limit: int = 100) -> list[UserOut]:
        """Get all users with pagination."""
        stmt = select(User).offset(skip).limit(limit)
        users = self.db.execute(stmt).scalars().all()
        return [self._to_user_out(u) for u in users]

    def get_active(self) -> list[UserOut]:
        """Get all active users."""
        stmt = select(User).where(User.is_active == True)
        users = self.db.execute(stmt).scalars().all()
        return [self._to_user_out(u) for u in users]

    def create(self, user: UserIn) -> UserOut:
        """Create a new user with a unique email token."""
        db_user = User(handle=user.handle, email_token=_generate_email_token())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_user_out(db_user)

    def generate_email_token(self, user_id: int) -> str | None:
        """Generate or regenerate email token for a user.

        Returns the new token, or None if user not found.
        """
        user = self._get_orm(user_id)
        if not user:
            return None

        user.email_token = _generate_email_token()
        self.db.commit()
        self.db.refresh(user)
        return user.email_token

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
            user.openai_api_key = settings.openai_api_key or None

        self.db.commit()
        self.db.refresh(user)
        return UserSettingsOut.from_user(user)

    def get_openai_key(self, user_id: int) -> str | None:
        """Get user's OpenAI API key (for internal use only)."""
        user = self._get_orm(user_id)
        return user.openai_api_key if user else None
