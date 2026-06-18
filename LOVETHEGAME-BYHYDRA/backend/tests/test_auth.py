"""
Authentication Tests
Test user creation, authentication, and token validation
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "firebase" in data


def test_create_user(client: TestClient, sample_user):
    """Test user creation."""
    response = client.post("/api/users", json=sample_user)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == sample_user["email"]
    assert data["display_name"] == sample_user["display_name"]
    assert "id" in data
    assert "couple_code" in data
    assert data["sarcasm_level"] == 1
    assert data["points"] == 0


def test_create_user_invalid_email(client: TestClient):
    """Test user creation with invalid email."""
    response = client.post("/api/users", json={
        "email": "invalid-email",
        "display_name": "Test"
    })
    assert response.status_code == 422


def test_get_user(client: TestClient, sample_user):
    """Test getting a user by ID."""
    # First create a user
    create_response = client.post("/api/users", json=sample_user)
    user_id = create_response.json()["id"]
    
    # Then get the user
    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == sample_user["email"]


def test_get_user_not_found(client: TestClient):
    """Test getting a non-existent user."""
    response = client.get("/api/users/nonexistent-id")
    assert response.status_code == 404


def test_update_user(client: TestClient, sample_user):
    """Test updating a user."""
    # Create user
    create_response = client.post("/api/users", json=sample_user)
    user_id = create_response.json()["id"]
    
    # Update user
    response = client.put(f"/api/users/{user_id}", json={
        "display_name": "Updated Name",
        "sarcasm_level": 2
    })
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"


def test_update_sarcasm_level(client: TestClient, sample_user):
    """Test updating sarcasm level."""
    # Create user
    create_response = client.post("/api/users", json=sample_user)
    user_id = create_response.json()["id"]
    
    # Update sarcasm level
    response = client.put(f"/api/users/{user_id}/sarcasm?level=3")
    assert response.status_code == 200
    data = response.json()
    assert data["sarcasm_level"] == 3
    assert data["name"] == "Radical Truth Wizard"


def test_update_sarcasm_level_invalid(client: TestClient, sample_user):
    """Test updating sarcasm level with invalid value."""
    # Create user
    create_response = client.post("/api/users", json=sample_user)
    user_id = create_response.json()["id"]
    
    # Try invalid level
    response = client.put(f"/api/users/{user_id}/sarcasm?level=5")
    assert response.status_code == 400
