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
