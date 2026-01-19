"""Authentication service for password hashing and JWT token management."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.exceptions import (
    AuthException,
    DuplicateEntityException,
    InvalidCredentialsException,
    InvalidTokenException,
)
from model.user import User
from schemas import AuthUserOut, TokenOut, UserLoginIn, UserRegisterIn
from utils.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def _get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: int) -> str:
        """Create an access token."""
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Create a refresh token."""
        expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh"}
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str, token_type: str = "access") -> int:
        """Decode and validate a token, returning the user_id.

        Args:
            token: The JWT token to decode
            token_type: Expected token type ("access" or "refresh")

        Returns:
            The user_id from the token

        Raises:
            InvalidTokenException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id: str | None = payload.get("sub")
            actual_type: str | None = payload.get("type")

            if user_id is None or actual_type != token_type:
                raise InvalidTokenException()

            return int(user_id)
        except JWTError as err:
            raise InvalidTokenException() from err

    def register(self, data: UserRegisterIn) -> TokenOut:
        """Register a new user and return tokens."""
        # Check if email already exists
        existing = self._get_user_by_email(data.email)
        if existing:
            raise DuplicateEntityException("User", "email", data.email)

        # Create user with hashed password
        hashed_password = self.hash_password(data.password)
        handle = data.email.split("@")[0]  # Use email prefix as handle

        user = User(
            email=data.email,
            hashed_password=hashed_password,
            handle=handle,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Return tokens
        return TokenOut(
            access_token=self.create_access_token(user.id),
            refresh_token=self.create_refresh_token(user.id),
        )

    def login(self, data: UserLoginIn) -> TokenOut:
        """Authenticate user and return tokens."""
        user = self._get_user_by_email(data.email)
        if not user or not user.hashed_password:
            raise InvalidCredentialsException()

        if not self.verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise AuthException("Account is disabled")

        return TokenOut(
            access_token=self.create_access_token(user.id),
            refresh_token=self.create_refresh_token(user.id),
        )

    def refresh_tokens(self, refresh_token: str) -> TokenOut:
        """Refresh access token using a valid refresh token."""
        user_id = self.decode_token(refresh_token, token_type="refresh")

        user = self._get_user_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidTokenException()

        return TokenOut(
            access_token=self.create_access_token(user.id),
            refresh_token=self.create_refresh_token(user.id),
        )

    def get_current_user(self, user_id: int) -> AuthUserOut:
        """Get current user info by ID."""
        user = self._get_user_by_id(user_id)
        if not user:
            raise InvalidTokenException()

        return AuthUserOut.model_validate(user)
