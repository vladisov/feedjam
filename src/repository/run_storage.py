from sqlalchemy.orm import Session
from model.subscription import Run, Subscription
from model.schema.feed_schema import RunCreate, RunUpdate, RunSchema
from typing import List, Optional


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

    def get_runs_by_subscription(self, subscription_id: int) -> List[RunSchema]:
        return self.db.query(Run).filter(Run.subscription_id == subscription_id).all()

    def update_run_status(self, run_id: int, status: str) -> Optional[RunSchema]:
        db_run = self.db.query(Run).filter(Run.id == run_id).first()
        if db_run is None:
            return None
        db_run.status = status
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

    def get_runs_by_user(self, user_id: int) -> List[RunSchema]:
        subscriptions_by_user = self.db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).all()

        subscription_ids = [sub.id for sub in subscriptions_by_user]

        runs = self.db.query(Run).filter(
            Run.subscription_id.in_(subscription_ids)).all()

        return runs
