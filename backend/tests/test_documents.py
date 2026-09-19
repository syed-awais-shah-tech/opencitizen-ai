"""Automated tests for /api/v1/documents endpoints."""

from fastapi.testclient import TestClient


def test_get_documents_success(client: TestClient) -> None:
    """Ensure GET /api/v1/documents returns 200 and valid schema structure."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "total" in data
    assert isinstance(data["total"], int)


def test_create_and_get_document(client: TestClient) -> None:
    """Ensure POST /api/v1/documents creates a record and GET /{id} retrieves it."""
    payload = {
        "title": "Clean_Energy_Transition_Strategy_2025.pdf",
        "department": "Sustainability Office",
        "category": "Environment",
        "page_count": 65,
        "chunk_count": 145,
        "size_bytes": 5800000,
        "summary": "Municipal solar rooftop array targets and energy benchmarking.",
    }
    create_res = client.post("/api/v1/documents", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"].startswith("doc_")
    assert created_data["title"] == "Clean_Energy_Transition_Strategy_2025.pdf"

    # Fetch by ID
    get_res = client.get(f"/api/v1/documents/{created_data['id']}")
    assert get_res.status_code == 200
    retrieved_data = get_res.json()
    assert retrieved_data["department"] == "Sustainability Office"
    assert retrieved_data["page_count"] == 65

    # Listing reflects created document
    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


def test_get_document_not_found(client: TestClient) -> None:
    """Ensure non-existent document ID returns 404."""
    response = client.get("/api/v1/documents/non-existent-doc-id")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"


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
