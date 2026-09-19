"""Automated tests for /api/v1/query endpoint."""

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide TestClient fixture."""
    return TestClient(app)


def test_post_query_success(client: TestClient) -> None:
    """Ensure POST /api/v1/query succeeds and returns schema-compliant placeholder."""
    payload = {
        "question": "What was the total expenditure for Parks & Rec in 2023?",
        "include_citations": True,
        "include_calculations": True,
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "query_id" in data
    assert data["query_id"].startswith("qry_")
    assert data["question"] == payload["question"]
    assert "answer" in data
    assert data["is_placeholder"] is True
    assert data["status"] == "completed"
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], (int, float))

    # Citations
    assert "citations" in data
    assert len(data["citations"]) > 0
    citation = data["citations"][0]
    assert "document_title" in citation
    assert "page_number" in citation
    assert "similarity_score" in citation
    assert "excerpt" in citation

    # Calculation
    assert "calculation" in data
    assert data["calculation"] is not None
    calc = data["calculation"]
    assert "query" in calc
    assert "execution_time_ms" in calc
    assert "rows_scanned" in calc
    assert "table_name" in calc
    assert "derivation" in calc


def test_post_query_without_citations_or_calculations(client: TestClient) -> None:
    """Ensure optional retrieval flags are honored."""
    payload = {
        "question": "Can you summarize the general city council meeting?",
        "include_citations": False,
        "include_calculations": False,
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["citations"] == []
    assert data["calculation"] is None


def test_post_query_validation_too_short(client: TestClient) -> None:
    """Ensure question shorter than 3 characters is rejected with 422."""
    payload = {"question": "ab"}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "REQUEST_VALIDATION_ERROR"


def test_post_query_validation_missing_question(client: TestClient) -> None:
    """Ensure payload missing question field is rejected with 422."""
    payload = {"include_citations": True}
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "REQUEST_VALIDATION_ERROR"
