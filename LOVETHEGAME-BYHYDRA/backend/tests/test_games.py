"""
Game Session Tests
Test game session creation, updates, and completion
"""

import pytest
from fastapi.testclient import TestClient


def test_create_game_session(client: TestClient):
    """Test creating a game session."""
    # Create user
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    # Create session
    response = client.post("/api/games/sessions", json={
        "user_id": user_id,
        "game_id": "truth-or-trust",
        "category_id": "emotional-connection"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["game_id"] == "truth-or-trust"
    assert data["category_id"] == "emotional-connection"
    assert data["completed"] is False
    assert data["score"] == 0
    assert "id" in data
    assert "timeout_at" in data


def test_create_game_session_invalid_game(client: TestClient):
    """Test creating a session with invalid game ID."""
    # Create user
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    # Try invalid game
    response = client.post("/api/games/sessions", json={
        "user_id": user_id,
        "game_id": "invalid-game",
        "category_id": "emotional-connection"
    })
    assert response.status_code == 400


def test_get_game_session(client: TestClient):
    """Test getting a game session."""
    # Create user and session
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    session_response = client.post("/api/games/sessions", json={
        "user_id": user_id,
        "game_id": "truth-or-trust",
        "category_id": "emotional-connection"
    })
    session_id = session_response.json()["id"]
    
    # Get session
    response = client.get(f"/api/games/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id


def test_update_game_session(client: TestClient):
    """Test updating game session progress."""
    # Create user and session
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    session_response = client.post("/api/games/sessions", json={
        "user_id": user_id,
        "game_id": "truth-or-trust",
        "category_id": "emotional-connection"
    })
    session_id = session_response.json()["id"]
    
    # Update session
    response = client.put(f"/api/games/sessions/{session_id}", json={
        "score": 50,
        "responses": [{"question_id": "q1", "answer": "test"}]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 50
    assert len(data["responses"]) == 1


def test_complete_game_session(client: TestClient):
    """Test completing a game session."""
    # Create user and session
    user_response = client.post("/api/users", json={
        "email": "user@test.com",
        "display_name": "Test User"
    })
    user_id = user_response.json()["id"]
    
    session_response = client.post("/api/games/sessions", json={
        "user_id": user_id,
        "game_id": "truth-or-trust",
        "category_id": "emotional-connection"
    })
    session_id = session_response.json()["id"]
    
    # Complete session
    response = client.put(f"/api/games/sessions/{session_id}", json={
        "score": 100,
        "completed": True,
        "responses": [{"question_id": "q1", "answer": "test"}]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["status"] == "completed"
    assert "completed_at" in data


def test_get_game_categories(client: TestClient):
    """Test getting game categories."""
    response = client.get("/api/games/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) > 0
    
    # Check category structure
    category = data["categories"][0]
    assert "id" in category
    assert "name" in category
    assert "games" in category


def test_get_game_registry(client: TestClient):
    """Test getting game registry."""
    response = client.get("/api/games/registry")
    assert response.status_code == 200
    data = response.json()
    assert "games" in data
    assert "total_games" in data
    assert "categories" in data
    assert data["total_games"] > 0


def test_get_game_details(client: TestClient):
    """Test getting specific game details."""
    response = client.get("/api/games/truth-or-trust")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "truth-or-trust"
    assert "name" in data
    assert "max_score" in data
    assert "category" in data


def test_get_game_details_not_found(client: TestClient):
    """Test getting non-existent game."""
    response = client.get("/api/games/nonexistent-game")
    assert response.status_code == 404
