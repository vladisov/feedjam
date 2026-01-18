"""User interest schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserInterestIn(BaseModel):
    """Input schema for creating/updating a user interest."""

    topic: str = Field(..., max_length=100)
    weight: float = Field(default=1.0, ge=0.0, le=2.0)


class UserInterestOut(BaseModel):
    """Output schema for user interest responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    topic: str
    weight: float
    created_at: datetime
    updated_at: datetime


class UserInterestsBulkIn(BaseModel):
    """Bulk update schema for replacing all user interests."""

    interests: list[UserInterestIn]
