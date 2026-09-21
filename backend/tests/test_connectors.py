"""Automated tests for Stage 17: Public-data connector abstraction, CivicOpenDataConnector,
provenance retention, DuckDB analytical integration, and extensible registry.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.analytics.engine import duckdb_engine
from app.connectors.base import BasePublicDataConnector
from app.connectors.civic_open_data import CivicOpenDataConnector
from app.connectors.exceptions import (
    ConnectorError,
    ConnectorFetchError,
    ConnectorValidationError,
)
from app.connectors.models import (
    ConnectorFetchResult,
    NormalizedDataset,
)
from app.connectors.registry import ConnectorRegistry
from app.models.dataset import Dataset


def test_base_connector_cannot_be_instantiated_directly() -> None:
    """Ensure BasePublicDataConnector enforces abstract method implementation."""
    with pytest.raises(TypeError):
        BasePublicDataConnector()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_civic_open_data_connector_ingest_csv(db_session: Session) -> None:
    """Verify end-to-end flow for public CSV dataset:

    fetch -> validate -> normalize -> record provenance -> store
    Ensures every external dataset retains:
    - source URL
    - source name
    - retrieval date
    - original format
    - processing metadata
    """
    csv_payload = (
        "department,project_name,allocated_budget,completion_rate\n"
        "Transportation,Bikeway Expansion,1200000,0.85\n"
        "Parks & Rec,Urban Greenway Trail,450000,1.00\n"
        "Public Works,Main St Stormwater Drain,2300000,0.40\n"
    ).encode("utf-8")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={
                "Content-Type": "text/csv; charset=utf-8",
                "ETag": '"abc123xyz"',
                "Last-Modified": "Mon, 21 Sep 2026 00:00:00 GMT",
            },
            content=csv_payload,
        )

    transport = httpx.MockTransport(mock_handler)
    connector = CivicOpenDataConnector(transport=transport)

    source_url = "https://data.austintexas.gov/resource/capital_projects.csv"
    source_name = "City of Austin Open Data"

    dataset_item, preview = await connector.ingest(
        source_url=source_url,
        source_name=source_name,
        db=db_session,
        category="Public Works",
        dataset_name="Austin Capital Projects 2026",
        table_name="austin_capital_projects",
    )

    # 1. Verify DatasetItem retains all provenance fields
    assert dataset_item.source_url == source_url
    assert dataset_item.source_name == source_name
    assert isinstance(dataset_item.retrieval_date, datetime)
    assert dataset_item.original_format == "CSV"
    assert isinstance(dataset_item.processing_metadata, dict)
    assert "content_sha256" in dataset_item.processing_metadata
    assert dataset_item.processing_metadata["row_count"] == 3
    assert dataset_item.processing_metadata["column_count"] == 4
    assert dataset_item.processing_metadata["header_etag"] == '"abc123xyz"'

    # 2. Verify Database entity retains provenance fields
    db_record = db_session.get(Dataset, dataset_item.id)
    assert db_record is not None
    assert db_record.source_url == source_url
    assert db_record.source_name == source_name
    assert db_record.retrieval_date is not None
    assert db_record.original_format == "CSV"
    assert db_record.processing_metadata["content_length_bytes"] == len(csv_payload)

    # 3. Verify immediate DuckDB queryability
    cols, rows, latency, scanned = duckdb_engine.execute_query(
        "SELECT department, SUM(allocated_budget) AS total_budget "
        "FROM austin_capital_projects "
        "GROUP BY department "
        "ORDER BY total_budget DESC;"
    )
    assert len(rows) == 3
    dept_totals = {r["department"]: r["total_budget"] for r in rows}
    assert dept_totals["Public Works"] == 2300000
    assert dept_totals["Transportation"] == 1200000
    assert dept_totals["Parks & Rec"] == 450000


@pytest.mark.asyncio
async def test_civic_open_data_connector_ingest_json_ckan(db_session: Session) -> None:
    """Verify ingestion and normalization of CKAN datastore format."""
    ckan_json = json.dumps({
        "help": "https://data.gov/api/3/action/datastore_search",
        "success": True,
        "result": {
            "resource_id": "res-12345",
            "records": [
                {"agency": "Health Services", "grant_amount": 75000.0, "status": "Awarded"},
                {"agency": "Youth Services", "grant_amount": 42000.0, "status": "Pending"},
                {"agency": "Senior Care", "grant_amount": 91000.0, "status": "Awarded"},
            ],
        },
    }).encode("utf-8")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=ckan_json,
        )

    transport = httpx.MockTransport(mock_handler)
    connector = CivicOpenDataConnector(transport=transport)

    source_url = "https://catalog.data.gov/api/3/action/datastore_search?resource_id=res-12345"
    source_name = "Data.gov CKAN Catalog"

    dataset_item, preview = await connector.ingest(
        source_url=source_url,
        source_name=source_name,
        db=db_session,
        category="Grants",
        dataset_name="Municipal Health Grants",
    )

    assert dataset_item.original_format == "JSON"
    assert dataset_item.source_url == source_url
    assert dataset_item.source_name == source_name
    assert dataset_item.row_count == 3
    assert dataset_item.processing_metadata["row_count"] == 3


@pytest.mark.asyncio
async def test_connector_validation_error_on_empty_payload() -> None:
    """Verify connector rejects 0-byte remote payload."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, content=b"")

    transport = httpx.MockTransport(mock_handler)
    connector = CivicOpenDataConnector(transport=transport)

    with pytest.raises(ConnectorValidationError) as exc:
        await connector.ingest(
            source_url="https://civic.data/empty.csv",
            source_name="Civic Portal",
            db=None,  # type: ignore[arg-type]
        )
    assert "empty (0 bytes)" in str(exc.value)


@pytest.mark.asyncio
async def test_connector_validation_error_on_html_response() -> None:
    """Verify connector detects and rejects HTML webpage returned instead of data."""
    html_page = b"<!DOCTYPE html><html><body><h1>404 Not Found</h1></body></html>"

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/html"},
            content=html_page,
        )

    transport = httpx.MockTransport(mock_handler)
    connector = CivicOpenDataConnector(transport=transport)

    with pytest.raises(ConnectorValidationError) as exc:
        await connector.ingest(
            source_url="https://civic.data/wrong_page",
            source_name="Civic Portal",
            db=None,  # type: ignore[arg-type]
        )
    assert "HTML webpage instead of tabular" in str(exc.value)


@pytest.mark.asyncio
async def test_connector_validation_error_on_binary_null_bytes_in_csv() -> None:
    """Verify connector rejects binary data disguised as CSV."""
    corrupted_csv = b"col1,col2\x00\x00\xffbinary_data"

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/csv"},
            content=corrupted_csv,
        )

    transport = httpx.MockTransport(mock_handler)
    connector = CivicOpenDataConnector(transport=transport)

    with pytest.raises(ConnectorValidationError) as exc:
        await connector.ingest(
            source_url="https://civic.data/corrupt.csv",
            source_name="Civic Portal",
            db=None,  # type: ignore[arg-type]
        )
    assert "Binary null bytes detected" in str(exc.value)


@pytest.mark.asyncio
async def test_connector_fetch_error_on_http_500() -> None:
    """Verify connector raises ConnectorFetchError on remote server 500 error."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, content=b"Internal Server Error")

    transport = httpx.MockTransport(mock_handler)
    connector = CivicOpenDataConnector(transport=transport)

    with pytest.raises(ConnectorFetchError) as exc:
        await connector.ingest(
            source_url="https://civic.data/server_error.csv",
            source_name="Civic Portal",
            db=None,  # type: ignore[arg-type]
        )
    assert "HTTP 500" in str(exc.value)


@pytest.mark.asyncio
async def test_connector_fetch_error_on_invalid_scheme() -> None:
    """Verify connector rejects unsafe URL schemes (file://, ftp://)."""
    connector = CivicOpenDataConnector()
    with pytest.raises(ConnectorFetchError) as exc:
        await connector.fetch(
            source_url="file:///etc/passwd",
            source_name="Local",
        )
    assert "Unsupported URL scheme 'file'" in str(exc.value)


@pytest.mark.asyncio
async def test_extensibility_custom_connector_without_modifying_system(db_session: Session) -> None:
    """Verify that future external data integrations can be implemented and registered

    cleanly without modifying the core ingestion system.
    """
    import pandas as pd

    class CustomMunicipalXmlConnector(BasePublicDataConnector):
        connector_id = "custom_municipal_xml"
        connector_name = "Custom Municipal XML Portal Connector"
        supported_formats = ["XML", "CSV"]

        async def fetch(self, source_url: str, source_name: str, **kwargs: Any) -> ConnectorFetchResult:
            simulated_xml_csv = b"council_district,rep_name,term_years\nDistrict 1,Elena Vance,4\nDistrict 2,Marcus Thorne,2\n"
            return ConnectorFetchResult(
                source_url=source_url,
                source_name=source_name,
                raw_content=simulated_xml_csv,
                content_type="text/plain",
                detected_format="CSV",
                status_code=200,
                headers={"Server": "CustomGov/2.0"},
                elapsed_ms=12.5,
            )

        def validate(self, fetch_result: ConnectorFetchResult) -> None:
            if not fetch_result.raw_content:
                raise ConnectorValidationError("Payload empty.")

        def normalize(
            self,
            fetch_result: ConnectorFetchResult,
            *,
            dataset_name: str | None = None,
            category: str = "Demographics",
            table_name: str | None = None,
            **kwargs: Any,
        ) -> NormalizedDataset:
            import io
            from app.ingestion.dataset_pipeline import dataset_pipeline

            df = pd.read_csv(io.BytesIO(fetch_result.raw_content))
            _, _, cols_meta = dataset_pipeline.infer_column_types(df)
            preview = dataset_pipeline.generate_preview(
                df=df,
                dataset_id="pending",
                name=dataset_name or "Custom Council Data",
                file_format="CSV",
            )
            provenance = self.record_provenance(fetch_result, df)
            return NormalizedDataset(
                dataframe=df,
                name=dataset_name or "Custom Council Data",
                category=category,
                table_name=table_name or "council_data",
                format="CSV",
                columns_metadata=cols_meta,
                preview=preview,
                provenance=provenance,
                raw_bytes=fetch_result.raw_content,
                size_bytes=len(fetch_result.raw_content),
            )

    registry = ConnectorRegistry()
    custom_connector = CustomMunicipalXmlConnector()
    registry.register("custom_municipal_xml", custom_connector)

    # Ingest through registered connector
    retrieved = registry.get("custom_municipal_xml")
    assert retrieved.connector_id == "custom_municipal_xml"

    item, preview = await retrieved.ingest(
        source_url="https://portal.city.gov/api/v2/council",
        source_name="City Council Registry",
        db=db_session,
    )

    assert item.source_name == "City Council Registry"
    assert item.source_url == "https://portal.city.gov/api/v2/council"
    assert item.row_count == 2


def test_api_list_connectors(client: TestClient) -> None:
    """Ensure GET /api/v1/connectors returns active connector definitions."""
    response = client.get("/api/v1/connectors")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1
    connector_ids = [c["id"] for c in data["items"]]
    assert "civic_open_data" in connector_ids


def test_api_ingest_external_dataset_success(client: TestClient) -> None:
    """Ensure POST /api/v1/connectors/ingest fetches, stores, and returns provenance."""
    csv_content = (
        "service_name,active_staff,annual_budget\n"
        "Fire & Rescue,180,14500000\n"
        "Emergency Medical,95,7800000\n"
    ).encode("utf-8")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/csv"},
            content=csv_content,
        )

    transport = httpx.MockTransport(mock_handler)
    mock_connector = CivicOpenDataConnector(transport=transport)

    with patch("app.connectors.registry.connector_registry.get", return_value=mock_connector):
        payload = {
            "source_url": "https://data.civic.gov/ems_budget.csv",
            "source_name": "Department of Public Safety",
            "category": "Expenditure",
            "dataset_name": "Emergency Services Budget",
            "connector_type": "civic_open_data",
        }
        response = client.post("/api/v1/connectors/ingest", json=payload)
        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "dataset" in data
        assert "preview" in data
        assert "provenance" in data

        # Check provenance details
        prov = data["provenance"]
        assert prov["source_url"] == payload["source_url"]
        assert prov["source_name"] == payload["source_name"]
        assert prov["original_format"] == "CSV"
        assert "content_sha256" in prov["processing_metadata"]

        # Check dataset item
        ds = data["dataset"]
        assert ds["name"] == "Emergency Services Budget"
        assert ds["source_url"] == payload["source_url"]
        assert ds["source_name"] == payload["source_name"]
        assert ds["original_format"] == "CSV"
        assert ds["row_count"] == 2
        assert ds["columns_count"] == 3


def test_api_ingest_unknown_connector_returns_400(client: TestClient) -> None:
    """Verify specifying non-existent connector type returns 400."""
    payload = {
        "source_url": "https://data.civic.gov/data.csv",
        "source_name": "Public Portal",
        "connector_type": "non_existent_connector_xyz",
    }
    response = client.post("/api/v1/connectors/ingest", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "CONNECTOR_NOT_FOUND"
