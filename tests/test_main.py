"""
Basic tests to verify the application can start and basic functionality works.
"""
import pytest
from app.main import app


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "AI Learning Assistant API"


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "Test1234",
            "course": "B.Tech CSE",
            "semester": 3,
            "daily_study_time": 120
        }
    )
    if response.status_code != 201:
        print(f"Error response: {response.json()}")
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"


def test_login_user(client):
    """Test user login."""
    # First register a user
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Login Test",
            "email": "logintest@example.com",
            "password": "Test1234",
            "course": "B.Tech CSE",
            "semester": 3
        }
    )
    
    # Then login
    response = client.post(
        "/api/auth/login",
        json={
            "email": "logintest@example.com",
            "password": "Test1234"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user_id" in data


def test_claim_full_access(client):
    """Test claiming full access grants the user a premium/full-access flag."""
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Full Access User",
            "email": "fullaccess@example.com",
            "password": "Test1234",
            "course": "B.Tech CSE",
            "semester": 3
        }
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "fullaccess@example.com",
            "password": "Test1234"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/auth/claim-full-access",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_access"] is True


def test_protected_route_without_token(client):
    """Test that protected routes require authentication."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_create_subject(client):
    """Test creating a subject (requires authentication)."""
    # Register and login
    register_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Subject Test",
            "email": "subject@example.com",
            "password": "Test1234",
            "course": "B.Tech CSE",
            "semester": 3
        }
    )
    
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "subject@example.com",
            "password": "Test1234"
        }
    )
    token = login_response.json()["access_token"]
    
    # Create subject
    response = client.post(
        "/api/subjects/",
        json={
            "name": "Database Management",
            "description": "DBMS subject"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Database Management"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])