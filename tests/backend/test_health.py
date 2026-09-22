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


from collections.abc import Generator


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create TestClient fixture with proper lifecycle management."""
    with TestClient(app) as test_client:
        yield test_client


def test_integration_health_endpoint(client: TestClient) -> None:
    """Validate GET /health integration response."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "service" in payload
    assert "version" in payload
