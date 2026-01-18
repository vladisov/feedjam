"""Run API endpoints."""

from fastapi import APIRouter, Depends

from repository.run_storage import RunStorage
from schemas import RunIn, RunOut
from utils.dependencies import get_run_storage

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunOut])
def list_runs(run_storage: RunStorage = Depends(get_run_storage)):
    """Get all runs (latest 100)."""
    return run_storage.get_all()


@router.get("/{subscription_id}", response_model=list[RunOut])
def get_runs_by_subscription(
    subscription_id: int,
    run_storage: RunStorage = Depends(get_run_storage),
):
    """Get all runs for a subscription."""
    return run_storage.get_by_subscription(subscription_id)


@router.post("", response_model=RunOut)
def create_run(
    run: RunIn,
    run_storage: RunStorage = Depends(get_run_storage),
):
    """Create a new run."""
    return run_storage.create(run)
