"""Comprehensive unit and integration tests for Stage 9 structured dataset ingestion.

Tests format detection, schema inspection, data type inference, validation,
missing-value calculation, and preview generation for CSV, XLSX, and JSON datasets.
"""

import io
import json
from datetime import date
import openpyxl
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.ingestion.dataset_pipeline import (
    DatasetIngestionPipeline,
    DatasetIngestionResult,
    dataset_pipeline,
)
from app.ingestion.exceptions import (
    DatasetValidationError,
    UnsupportedDatasetFormatError,
)
from app.schemas.datasets import DatasetPreview, DatasetUploadResponse


# ---------------------------------------------------------------------------
# Test Fixtures & Data Generators
# ---------------------------------------------------------------------------


def generate_sample_csv_bytes() -> bytes:
    """Generate representative civic expenditure CSV dataset with mixed types and nulls."""
    csv_text = (
        "department,expenditure_amount,fiscal_year,is_audited,approval_date\n"
        "Parks & Rec,4250000.50,2023,true,2023-06-15\n"
        "Transportation,8450000.00,2023,true,2023-07-01\n"
        "Public Safety,3100000.25,2023,false,2023-08-20\n"
        "Civic IT,1850000.00,2023,true,2023-09-10\n"
        "Health Services,,2023,false,2023-10-05\n"
    )
    return csv_text.encode("utf-8")


def generate_sample_xlsx_bytes() -> bytes:
    """Generate representative municipal capital projects Excel (.xlsx) file in memory."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Capital_Projects"

    # Header row
    ws.append(["project_id", "project_name", "allocated_budget", "completion_ratio", "is_active", "start_date"])

    # Data rows
    ws.append(["PRJ-001", "Downtown Bikeway Phase II", 3400000, 0.625, True, date(2023, 3, 1)])
    ws.append(["PRJ-002", "Central Library Solar Roof", 850000, 1.000, False, date(2022, 5, 15)])
    ws.append(["PRJ-003", "Main Street Stormwater Basin", 5200000, 0.410, True, date(2023, 9, 1)])
    ws.append(["PRJ-004", "Civic Center HVAC Retrofit", 1200000, None, True, date(2024, 1, 10)])

    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()


def generate_sample_json_records_bytes() -> bytes:
    """Generate representative civic vendor registry JSON dataset (array of records)."""
    data = [
        {
            "vendor_name": "Metro Asphalt Corp",
            "contract_id": "CTR-2023-142",
            "contract_value": 4800000.0,
            "department": "Transportation",
            "is_active": True,
        },
        {
            "vendor_name": "CleanGrid Solutions",
            "contract_id": "CTR-2023-205",
            "contract_value": 2100000.0,
            "department": "Sustainability",
            "is_active": True,
        },
        {
            "vendor_name": "Civic Security Systems",
            "contract_id": "CTR-2023-088",
            "contract_value": 750000.0,
            "department": "Public Safety",
            "is_active": False,
        },
        {
            "vendor_name": "Greenway Landscaping",
            "contract_id": "CTR-2023-311",
            "contract_value": None,
            "department": "Parks & Rec",
            "is_active": True,
        },
    ]
    return json.dumps(data).encode("utf-8")


def generate_sample_json_wrapped_bytes() -> bytes:
    """Generate representative civic records wrapped in an object dict."""
    payload = {
        "metadata": {"agency": "City Auditor", "version": "1.0"},
        "records": [
            {"grant_id": "GRT-101", "recipient": "Community Youth Arts", "amount": 50000, "awarded_year": 2024},
            {"grant_id": "GRT-102", "recipient": "Urban Garden Initiative", "amount": 35000, "awarded_year": 2024},
            {"grant_id": "GRT-103", "recipient": "Senior Mobility Project", "amount": 75000, "awarded_year": 2024},
        ],
    }
    return json.dumps(payload).encode("utf-8")


# ---------------------------------------------------------------------------
# Unit Tests: Format Detection & Validation
# ---------------------------------------------------------------------------


def test_detect_format_by_extension_and_content() -> None:
    """Ensure pipeline reliably detects CSV, XLSX, and JSON formats."""
    pipeline = DatasetIngestionPipeline()

    # Extension based
    assert pipeline.detect_format("budget.csv", b"a,b,c") == "CSV"
    assert pipeline.detect_format("records.tsv", b"a\tb\tc") == "CSV"
    assert pipeline.detect_format("projects.xlsx", b"some bytes") == "XLSX"
    assert pipeline.detect_format("contracts.json", b"[1, 2]") == "JSON"

    # Content sniffing
    assert pipeline.detect_format("unknown_file", b'{"data": [1, 2]}') == "JSON"
    assert pipeline.detect_format("unknown_file", b'[{"id": 1}]') == "JSON"
    assert pipeline.detect_format("unknown_file", b"PK\x03\x04ziparchive") == "XLSX"
    assert pipeline.detect_format("unknown_file", b"col1,col2,col3\n1,2,3\n") == "CSV"


def test_detect_format_unsupported_error() -> None:
    """Ensure unsupported file formats raise UnsupportedDatasetFormatError."""
    pipeline = DatasetIngestionPipeline()

    with pytest.raises(UnsupportedDatasetFormatError) as exc_info:
        pipeline.detect_format("document.pdf", b"%PDF-1.4 binary content")
    assert "Unsupported dataset format" in str(exc_info.value)


def test_empty_content_validation_error() -> None:
    """Ensure 0-byte upload raises DatasetValidationError."""
    pipeline = DatasetIngestionPipeline()

    with pytest.raises(DatasetValidationError) as exc_info:
        pipeline.load_dataframe(b"", "CSV")
    assert "empty" in str(exc_info.value).lower()


def test_empty_dataframe_validation_error() -> None:
    """Ensure dataframe with 0 rows or columns raises DatasetValidationError."""
    pipeline = DatasetIngestionPipeline()
    empty_df = pd.DataFrame()

    with pytest.raises(DatasetValidationError) as exc_info:
        pipeline.validate_dataset(empty_df)
    assert "empty" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Unit Tests: Pipeline Processing & Schema Inspection
# ---------------------------------------------------------------------------


def test_ingest_csv_pipeline_success() -> None:
    """Ensure CSV ingestion detects schema, infers types, and computes missing counts."""
    content = generate_sample_csv_bytes()
    result = dataset_pipeline.process_bytes(
        content=content,
        filename="dept_expenses_2023.csv",
        category="Expenditure",
    )

    assert isinstance(result, DatasetIngestionResult)
    assert result.format == "CSV"
    assert result.row_count == 5
    assert result.columns_count == 5
    assert result.category == "Expenditure"
    assert result.table_name.startswith("dept_expenses_2023_")

    # Inferred types
    types = result.preview.inferred_types
    assert types["department"] == "VARCHAR"
    assert types["expenditure_amount"] == "DOUBLE"
    assert types["fiscal_year"] == "INTEGER"
    assert types["is_audited"] == "BOOLEAN"
    assert types["approval_date"] == "DATE"

    # Missing counts
    missing = result.preview.missing_value_counts
    assert missing["expenditure_amount"] == 1
    assert missing["department"] == 0
    assert missing["fiscal_year"] == 0

    # Preview sample rows
    samples = result.preview.sample_rows
    assert len(samples) == 5
    # Check NaN was converted to None
    assert samples[4]["expenditure_amount"] is None
    assert samples[0]["department"] == "Parks & Rec"
    assert samples[0]["is_audited"] is True


def test_ingest_xlsx_pipeline_success() -> None:
    """Ensure Excel XLSX ingestion detects schema, infers types, and generates preview."""
    content = generate_sample_xlsx_bytes()
    result = dataset_pipeline.process_bytes(
        content=content,
        filename="capital_projects_2024.xlsx",
        category="Public Works",
    )

    assert isinstance(result, DatasetIngestionResult)
    assert result.format == "XLSX"
    assert result.row_count == 4
    assert result.columns_count == 6

    # Inferred types
    types = result.preview.inferred_types
    assert types["project_id"] == "VARCHAR"
    assert types["project_name"] == "VARCHAR"
    assert types["allocated_budget"] == "INTEGER"
    assert types["completion_ratio"] == "DOUBLE"
    assert types["is_active"] == "BOOLEAN"
    assert types["start_date"] == "DATE"

    # Missing counts
    missing = result.preview.missing_value_counts
    assert missing["completion_ratio"] == 1
    assert missing["project_id"] == 0

    # Sample rows verification
    samples = result.preview.sample_rows
    assert len(samples) == 4
    assert samples[0]["project_name"] == "Downtown Bikeway Phase II"
    assert samples[3]["completion_ratio"] is None


def test_ingest_json_records_pipeline_success() -> None:
    """Ensure JSON records ingestion detects schema, infers types, and generates preview."""
    content = generate_sample_json_records_bytes()
    result = dataset_pipeline.process_bytes(
        content=content,
        filename="vendor_contracts.json",
        category="Procurement",
    )

    assert isinstance(result, DatasetIngestionResult)
    assert result.format == "JSON"
    assert result.row_count == 4
    assert result.columns_count == 5

    types = result.preview.inferred_types
    assert types["vendor_name"] == "VARCHAR"
    assert types["contract_value"] == "DOUBLE"
    assert types["is_active"] == "BOOLEAN"

    missing = result.preview.missing_value_counts
    assert missing["contract_value"] == 1
    assert missing["vendor_name"] == 0

    samples = result.preview.sample_rows
    assert len(samples) == 4
    assert samples[0]["vendor_name"] == "Metro Asphalt Corp"
    assert samples[3]["contract_value"] is None


def test_ingest_json_wrapped_records_pipeline_success() -> None:
    """Ensure JSON with wrapped 'records' key is handled transparently."""
    content = generate_sample_json_wrapped_bytes()
    result = dataset_pipeline.process_bytes(
        content=content,
        filename="civic_grants.json",
        category="Grants",
    )

    assert isinstance(result, DatasetIngestionResult)
    assert result.format == "JSON"
    assert result.row_count == 3
    assert result.columns_count == 4
    assert "grant_id" in result.preview.columns
    assert result.preview.inferred_types["amount"] == "INTEGER"


# ---------------------------------------------------------------------------
# Integration Tests: FastAPI Endpoints (/api/v1/datasets/upload & preview)
# ---------------------------------------------------------------------------


def test_api_upload_csv_dataset(client: TestClient) -> None:
    """Test POST /api/v1/datasets/upload with CSV file and inspect response and preview."""
    content = generate_sample_csv_bytes()
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("city_expenses.csv", content, "text/csv")},
        data={"category": "Expenditure"},
    )
    assert response.status_code == 201
    data = response.json()

    assert "dataset" in data
    assert "preview" in data

    ds = data["dataset"]
    assert ds["id"].startswith("ds_")
    assert ds["name"] == "city_expenses.csv"
    assert ds["format"] == "CSV"
    assert ds["row_count"] == 5
    assert ds["columns_count"] == 5
    assert ds["status"] == "ready"

    preview = data["preview"]
    assert preview["dataset_id"] == ds["id"]
    assert preview["row_count"] == 5
    assert "department" in preview["columns"]
    assert preview["inferred_types"]["fiscal_year"] == "INTEGER"
    assert preview["missing_value_counts"]["expenditure_amount"] == 1
    assert len(preview["sample_rows"]) == 5

    # Test GET /{dataset_id}/preview
    preview_res = client.get(f"/api/v1/datasets/{ds['id']}/preview")
    assert preview_res.status_code == 200
    pdata = preview_res.json()
    assert pdata["dataset_id"] == ds["id"]
    assert pdata["row_count"] == 5
    assert len(pdata["sample_rows"]) == 5


def test_api_upload_xlsx_dataset(client: TestClient) -> None:
    """Test POST /api/v1/datasets/upload with XLSX file."""
    content = generate_sample_xlsx_bytes()
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("capital_projects.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"category": "Public Works"},
    )
    assert response.status_code == 201
    data = response.json()

    ds = data["dataset"]
    assert ds["format"] == "XLSX"
    assert ds["row_count"] == 4
    assert ds["columns_count"] == 6

    preview = data["preview"]
    assert preview["inferred_types"]["allocated_budget"] == "INTEGER"
    assert len(preview["sample_rows"]) == 4


def test_api_upload_json_dataset(client: TestClient) -> None:
    """Test POST /api/v1/datasets/upload with JSON file."""
    content = generate_sample_json_records_bytes()
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("vendors.json", content, "application/json")},
        data={"category": "Procurement"},
    )
    assert response.status_code == 201
    data = response.json()

    ds = data["dataset"]
    assert ds["format"] == "JSON"
    assert ds["row_count"] == 4

    preview = data["preview"]
    assert "vendor_name" in preview["columns"]


def test_api_upload_unsupported_format(client: TestClient) -> None:
    """Test POST /api/v1/datasets/upload with unsupported file returns 400."""
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("image.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "UNSUPPORTED_DATASET_FORMAT"


def test_api_get_preview_not_found(client: TestClient) -> None:
    """Test GET /api/v1/datasets/{non_existent_id}/preview returns 404."""
    response = client.get("/api/v1/datasets/non_existent_ds_id/preview")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"
