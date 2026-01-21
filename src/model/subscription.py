from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.db import Base


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
