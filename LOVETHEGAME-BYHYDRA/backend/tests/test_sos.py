"""
SOS Crisis System Tests
Test SOS trigger, resources, and resolution
"""

import pytest
from fastapi.testclient import TestClient


def test_trigger_sos(client: TestClient):
    """Test triggering an SOS session."""
    response = client.post("/api/sos/trigger", json={
        "user_id": "user_123",
        "couple_id": "couple_456",
        "trigger": "Feeling overwhelmed",
        "severity": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert data["couple_id"] == "couple_456"
    assert data["status"] == "active"
    assert data["severity"] == 3
    assert "id" in data


def test_trigger_sos_without_couple(client: TestClient):
    """Test triggering SOS without couple ID."""
    response = client.post("/api/sos/trigger", json={
        "user_id": "user_123",
        "trigger": "Personal crisis",
        "severity": 4
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["partner_notified"] is False


def test_get_crisis_resources(client: TestClient):
    """Test getting all crisis resources."""
    response = client.get("/api/sos/resources")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "resources" in data
    assert "immediate" in data["resources"]
    assert "de_escalation_games" in data["resources"]


def test_get_crisis_resources_by_category(client: TestClient):
    """Test getting resources by category."""
    response = client.get("/api/sos/resources?category=immediate")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "immediate"
    assert "resources" in data


def test_get_crisis_resources_invalid_category(client: TestClient):
    """Test getting resources with invalid category."""
    response = client.get("/api/sos/resources?category=invalid")
    assert response.status_code == 404


def test_get_recommended_resources(client: TestClient):
    """Test getting personalized recommendations."""
    response = client.get("/api/sos/resources/recommended?user_id=user_123&severity=4")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert data["severity"] == 4
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0


def test_submit_sos_booth(client: TestClient):
    """Test submitting SOS booth response."""
    # Create SOS session
    sos_response = client.post("/api/sos/trigger", json={
        "user_id": "user_123",
        "couple_id": "couple_456",
        "severity": 3
    })
    sos_id = sos_response.json()["id"]
    
    # Submit booth response
    response = client.post(f"/api/sos/{sos_id}/booth/submit", json={
        "user_id": "user_123",
        "i_feel": "Hurt and frustrated",
        "when_partner": "When you dismiss my concerns",
        "because_i_tell_myself": "That my feelings don't matter",
        "what_i_need": "To be heard and validated"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["both_submitted"] is False


def test_resolve_sos(client: TestClient):
    """Test resolving an SOS session."""
    # Create SOS session
    sos_response = client.post("/api/sos/trigger", json={
        "user_id": "user_123",
        "couple_id": "couple_456",
        "severity": 3
    })
    sos_id = sos_response.json()["id"]
    
    # Resolve SOS
    response = client.post(f"/api/sos/{sos_id}/resolve", json={
        "user_id": "user_123",
        "resolution_notes": "Talked it through",
        "used_game": "repair-attempt",
        "feeling_better": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "resolved_at" in data


def test_escalate_sos(client: TestClient):
    """Test escalating an SOS session."""
    # Create SOS session
    sos_response = client.post("/api/sos/trigger", json={
        "user_id": "user_123",
        "couple_id": "couple_456",
        "severity": 5
    })
    sos_id = sos_response.json()["id"]
    
    # Escalate SOS
    response = client.post(f"/api/sos/{sos_id}/escalate", json={
        "user_id": "user_123",
        "reason": "Need professional help"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "escalated"
    assert "immediate_resources" in data


def test_get_sos_history(client: TestClient):
    """Test getting user SOS history."""
    # Create user and multiple SOS sessions
    user_id = "user_history_test"
    
    for i in range(3):
        client.post("/api/sos/trigger", json={
            "user_id": user_id,
            "severity": i + 1
        })
    
    # Get history
    response = client.get(f"/api/sos/user/{user_id}/history")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["total_count"] >= 3
    assert "patterns" in data
    assert "average_severity" in data["patterns"]
