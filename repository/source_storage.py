from sqlalchemy.orm import Session

from model.model import Source
from model.schema.feed_schema import SourceCreate, SourceSchema, SourceUpdate


class SourceStorage:
    def __init__(self, db: Session):
        self.db = db

    def get_source(self, source_id: int):
        return self.db.query(Source).filter(Source.id == source_id).first()

    def get_sources(self, skip: int = 0, limit: int = 100):
        return self.db.query(Source).offset(skip).limit(limit).all()

    def create_source(self, source: SourceCreate) -> SourceSchema:
        db_source = self.db.query(Source).filter(
            (Source.name == source.name) |
            (Source.resource_url == source.resource_url)
        ).first()

        if db_source is None:
            db_source = Source(**source.dict())
            self.db.add(db_source)
            self.db.commit()
            self.db.refresh(db_source)
        return db_source

    def update_source(self, source: SourceUpdate, source_id: int):
        db_source = self.get_source(source_id)
        if db_source is None:
            return None
        for var, value in vars(source).items():
            setattr(db_source, var, value) if value else None
        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    def delete_source(self, source_id: int):
        db_source = self.get_source(source_id)
        if db_source is None:
            return None
        self.db.delete(db_source)
        self.db.commit()
        return {"message": "Source deleted"}
