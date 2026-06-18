"""
Leaderboard Tests
Test leaderboard retrieval and ranking
"""

import pytest
from fastapi.testclient import TestClient


def test_get_global_leaderboard(client: TestClient):
    """Test getting global leaderboard."""
    response = client.get("/api/leaderboards/global")
    assert response.status_code == 200
    data = response.json()
    assert "leaderboard" in data
    assert "total_entries" in data
    assert "time_period" in data
    assert isinstance(data["leaderboard"], list)


def test_get_global_leaderboard_pagination(client: TestClient):
    """Test leaderboard pagination."""
    response = client.get("/api/leaderboards/global?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["leaderboard"]) <= 10


def test_get_global_leaderboard_time_periods(client: TestClient):
    """Test different time periods."""
    for period in ["all_time", "weekly", "monthly"]:
        response = client.get(f"/api/leaderboards/global?time_period={period}")
        assert response.status_code == 200
        data = response.json()
        assert data["time_period"] == period


def test_get_global_leaderboard_invalid_params(client: TestClient):
    """Test invalid query parameters."""
    response = client.get("/api/leaderboards/global?limit=1000")
    assert response.status_code == 200  # Should cap at max
    
    response = client.get("/api/leaderboards/global?time_period=invalid")
    assert response.status_code == 400


def test_get_couple_ranking(client: TestClient):
    """Test getting specific couple ranking."""
    response = client.get("/api/leaderboards/couples/couple_123/ranking")
    assert response.status_code == 200
    data = response.json()
    assert "couple" in data
    assert "nearby_competitors" in data
    assert "percentile" in data
    assert "total_participants" in data


def test_get_friends_leaderboard(client: TestClient):
    """Test getting friends leaderboard."""
    response = client.get("/api/leaderboards/friends/user_123")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert "leaderboard" in data
    assert "your_rank" in data
    assert isinstance(data["leaderboard"], list)


def test_get_category_leaderboard(client: TestClient):
    """Test getting category-specific leaderboard."""
    response = client.get("/api/leaderboards/categories/emotional-connection")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "emotional-connection"
    assert "leaderboard" in data
    assert "category_stats" in data


def test_get_category_leaderboard_invalid(client: TestClient):
    """Test getting leaderboard for invalid category."""
    response = client.get("/api/leaderboards/categories/invalid-category")
    assert response.status_code == 404


def test_get_achievement_leaderboard(client: TestClient):
    """Test getting achievement leaderboard."""
    response = client.get("/api/leaderboards/achievements")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "achievements"
    assert "leaderboard" in data
    assert "total_achievements_available" in data
    assert "rarest_achievements" in data


def test_get_streak_leaderboard(client: TestClient):
    """Test getting streak leaderboard."""
    response = client.get("/api/leaderboards/streaks")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "streaks"
    assert "leaderboard" in data
    assert "longest_streak_ever" in data
    assert "streak_milestones" in data


def test_get_newcomer_leaderboard(client: TestClient):
    """Test getting newcomer leaderboard."""
    response = client.get("/api/leaderboards/newcomers")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "newcomers"
    assert "leaderboard" in data


def test_refresh_leaderboard_cache(client: TestClient):
    """Test refreshing leaderboard cache."""
    response = client.post("/api/leaderboards/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cached_boards" in data
    assert "refreshed_at" in data


def test_get_leaderboard_stats(client: TestClient):
    """Test getting leaderboard statistics."""
    response = client.get("/api/leaderboards/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_couples" in data
    assert "total_games_played" in data
    assert "growth" in data
