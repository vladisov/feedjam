"""User API endpoints."""

from fastapi import APIRouter, Depends

from api.exceptions import DuplicateEntityException, EntityNotFoundException
from repository.user_storage import UserStorage
from schemas import UserIn, UserOut
from utils.dependencies import get_user_storage

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut)
def create_user(
    user: UserIn,
    user_storage: UserStorage = Depends(get_user_storage),
):
    """Create a new user."""
    existing = user_storage.get_by_handle(user.handle)
    if existing:
        raise DuplicateEntityException("User", "handle", user.handle)
    return user_storage.create(user)


@router.get("/", response_model=list[UserOut])
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
