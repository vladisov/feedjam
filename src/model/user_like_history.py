"""User like history model for source affinity tracking."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from repository.db import Base


class UserLikeHistory(Base):
    """Aggregated like/dislike counts per source for a user."""

    __tablename__ = "user_like_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    like_count: Mapped[int] = mapped_column(default=0)
    dislike_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
