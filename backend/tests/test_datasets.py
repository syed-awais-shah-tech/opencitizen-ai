"""Automated tests for /api/v1/datasets endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide TestClient fixture."""
    return TestClient(app)


def test_get_datasets_success(client: TestClient) -> None:
    """Ensure GET /api/v1/datasets returns 200 and valid schema structure."""
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "total" in data
    assert isinstance(data["total"], int)


def test_get_datasets_pagination(client: TestClient) -> None:
    """Ensure pagination query parameters are respected."""
    response = client.get("/api/v1/datasets?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 10


def test_get_datasets_invalid_pagination(client: TestClient) -> None:
    """Ensure invalid pagination query parameters return 422 error."""
    # limit exceeds 100
    response = client.get("/api/v1/datasets?limit=500")
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "REQUEST_VALIDATION_ERROR"
