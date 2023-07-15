import os
from sqlmodel import create_engine

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


DATABASE_URL = os.environ.get(
    "DATABASE_URL") or "sqlite:///./sqlite_feedjam.db"

# for local debugging
# DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/foo'


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
