"""Automated tests for /api/v1/documents endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide TestClient fixture."""
    return TestClient(app)


def test_get_documents_success(client: TestClient) -> None:
    """Ensure GET /api/v1/documents returns 200 and valid schema structure."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "total" in data
    assert isinstance(data["total"], int)


def test_get_documents_pagination(client: TestClient) -> None:
    """Ensure pagination query parameters are respected."""
    response = client.get("/api/v1/documents?limit=25&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 25


def test_get_documents_invalid_pagination(client: TestClient) -> None:
    """Ensure invalid pagination parameter (limit=0) returns 422 error."""
    response = client.get("/api/v1/documents?limit=0")
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "REQUEST_VALIDATION_ERROR"
