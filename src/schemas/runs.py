"""Run schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RunIn(BaseModel):
    """Input schema for creating a run."""

    job_type: str
    status: str = "pending"
    subscription_id: int | None = None
    user_id: int | None = None


class RunOut(BaseModel):
    """Output schema for run responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    subscription_id: int | None = None
    user_id: int | None = None
    created_at: datetime
