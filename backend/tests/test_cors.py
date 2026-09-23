"""Automated tests verifying CORS configuration and preflight handling for local frontend origins."""

import io
from fastapi.testclient import TestClient
import pytest

from app.core.config import Settings, settings
from app.main import create_application
from tests.pdf_helpers import create_test_pdf


@pytest.fixture
def client():
    """Create test client with CORS-configured FastAPI instance."""
    app = create_application()
    return TestClient(app, raise_server_exceptions=False)


def test_cors_origins_settings_parsing():
    """Test that Settings correctly parses lists, JSON strings, and comma-separated strings."""
    # List of strings
    s1 = Settings(CORS_ORIGINS=["http://localhost:3000", "http://custom-host:3000"])
    assert "http://localhost:3000" in s1.CORS_ORIGINS
    assert "http://127.0.0.1:3000" in s1.CORS_ORIGINS
    assert "http://custom-host:3000" in s1.CORS_ORIGINS

    # JSON formatted list string
    s2 = Settings(CORS_ORIGINS='["http://localhost:3000", "http://staging.civic.gov"]')
    assert "http://localhost:3000" in s2.CORS_ORIGINS
    assert "http://staging.civic.gov" in s2.CORS_ORIGINS

    # Comma-separated string
    s3 = Settings(CORS_ORIGINS="http://localhost:3000, http://production.civic.gov")
    assert "http://localhost:3000" in s3.CORS_ORIGINS
    assert "http://production.civic.gov" in s3.CORS_ORIGINS


def test_cors_options_preflight_localhost_3000(client):
    """Test that OPTIONS preflight request from http://localhost:3000 receives correct headers."""
    response = client.options(
        "/api/v1/documents/upload",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert "content-type" in response.headers.get("access-control-allow-headers", "").lower()


def test_cors_options_preflight_127_0_0_1_3000(client):
    """Test that OPTIONS preflight request from http://127.0.0.1:3000 receives correct headers."""
    response = client.options(
        "/api/v1/documents/upload",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin(client):
    """Test that an untrusted origin does not receive Access-Control-Allow-Origin."""
    response = client.options(
        "/api/v1/documents/upload",
        headers={
            "Origin": "http://malicious-external-site.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.headers.get("access-control-allow-origin") is None


def test_cors_upload_post_success(client):
    """Test document upload endpoint returns CORS headers on successful request."""
    pdf_bytes = create_test_pdf(["Page 1: Civic municipal procurement report."])
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Origin": "http://localhost:3000"},
        files={"file": ("civic_report.pdf", pdf_bytes, "application/pdf")},
        data={"department": "Public Works", "category": "Report", "sync": "false"},
    )

    assert response.status_code == 201
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"
    data = response.json()
    assert "job_id" in data
    assert data["document"]["title"] == "civic_report.pdf"


def test_cors_upload_post_validation_error(client):
    """Test that 422 validation errors retain CORS headers for the frontend origin."""
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 422
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_health_get_request(client):
    """Test standard GET endpoint returns CORS headers."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"
