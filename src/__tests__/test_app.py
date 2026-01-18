"""User API tests."""

from __tests__.base import BaseTestCase


class TestUserAPI(BaseTestCase):
    """Test user-related API endpoints."""

    def test_create_user(self):
        """Test creating a new user."""
        user = self.create_user("testuser")
        assert user.handle == "testuser"
        assert user.is_active

    def test_create_user_duplicate_handle(self):
        """Test that duplicate handles are rejected."""
        self.create_user("duplicate")
        response = self.client.post("/users/", json={"handle": "duplicate"})
        self.assert_bad_request(response, "already exists")

    def test_get_user(self):
        """Test getting a user by ID."""
        created = self.create_user("getme")
        response = self.client.get(f"/users/{created.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["handle"] == "getme"

    def test_get_user_not_found(self):
        """Test 404 for non-existent user."""
        response = self.client.get("/users/9999")
        self.assert_not_found(response, "User")

    def test_list_users(self):
        """Test listing all users."""
        self.create_user("user1")
        self.create_user("user2")
        response = self.client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_users_pagination(self):
        """Test user list pagination."""
        for i in range(5):
            self.create_user(f"user{i}")
        response = self.client.get("/users/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
