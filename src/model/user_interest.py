"""User interest model for personalized ranking."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from repository.db import Base


class UserInterest(Base):
    """User interests/topics for feed ranking."""

    __tablename__ = "user_interests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic: Mapped[str] = mapped_column(String(100))
    weight: Mapped[float] = mapped_column(default=1.0)  # Range 0.0-2.0
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
