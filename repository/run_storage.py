from sqlalchemy.orm import Session
from model.model import Run
from model.schema.feed_schema import RunCreate, RunUpdate, RunSchema
from typing import Optional


class RunStorage:
    def __init__(self, db: Session):
        self.db = db

    def create_run(self, run: RunCreate) -> RunSchema:
        db_run = Run(**run.dict())
        self.db.add(db_run)
        self.db.commit()
        self.db.refresh(db_run)
        return RunSchema.from_orm(db_run)

    def get_run(self, run_id: int) -> Optional[RunSchema]:
        db_run = self.db.query(Run).filter(Run.id == run_id).first()
        if db_run is None:
            return None
        return RunSchema.from_orm(db_run)

    def update_run_status(self, run_id: int, status: str) -> Optional[RunSchema]:
        db_run = self.db.query(Run).filter(Run.id == run_id).first()
        if db_run is None:
            return None
        db_run.last_run_status = status
        self.db.commit()
        self.db.refresh(db_run)
        return RunSchema.from_orm(db_run)

    def update_run(self, run_id: int, run_update: RunUpdate) -> Optional[RunSchema]:
        db_run = self.db.query(Run).filter(Run.id == run_id).first()
        if db_run is None:
            return None
        for var, value in vars(run_update).items():
            if value:
                setattr(db_run, var, value)
        self.db.commit()
        self.db.refresh(db_run)
        return RunSchema.from_orm(db_run)
