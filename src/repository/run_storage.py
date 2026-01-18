"""Run repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from model.subscription import Run
from schemas import RunIn, RunOut


class RunStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, run_id: int) -> RunOut | None:
        """Get a run by ID."""
        stmt = select(Run).where(Run.id == run_id)
        run = self.db.execute(stmt).scalar_one_or_none()
        return RunOut.model_validate(run) if run else None

    def get_by_subscription(self, subscription_id: int) -> list[RunOut]:
        """Get all runs for a subscription."""
        stmt = select(Run).where(Run.subscription_id == subscription_id)
        runs = self.db.execute(stmt).scalars().all()
        return [RunOut.model_validate(r) for r in runs]

    def get_all(self, limit: int = 100) -> list[RunOut]:
        """Get all runs (latest first)."""
        stmt = select(Run).order_by(Run.created_at.desc()).limit(limit)
        runs = self.db.execute(stmt).scalars().all()
        return [RunOut.model_validate(r) for r in runs]

    def get_pending(self) -> list[Run]:
        """Get all pending runs (returns ORM objects for processing)."""
        stmt = select(Run).where(Run.status == "pending")
        return list(self.db.execute(stmt).scalars().all())

    def create(self, run: RunIn) -> RunOut:
        """Create a new run."""
        db_run = Run(**run.model_dump())
        self.db.add(db_run)
        self.db.commit()
        self.db.refresh(db_run)
        return RunOut.model_validate(db_run)

    def update_status(self, run_id: int, status: str) -> RunOut | None:
        """Update run status."""
        stmt = select(Run).where(Run.id == run_id)
        run = self.db.execute(stmt).scalar_one_or_none()
        if not run:
            return None
        run.status = status
        self.db.commit()
        self.db.refresh(run)
        return RunOut.model_validate(run)
