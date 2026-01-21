import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sqlite_feedjam.db")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # For SQLite, we need these settings
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _db_session() -> Generator[Session, None, None]:
    """Core database session logic."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# FastAPI dependency (needs raw generator)
def get_db() -> Generator[Session, None, None]:
    """Database session for FastAPI Depends()."""
    yield from _db_session()


# Context manager for background tasks
get_db_session = contextmanager(_db_session)
