"""Integration tests for backend health check endpoints."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Create TestClient fixture."""
    return TestClient(app)


def test_integration_health_endpoint(client: TestClient) -> None:
    """Validate GET /health integration response."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "service" in payload
    assert "version" in payload
