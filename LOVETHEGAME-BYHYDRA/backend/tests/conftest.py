"""
Pytest Configuration and Fixtures
Shared test fixtures for backend testing
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Import the app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "display_name": "Test User"
    }


@pytest.fixture
def sample_couple():
    """Sample couple data for testing."""
    return {
        "user1_id": "user_123",
        "user2_id": "user_456"
    }


@pytest.fixture
def sample_game_session():
    """Sample game session data for testing."""
    return {
        "user_id": "user_123",
        "game_id": "truth-or-trust",
        "category_id": "emotional-connection"
    }


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
