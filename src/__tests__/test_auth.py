"""Authentication API tests."""

from __tests__.base import BaseTestCase
from service.auth_service import AuthService


class TestAuthService(BaseTestCase):
    """Test auth service methods directly."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "mysecretpassword"
        hashed = AuthService.hash_password(password)
        assert hashed != password
        assert AuthService.verify_password(password, hashed)

    def test_verify_password_wrong(self):
        """Test wrong password verification."""
        hashed = AuthService.hash_password("correct")
        assert not AuthService.verify_password("wrong", hashed)

    def test_create_access_token(self):
        """Test access token creation."""
        token = AuthService.create_access_token(user_id=123)
        assert token
        user_id = AuthService.decode_token(token, token_type="access")
        assert user_id == 123

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = AuthService.create_refresh_token(user_id=456)
        assert token
        user_id = AuthService.decode_token(token, token_type="refresh")
        assert user_id == 456

    def test_decode_token_wrong_type(self):
        """Test decoding token with wrong type fails."""
        access_token = AuthService.create_access_token(user_id=123)
        from api.exceptions import InvalidTokenException
        import pytest
        with pytest.raises(InvalidTokenException):
            AuthService.decode_token(access_token, token_type="refresh")

    def test_decode_invalid_token(self):
        """Test decoding invalid token fails."""
        from api.exceptions import InvalidTokenException
        import pytest
        with pytest.raises(InvalidTokenException):
            AuthService.decode_token("invalid.token.here", token_type="access")


class TestAuthRegister(BaseTestCase):
    """Test user registration endpoint."""

    def test_register_success(self):
        """Test successful registration."""
        response = self.client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_creates_user(self):
        """Test registration creates user in database."""
        self.client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "password123"
        })
        from model.user import User
        from sqlalchemy import select
        stmt = select(User).where(User.email == "newuser@example.com")
        user = self.db.execute(stmt).scalar_one_or_none()
        assert user is not None
        assert user.handle == "newuser"
        assert user.hashed_password is not None

    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails."""
        self.client.post("/auth/register", json={
            "email": "dupe@example.com",
            "password": "password123"
        })
        response = self.client.post("/auth/register", json={
            "email": "dupe@example.com",
            "password": "different"
        })
        self.assert_bad_request(response, "already exists")

    def test_register_invalid_email(self):
        """Test registration with invalid email fails."""
        response = self.client.post("/auth/register", json={
            "email": "notanemail",
            "password": "password123"
        })
        assert response.status_code == 422

    def test_register_password_too_short(self):
        """Test registration with short password fails."""
        response = self.client.post("/auth/register", json={
            "email": "short@example.com",
            "password": "short"
        })
        assert response.status_code == 422


class TestAuthLogin(BaseTestCase):
    """Test user login endpoint."""

    def test_login_success(self):
        """Test successful login."""
        self.client.post("/auth/register", json={
            "email": "login@example.com",
            "password": "password123"
        })
        response = self.client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self):
        """Test login with wrong password fails."""
        self.client.post("/auth/register", json={
            "email": "wrongpass@example.com",
            "password": "correct"
        })
        response = self.client.post("/auth/login", json={
            "email": "wrongpass@example.com",
            "password": "wrong"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user fails."""
        response = self.client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "password"
        })
        assert response.status_code == 401


class TestAuthRefresh(BaseTestCase):
    """Test token refresh endpoint."""

    def test_refresh_success(self):
        """Test successful token refresh."""
        reg_response = self.client.post("/auth/register", json={
            "email": "refresh@example.com",
            "password": "password123"
        })
        refresh_token = reg_response.json()["refresh_token"]

        response = self.client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self):
        """Test refresh with invalid token fails."""
        response = self.client.post("/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })
        assert response.status_code == 401

    def test_refresh_with_access_token_fails(self):
        """Test using access token for refresh fails."""
        reg_response = self.client.post("/auth/register", json={
            "email": "accessonly@example.com",
            "password": "password123"
        })
        access_token = reg_response.json()["access_token"]

        response = self.client.post("/auth/refresh", json={
            "refresh_token": access_token
        })
        assert response.status_code == 401


class TestAuthMe(BaseTestCase):
    """Test get current user endpoint."""

    def test_get_me_success(self):
        """Test getting current user info."""
        reg_response = self.client.post("/auth/register", json={
            "email": "me@example.com",
            "password": "password123"
        })
        access_token = reg_response.json()["access_token"]

        response = self.client.get("/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["handle"] == "me"
        assert "id" in data

    def test_get_me_no_token(self):
        """Test getting current user without token fails."""
        response = self.client.get("/auth/me")
        assert response.status_code == 403

    def test_get_me_invalid_token(self):
        """Test getting current user with invalid token fails."""
        response = self.client.get("/auth/me", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert response.status_code == 401


class TestProtectedEndpoints(BaseTestCase):
    """Test that endpoints require authentication."""

    def test_feed_requires_auth(self):
        """Test feed endpoint requires authentication."""
        response = self.client.get("/feed")
        assert response.status_code == 403

    def test_feed_with_auth(self):
        """Test feed endpoint works with authentication."""
        reg_response = self.client.post("/auth/register", json={
            "email": "feeduser@example.com",
            "password": "password123"
        })
        access_token = reg_response.json()["access_token"]

        response = self.client.get("/feed", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert response.status_code == 200

    def test_subscriptions_requires_auth(self):
        """Test subscriptions endpoint requires authentication."""
        response = self.client.get("/subscriptions")
        assert response.status_code == 403

    def test_interests_requires_auth(self):
        """Test interests endpoint requires authentication."""
        response = self.client.get("/users/me/interests")
        assert response.status_code == 403

    def test_settings_requires_auth(self):
        """Test settings endpoint requires authentication."""
        response = self.client.get("/users/me/settings")
        assert response.status_code == 403
