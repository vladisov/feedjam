from datetime import datetime
from enum import Enum

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from repository.db import Base


class SourceType(str, Enum):
    """Supported source types for feed parsing."""

    RSS = "rss"
    HACKERNEWS = "hackernews"
    TELEGRAM = "telegram"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    GITHUB = "github"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    resource_url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(50), default=SourceType.RSS.value)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
