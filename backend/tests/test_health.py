"""Automated tests for FastAPI health and discovery endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient fixture for endpoint requests."""
    return TestClient(app)


def test_root_endpoint(client: TestClient) -> None:
    """Ensure root discovery endpoint responds with 200 and docs links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs_url" in data
    assert data["health_url"] == "/health"


def test_health_check_endpoint(client: TestClient) -> None:
    """Ensure GET /health returns 200 and valid healthy status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data


def test_api_v1_health_check_endpoint(client: TestClient) -> None:
    """Ensure GET /api/v1/health is also accessible and healthy."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
