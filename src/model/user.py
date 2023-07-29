
from repository.db import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    handle = Column(String,)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
