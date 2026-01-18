"""Source repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from model.source import Source
from schemas import SourceIn, SourceOut


class SourceStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, source_id: int) -> Source | None:
        """Get a source by ID (returns ORM object for service layer)."""
        stmt = select(Source).where(Source.id == source_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_url(self, resource_url: str) -> Source | None:
        """Get a source by URL."""
        stmt = select(Source).where(Source.resource_url == resource_url)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[SourceOut]:
        """Get all sources with pagination."""
        stmt = select(Source).offset(skip).limit(limit)
        sources = self.db.execute(stmt).scalars().all()
        return [SourceOut.model_validate(s) for s in sources]

    def create(self, source: SourceIn) -> Source:
        """Create a source or return existing one."""
        existing = self.get_by_url(source.resource_url)
        if existing:
            return existing

        db_source = Source(
            name=source.name,
            resource_url=source.resource_url,
            source_type=source.source_type,
        )
        self.db.add(db_source)
        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    def delete(self, source_id: int) -> bool:
        """Delete a source by ID."""
        source = self.get(source_id)
        if not source:
            return False
        self.db.delete(source)
        self.db.commit()
        return True
