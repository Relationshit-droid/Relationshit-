"""
Couple Linking Tests
Test couple creation, joining, and management
"""

import pytest
from fastapi.testclient import TestClient


def test_create_couple(client: TestClient):
    """Test creating a couple."""
    # Create first user
    user1_response = client.post("/api/users", json={
        "email": "user1@test.com",
        "display_name": "User One"
    })
    user1_id = user1_response.json()["id"]
    
    # Create couple
    response = client.post("/api/couples/create", json={
        "user_id": user1_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user1_id"] == user1_id
    assert data["user2_id"] is None
    assert data["status"] == "pending"
    assert len(data["invite_code"]) == 6
    assert "id" in data


def test_join_couple(client: TestClient):
    """Test joining a couple with invite code."""
    # Create users
    user1_response = client.post("/api/users", json={
        "email": "user1@test.com",
        "display_name": "User One"
    })
    user1_id = user1_response.json()["id"]
    
    user2_response = client.post("/api/users", json={
        "email": "user2@test.com",
        "display_name": "User Two"
    })
    user2_id = user2_response.json()["id"]
    
    # Create couple
    couple_response = client.post("/api/couples/create", json={
        "user_id": user1_id
    })
    invite_code = couple_response.json()["invite_code"]
    
    # Join couple
    response = client.post("/api/couples/join", json={
        "user_id": user2_id,
        "invite_code": invite_code
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user1_id"] == user1_id
    assert data["user2_id"] == user2_id
    assert data["status"] == "active"


def test_join_couple_invalid_code(client: TestClient):
    """Test joining with invalid invite code."""
    # Create user
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    # Try to join with invalid code
    response = client.post("/api/couples/join", json={
        "user_id": user_id,
        "invite_code": "INVALID"
    })
    assert response.status_code == 404


def test_get_my_couple_no_couple(client: TestClient):
    """Test getting couple info when not linked."""
    # Create user
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    # Get couple info
    response = client.get(f"/api/couples/me?user_id={user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "none"
    assert data["has_couple"] is False


def test_regenerate_invite_code(client: TestClient):
    """Test regenerating invite code."""
    # Create user and couple
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    couple_response = client.post("/api/couples/create", json={
        "user_id": user_id
    })
    old_code = couple_response.json()["invite_code"]
    
    # Regenerate code
    response = client.post("/api/couples/regenerate-code", json={
        "user_id": user_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["invite_code"] != old_code
    assert len(data["invite_code"]) == 6


def test_unlink_couple(client: TestClient):
    """Test unlinking a couple."""
    # Create users and couple
    user1_response = client.post("/api/users", json={
        "email": "user1@test.com",
        "display_name": "User One"
    })
    user1_id = user1_response.json()["id"]
    
    user2_response = client.post("/api/users", json={
        "email": "user2@test.com",
        "display_name": "User Two"
    })
    user2_id = user2_response.json()["id"]
    
    couple_response = client.post("/api/couples/create", json={
        "user_id": user1_id
    })
    invite_code = couple_response.json()["invite_code"]
    
    client.post("/api/couples/join", json={
        "user_id": user2_id,
        "invite_code": invite_code
    })
    
    # Unlink couple
    response = client.post("/api/couples/unlink", json={
        "user_id": user1_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify couple is unlinked
    me_response = client.get(f"/api/couples/me?user_id={user1_id}")
    assert me_response.json()["status"] == "none"


def test_update_couple_meters(client: TestClient):
    """Test updating couple relationship meters."""
    # Create user and couple
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    couple_response = client.post("/api/couples/create", json={
        "user_id": user_id
    })
    couple_id = couple_response.json()["id"]
    
    # Update meters
    response = client.put(f"/api/couples/{couple_id}/meters", json={
        "trust_meter": 0.8,
        "romance_meter": 0.75
    })
    assert response.status_code == 200
    data = response.json()
    assert data["trust_meter"] == 0.8
    assert data["romance_meter"] == 0.75


def test_update_couple_meters_invalid_value(client: TestClient):
    """Test updating meters with invalid values."""
    # Create user and couple
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    couple_response = client.post("/api/couples/create", json={
        "user_id": user_id
    })
    couple_id = couple_response.json()["id"]
    
    # Try invalid value
    response = client.put(f"/api/couples/{couple_id}/meters", json={
        "trust_meter": 1.5  # Invalid: > 1
    })
    assert response.status_code == 400
