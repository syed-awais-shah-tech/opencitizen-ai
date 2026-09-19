"""Automated tests for /api/v1/datasets endpoints."""

from fastapi.testclient import TestClient


def test_get_datasets_success(client: TestClient) -> None:
    """Ensure GET /api/v1/datasets returns 200 and valid schema structure."""
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "total" in data
    assert isinstance(data["total"], int)


def test_create_and_get_dataset(client: TestClient) -> None:
    """Ensure POST /api/v1/datasets creates a record and GET /{id} retrieves it."""
    payload = {
        "name": "vendor_contracts_2024.xlsx",
        "category": "Procurement",
        "format": "XLSX",
        "row_count": 3840,
        "columns_count": 2,
        "table_name": "vendor_contracts_2024",
        "size_bytes": 1800000,
        "columns": [
            {"name": "vendor_name", "type": "VARCHAR"},
            {"name": "contract_amount", "type": "DOUBLE"},
        ],
    }
    create_res = client.post("/api/v1/datasets", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"].startswith("ds_")
    assert created_data["table_name"] == "vendor_contracts_2024"

    # Fetch by ID
    get_res = client.get(f"/api/v1/datasets/{created_data['id']}")
    assert get_res.status_code == 200
    retrieved_data = get_res.json()
    assert retrieved_data["name"] == "vendor_contracts_2024.xlsx"
    assert len(retrieved_data["columns"]) == 2

    # Listing reflects created dataset
    list_res = client.get("/api/v1/datasets")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


def test_get_dataset_not_found(client: TestClient) -> None:
    """Ensure non-existent dataset ID returns 404."""
    response = client.get("/api/v1/datasets/non-existent-ds-id")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"


def test_get_datasets_pagination(client: TestClient) -> None:
    """Ensure pagination query parameters are respected."""
    response = client.get("/api/v1/datasets?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 10


def test_get_datasets_invalid_pagination(client: TestClient) -> None:
    """Ensure invalid pagination query parameters return 422 error."""
    response = client.get("/api/v1/datasets?limit=500")
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "REQUEST_VALIDATION_ERROR"
