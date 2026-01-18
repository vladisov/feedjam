"""Source schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceIn(BaseModel):
    """Input schema for creating a source."""

    name: str
    resource_url: str
    source_type: str = "rss"  # Default to RSS


class SourceOut(BaseModel):
    """Output schema for source responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    resource_url: str
    source_type: str
    is_active: bool
    created_at: datetime
