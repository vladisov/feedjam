"""Source schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceIn(BaseModel):
    """Input schema for creating a source."""

    name: str
    resource_url: str


class SourceOut(BaseModel):
    """Output schema for source responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    resource_url: str
    is_active: bool
    created_at: datetime
