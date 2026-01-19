"""Authentication API endpoints."""

from fastapi import APIRouter, Depends

from schemas import AuthUserOut, RefreshTokenIn, TokenOut, UserLoginIn, UserRegisterIn
from service.auth_service import AuthService
from utils.dependencies import get_auth_service, get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(
    data: UserRegisterIn,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user and return authentication tokens."""
    return auth_service.register(data)


@router.post("/login", response_model=TokenOut)
def login(
    data: UserLoginIn,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return tokens."""
    return auth_service.login(data)


@router.post("/refresh", response_model=TokenOut)
def refresh_token(
    data: RefreshTokenIn,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using a valid refresh token."""
    return auth_service.refresh_tokens(data.refresh_token)


@router.get("/me", response_model=AuthUserOut)
def get_current_user(
    user_id: int = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current authenticated user info."""
    return auth_service.get_current_user(user_id)
