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
from schemas.email import InboxAddressOut
from utils.dependencies import get_current_user_id, get_interest_storage, get_user_storage

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


# --- Interest endpoints (authenticated) ---
@router.get("/me/interests", response_model=list[UserInterestOut])
def list_my_interests(
    user_id: int = Depends(get_current_user_id),
    interest_storage: InterestStorage = Depends(get_interest_storage),
):
    """List all interests for the authenticated user."""
    return interest_storage.get_by_user(user_id)


@router.put("/me/interests", response_model=list[UserInterestOut])
def replace_my_interests(
    data: UserInterestsBulkIn,
    user_id: int = Depends(get_current_user_id),
    interest_storage: InterestStorage = Depends(get_interest_storage),
):
    """Replace all interests for the authenticated user (bulk update from UI)."""
    return interest_storage.replace_all(user_id, data.interests)


@router.post("/me/interests", response_model=UserInterestOut)
def add_my_interest(
    interest: UserInterestIn,
    user_id: int = Depends(get_current_user_id),
    interest_storage: InterestStorage = Depends(get_interest_storage),
):
    """Add a single interest for the authenticated user."""
    return interest_storage.create(user_id, interest)


@router.delete("/me/interests/{interest_id}")
def delete_my_interest(
    interest_id: int,
    user_id: int = Depends(get_current_user_id),
    interest_storage: InterestStorage = Depends(get_interest_storage),
):
    """Delete a specific interest."""
    # Verify the interest belongs to this user
    interest = interest_storage.get(interest_id)
    if not interest or interest.user_id != user_id:
        raise EntityNotFoundException("Interest", interest_id)
    interest_storage.delete(interest_id)
    return {"status": "ok"}


# --- Settings endpoints (authenticated) ---
@router.get("/me/settings", response_model=UserSettingsOut)
def get_my_settings(
    user_id: int = Depends(get_current_user_id),
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Get settings for the authenticated user."""
    settings = user_storage.get_settings(user_id)
    if not settings:
        raise EntityNotFoundException("User", user_id)
    return settings


@router.put("/me/settings", response_model=UserSettingsOut)
def update_my_settings(
    settings: UserSettingsIn,
    user_id: int = Depends(get_current_user_id),
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Update settings for the authenticated user (API keys, etc)."""
    result = user_storage.update_settings(user_id, settings)
    if not result:
        raise EntityNotFoundException("User", user_id)
    return result


# --- Inbox endpoints (authenticated) ---
@router.get("/me/inbox", response_model=InboxAddressOut)
def get_my_inbox(
    user_id: int = Depends(get_current_user_id),
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Get the inbox address for the authenticated user.

    Auto-generates an email token if the user doesn't have one yet.
    """
    user = user_storage.get(user_id)
    if not user:
        raise EntityNotFoundException("User", user_id)

    if not user.inbox_address:
        user_storage.generate_email_token(user_id)
        user = user_storage.get(user_id)

    return InboxAddressOut(inbox_address=user.inbox_address, email_token=user.email_token)


@router.post("/me/inbox/regenerate", response_model=InboxAddressOut)
def regenerate_my_inbox(
    user_id: int = Depends(get_current_user_id),
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Regenerate the inbox address for the authenticated user.

    Invalidates the old address and creates a new one.
    """
    if not user_storage.generate_email_token(user_id):
        raise EntityNotFoundException("User", user_id)

    user = user_storage.get(user_id)
    return InboxAddressOut(inbox_address=user.inbox_address, email_token=user.email_token)


@router.post("/me/complete-onboarding")
def complete_onboarding(
    user_id: int = Depends(get_current_user_id),
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Mark the user's onboarding as completed."""
    if not user_storage.complete_onboarding(user_id):
        raise EntityNotFoundException("User", user_id)
    return {"status": "ok"}
