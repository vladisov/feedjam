"""User API endpoints."""

from fastapi import APIRouter, Depends

from api.exceptions import DuplicateEntityException, EntityNotFoundException
from repository.interest_storage import InterestStorage
from repository.user_storage import UserStorage
from schemas import (
    UserIn,
    UserInterestIn,
    UserInterestOut,
    UserInterestsBulkIn,
    UserOut,
    UserSettingsIn,
    UserSettingsOut,
)
from utils.dependencies import get_interest_storage, get_user_storage

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut)
def create_user(
    user: UserIn,
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Create a new user."""
    existing = user_storage.get_by_handle(user.handle)
    if existing:
        raise DuplicateEntityException("User", "handle", user.handle)
    return user_storage.create(user)


@router.get("", response_model=list[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    user_storage: UserStorage = Depends(get_user_storage),
):
    """List all users."""
    return user_storage.get_all(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Get a user by ID."""
    user = user_storage.get(user_id)
    if not user:
        raise EntityNotFoundException("User", user_id)
    return user


# --- Interest endpoints ---
@router.get("/{user_id}/interests", response_model=list[UserInterestOut])
def list_interests(
    user_id: int,
    interest_storage: InterestStorage = Depends(get_interest_storage),
):
    """List all interests for a user."""
    return interest_storage.get_by_user(user_id)


@router.put("/{user_id}/interests", response_model=list[UserInterestOut])
def replace_interests(
    user_id: int,
    data: UserInterestsBulkIn,
    interest_storage: InterestStorage = Depends(get_interest_storage),
):
    """Replace all interests for a user (bulk update from UI)."""
    return interest_storage.replace_all(user_id, data.interests)


@router.post("/{user_id}/interests", response_model=UserInterestOut)
def add_interest(
    user_id: int,
    interest: UserInterestIn,
    interest_storage: InterestStorage = Depends(get_interest_storage),
):
    """Add a single interest for a user."""
    return interest_storage.create(user_id, interest)


@router.delete("/{user_id}/interests/{interest_id}")
def delete_interest(
    user_id: int,
    interest_id: int,
    interest_storage: InterestStorage = Depends(get_interest_storage),
):
    """Delete a specific interest."""
    # Verify the interest belongs to this user
    interest = interest_storage.get(interest_id)
    if not interest or interest.user_id != user_id:
        raise EntityNotFoundException("Interest", interest_id)
    interest_storage.delete(interest_id)
    return {"status": "ok"}


# --- Settings endpoints ---
@router.get("/{user_id}/settings", response_model=UserSettingsOut)
def get_settings(
    user_id: int,
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Get user settings."""
    settings = user_storage.get_settings(user_id)
    if not settings:
        raise EntityNotFoundException("User", user_id)
    return settings


@router.put("/{user_id}/settings", response_model=UserSettingsOut)
def update_settings(
    user_id: int,
    settings: UserSettingsIn,
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Update user settings (API keys, etc)."""
    result = user_storage.update_settings(user_id, settings)
    if not result:
        raise EntityNotFoundException("User", user_id)
    return result
