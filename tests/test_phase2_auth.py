"""
Phase 2 Tests: Authentication & Security
Tests registration, login, JWT auth, user isolation, and security.
"""
import time
import pytest
import jwt
from datetime import datetime, timedelta

# Import test constants
from conftest import TEST_USER_ID, TEST_USER_ID_2, TEST_PASSWORD


class TestRegistration:
    """Test user registration flows."""

    def test_register_valid_user(self, client):
        """Test: Register with valid data returns user (no password_hash in response)."""
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        # SECURITY: password_hash must NOT be in response
        assert "password_hash" not in data
        assert "password" not in data

    def test_register_duplicate_username(self, client):
        """Test: Register with duplicate username returns 409."""
        response = client.post("/api/auth/register", json={
            "username": "testuser",  # Already exists from fixture
            "email": "different@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 409

    def test_register_short_password(self, client):
        """Test: Register with short password returns 422."""
        response = client.post("/api/auth/register", json={
            "username": "shortpwuser",
            "email": "shortpw@example.com",
            "password": "short",  # < 8 chars
        })
        assert response.status_code == 422


class TestLogin:
    """Test login and JWT token flows."""

    def test_login_valid_credentials(self, client):
        """Test: Login with correct credentials returns JWT."""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": TEST_PASSWORD,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
        # Verify token is valid JWT
        assert len(data["access_token"].split(".")) == 3

    def test_login_wrong_password(self, client):
        """Test: Login with wrong password returns 401."""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword123",
        })
        assert response.status_code == 401
        # Generic error message — doesn't reveal if username or password is wrong
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_nonexistent_user(self, client):
        """Test: Login with non-existent user returns 401 (same generic message)."""
        response = client.post("/api/auth/login", json={
            "username": "ghostuser",
            "password": "anypassword123",
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"


class TestProtectedRoutes:
    """Test that routes require valid authentication."""

    def test_access_without_token_returns_401(self, client):
        """Test: Access /api/clients without token returns 401."""
        response = client.get("/api/clients")
        assert response.status_code in (401, 403)

    def test_access_with_valid_token(self, client, auth_headers):
        """Test: Access /api/clients with valid token returns data."""
        response = client.get("/api/clients", headers=auth_headers)
        assert response.status_code == 200

    def test_access_with_expired_token(self, client):
        """Test: Access /api/clients with expired token returns 401."""
        from config import settings
        # Create an expired token
        payload = {
            "user_id": TEST_USER_ID,
            "iat": datetime.utcnow() - timedelta(hours=48),
            "exp": datetime.utcnow() - timedelta(hours=24),  # Expired
        }
        expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.get("/api/clients", headers=headers)
        assert response.status_code == 401

    def test_access_with_invalid_token(self, client):
        """Test: Access with garbage token returns 401."""
        headers = {"Authorization": "Bearer invalid.garbage.token"}
        response = client.get("/api/clients", headers=headers)
        assert response.status_code == 401


class TestUserIsolationAuth:
    """Test that users can only see their own data."""

    def test_user_a_cannot_see_user_b_clients(self, client, auth_headers, second_user, second_auth_headers):
        """Test: User A cannot see User B's clients."""
        # User A creates a client
        client.post("/api/clients", json={"name": "User A Client"}, headers=auth_headers)

        # User B creates a client
        client.post("/api/clients", json={"name": "User B Client"}, headers=second_auth_headers)

        # User A should only see their own client
        response = client.get("/api/clients", headers=auth_headers)
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "User A Client"

        # User B should only see their own client
        response = client.get("/api/clients", headers=second_auth_headers)
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "User B Client"


class TestPasswordSecurity:
    """Test password security requirements."""

    def test_password_is_hashed_in_db(self, client, db):
        """Test: Password in database is not plaintext."""
        from models.user import User
        user = db.query(User).filter(User.username == "testuser").first()
        assert user.password_hash != TEST_PASSWORD
        assert user.password_hash.startswith("$2b$12$")  # bcrypt cost factor 12


class TestAuthMe:
    """Test the /api/auth/me endpoint."""

    def test_get_me_with_valid_token(self, client, auth_headers):
        """Test: GET /api/auth/me returns current user info."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password_hash" not in data
