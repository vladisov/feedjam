

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from repository.db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    created_at = Column(DateTime, server_default=func.now())
    last_run = Column(DateTime,)

    runs = relationship("Run", back_populates="subscription")


class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String, default="pending")
    job_type = Column(String,)

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    subscription = relationship("Subscription", back_populates="runs")
