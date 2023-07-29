
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from repository.db import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    resource_url = Column(String, unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
