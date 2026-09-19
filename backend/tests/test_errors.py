"""Automated tests for error handlers and domain exceptions."""

from fastapi.testclient import TestClient
import pytest

from app.core.errors import EntityNotFoundError, ValidationException
from app.main import app





def test_404_not_found_handling(client: TestClient) -> None:
    """Ensure accessing an unregistered route triggers 404 handler."""
    response = client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "HTTP_ERROR"


def test_custom_domain_exceptions() -> None:
    """Ensure custom domain exceptions format messages properly."""
    not_found = EntityNotFoundError("Dataset", "ds-123")
    assert not_found.status_code == 404
    assert not_found.error_code == "NOT_FOUND"
    assert "ds-123" in not_found.message

    val_err = ValidationException("Invalid filter format", details={"field": "category"})
    assert val_err.status_code == 422
    assert val_err.error_code == "VALIDATION_ERROR"
    assert val_err.details == {"field": "category"}
