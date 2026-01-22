from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.db import Base

if TYPE_CHECKING:
    from model.source import Source


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_run: Mapped[datetime | None] = mapped_column(default=None)
    last_error: Mapped[str | None] = mapped_column(String(500), default=None)
    item_count: Mapped[int] = mapped_column(default=0)

    runs: Mapped[list["Run"]] = relationship(back_populates="subscription")
    source: Mapped["Source"] = relationship(lazy="joined")

    @property
    def source_name(self) -> str | None:
        """Get source name from related Source."""
        return self.source.name if self.source else None

    @property
    def source_type(self) -> str:
        """Get source type from related Source."""
        return self.source.source_type if self.source else "rss"

    @property
    def resource_url(self) -> str | None:
        """Get resource URL from related Source."""
        return self.source.resource_url if self.source else None


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    status: Mapped[str] = mapped_column(String(50), default="pending")
    job_type: Mapped[str] = mapped_column(String(100))
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscriptions.id"), default=None
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)

    subscription: Mapped["Subscription | None"] = relationship(back_populates="runs")
