"""Automated tests for /api/v1/query endpoint."""

from fastapi.testclient import TestClient


def test_post_query_success(client: TestClient) -> None:
    """Ensure POST /api/v1/query succeeds and returns schema-compliant grounded RAG answer."""
    from app.ingestion.models import DocumentChunk
    from app.search.dependencies import get_vector_search_service

    v_svc = get_vector_search_service()
    v_svc.index_chunks(
        [
            DocumentChunk(
                chunk_id="chk_parks_01",
                document_id="doc_parks",
                source_filename="City_Budget_Parks.pdf",
                page_number=14,
                chunk_index=0,
                text="Section 3.2 - Parks, Recreation & Community Facilities: Authorized operational allocation for fiscal year 2023 was adjusted to $4,250,000.",
                character_count=138,
                word_count=19,
                metadata={"department": "Parks & Rec"},
            )
        ]
    )

    payload = {
        "question": "What was the total expenditure for Parks & Rec in 2023?",
        "include_citations": True,
        "include_calculations": False,
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "query_id" in data
    assert data["query_id"].startswith("qry_")
    assert data["question"] == payload["question"]
    assert "answer" in data
    assert data["status"] == "completed"
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], (int, float))

    # Citations
    assert "citations" in data
    assert len(data["citations"]) > 0
    citation = data["citations"][0]
    assert citation["document_title"] == "City_Budget_Parks.pdf"
    assert citation["page_number"] == 14
    assert citation["chunk_id"] == "chk_parks_01"
    assert "similarity_score" in citation
    assert "excerpt" in citation


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
