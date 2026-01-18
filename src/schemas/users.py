"""User schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserIn(BaseModel):
    """Input schema for creating a user."""

    handle: str


class UserOut(BaseModel):
    """Output schema for user responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    handle: str
    is_active: bool
    created_at: datetime


class UserSettingsIn(BaseModel):
    """Input schema for updating user settings."""

    openai_api_key: str | None = None


class UserSettingsOut(BaseModel):
    """Output schema for user settings (masks sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    has_openai_key: bool = False

    @classmethod
    def from_user(cls, user) -> "UserSettingsOut":
        return cls(has_openai_key=bool(user.openai_api_key))
