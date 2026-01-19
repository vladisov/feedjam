"""Authentication schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterIn(BaseModel):
    """Input schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLoginIn(BaseModel):
    """Input schema for user login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    """Output schema for authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenIn(BaseModel):
    """Input schema for token refresh."""

    refresh_token: str


class AuthUserOut(BaseModel):
    """Output schema for authenticated user info."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    handle: str
    is_active: bool
    is_verified: bool
    created_at: datetime
