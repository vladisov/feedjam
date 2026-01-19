"""Base test case with factory methods.

Inspired by ff_all patterns - provides reusable test fixtures and factories.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from main import app
from repository.db import Base, get_db
from schemas import AuthUserOut, SourceIn, SubscriptionOut, UserIn, UserOut
from service.factory import ServiceFactory

# --- Test Database Setup ---

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply override
app.dependency_overrides[get_db] = override_get_db


class BaseTestCase:
    """Base test case with common setup and factory methods.

    Usage:
        class TestUsers(BaseTestCase):
            def test_create_user(self):
                user = self.create_user("testuser")
                assert user.handle == "testuser"
    """

    client: TestClient
    db: Session
    factory: ServiceFactory

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Create client and db session
        self.client = TestClient(app)
        self.db = next(override_get_db())

        # Create factory (provides all storages and services)
        self.factory = ServiceFactory(self.db, openai_key="")

        # Convenience aliases for commonly used components
        self.user_storage = self.factory.user_storage
        self.source_storage = self.factory.source_storage
        self.subscription_storage = self.factory.subscription_storage
        self.feed_storage = self.factory.feed_storage
        self.interest_storage = self.factory.interest_storage
        self.like_history_storage = self.factory.like_history_storage
        self.feed_service = self.factory.feed_service
        self.ranking_service = self.factory.ranking_service

        yield

        # Teardown
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    # --- Factory Methods ---

    def create_user(self, handle: str = "testuser") -> UserOut:
        """Create a test user via API."""
        response = self.client.post("/users/", json={"handle": handle})
        assert response.status_code == 200, f"Failed to create user: {response.json()}"
        return UserOut(**response.json())

    def create_user_direct(self, handle: str = "testuser") -> UserOut:
        """Create a test user directly via storage."""
        return self.user_storage.create(UserIn(handle=handle))

    def create_source(
        self,
        name: str = "Test Source",
        resource_url: str = "https://example.com/feed",
    ) -> int:
        """Create a test source."""
        source = self.source_storage.create(SourceIn(name=name, resource_url=resource_url))
        return source.id

    def create_subscription(
        self,
        user_id: int,
        resource_url: str = "https://hnrss.org/best",
    ) -> SubscriptionOut:
        """Create a test subscription via API."""
        payload = {"user_id": user_id, "resource_url": resource_url}
        response = self.client.post("/subscriptions/", json=payload)
        assert response.status_code == 200, f"Failed to create subscription: {response.json()}"
        return SubscriptionOut(**response.json())

    def create_subscription_direct(
        self,
        user_id: int,
        source_id: int,
    ) -> SubscriptionOut:
        """Create a test subscription directly via storage."""
        return self.subscription_storage.create(user_id, source_id)

    def create_user_with_subscription(
        self,
        handle: str = "testuser",
        resource_url: str = "https://hnrss.org/best",
    ) -> tuple[UserOut, SubscriptionOut]:
        """Create a user with a subscription (convenience method)."""
        user = self.create_user(handle)
        subscription = self.create_subscription(user.id, resource_url)
        return user, subscription

    # --- Assertion Helpers ---

    def assert_error_response(
        self,
        response,
        status_code: int,
        message_contains: str | None = None,
    ):
        """Assert error response format."""
        assert response.status_code == status_code
        data = response.json()
        assert "message" in data
        if message_contains:
            assert message_contains in data["message"]

    def assert_not_found(self, response, entity: str | None = None):
        """Assert 404 response."""
        self.assert_error_response(response, 404, entity)

    def assert_bad_request(self, response, message_contains: str | None = None):
        """Assert 400 response."""
        self.assert_error_response(response, 400, message_contains)

    def assert_unauthorized(self, response, message_contains: str | None = None):
        """Assert 401 response."""
        self.assert_error_response(response, 401, message_contains)

    # --- Auth Helpers ---

    def register_user(
        self,
        email: str = "test@example.com",
        password: str = "password123",
    ) -> tuple[AuthUserOut, str]:
        """Register a user and return user info and access token."""
        response = self.client.post("/auth/register", json={
            "email": email,
            "password": password,
        })
        assert response.status_code == 200, f"Failed to register: {response.json()}"
        data = response.json()
        access_token = data["access_token"]

        me_response = self.client.get("/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        user = AuthUserOut(**me_response.json())
        return user, access_token

    def auth_headers(self, token: str) -> dict[str, str]:
        """Return authorization headers for a token."""
        return {"Authorization": f"Bearer {token}"}
