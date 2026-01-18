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
from repository.feed_storage import FeedStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from repository.user_storage import UserStorage
from schemas import SourceIn, SubscriptionOut, UserIn, UserOut
from service.data_extractor import DataExtractor
from service.feed_service import FeedService

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

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Create client and db session
        self.client = TestClient(app)
        self.db = next(override_get_db())

        # Create storages
        self.user_storage = UserStorage(self.db)
        self.source_storage = SourceStorage(self.db)
        self.subscription_storage = SubscriptionStorage(self.db)
        self.feed_storage = FeedStorage(self.db)

        # Create services
        self.data_extractor = DataExtractor("")  # Empty key for tests
        self.feed_service = FeedService(
            self.feed_storage,
            self.subscription_storage,
            self.source_storage,
            self.data_extractor,
        )

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
