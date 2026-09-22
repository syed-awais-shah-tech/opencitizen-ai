# Extending Connectors: Adding External Public Data Sources

OpenCitizen AI provides a pluggable connector architecture designed to ingest civic and public-data feeds from municipal portals, government open-data APIs, and statistical bureaus.

This guide explains how to build, register, and test a new external connector.

---

## 1. Architectural Pipeline

All connectors inherit from `BasePublicDataConnector` in `backend/app/connectors/base.py` and implement the 5-step lifecycle:

```
┌─────────┐      ┌──────────┐      ┌───────────┐      ┌───────────────────┐      ┌─────────┐
│  FETCH  │ ───► │ VALIDATE │ ───► │ NORMALIZE │ ───► │ RECORD PROVENANCE │ ───► │  STORE  │
└─────────┘      └──────────┘      └───────────┘      └───────────────────┘      └─────────┘
```

1. **`fetch`**: Retrieves the raw HTTP payload or API stream from the source URL.
2. **`validate`**: Verifies HTTP status, magic bytes, file extensions, and size limits.
3. **`normalize`**: Converts source-specific rows into a canonical `pandas.DataFrame` and extracts typed column metadata.
4. **`record_provenance`**: Automatically computes SHA-256 hash, HTTP headers, timestamps, and transformation steps.
5. **`store`**: Persists file to storage, creates PostgreSQL metadata record, and registers an in-memory SQL table in DuckDB.

---

## 2. Invariant Requirements for Connectors

Every ingested external dataset must retain:
- `source_url`: Full URI of the external data resource.
- `source_name`: Human-readable publisher name (e.g. "City of Austin Open Data Portal").
- `retrieval_date`: UTC ISO timestamp of retrieval.
- `original_format`: Format detected at download (e.g. `CSV`, `JSON`, `XLSX`).
- `processing_metadata`: SHA-256 checksum, content length, transformations, HTTP headers.

---

## 3. Step-by-Step Implementation Example

Let's implement a new connector for a fictional municipal API or CKAN portal: `CKANDataConnector`.

### Step 3.1: Create Connector Class

Create a new file `backend/app/connectors/ckan.py`:

```python
"""CKAN open data portal connector."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd

from app.connectors.base import BasePublicDataConnector
from app.connectors.exceptions import ConnectorFetchError, ConnectorValidationError
from app.connectors.models import ConnectorFetchResult, NormalizedDataset
from app.schemas.datasets import DatasetColumnSchema, DatasetPreview


class CKANDataConnector(BasePublicDataConnector):
    """Connector for CKAN-powered open data portals (e.g., data.gov, open.canada.ca)."""

    connector_id: str = "ckan"
    connector_name: str = "CKAN Open Data Portal"
    description: str = "Ingests tabular datasets from CKAN package and resource endpoints"
    supported_formats: list[str] = ["CSV", "JSON"]

    async def fetch(
        self,
        source_url: str,
        source_name: str,
        **kwargs: Any,
    ) -> ConnectorFetchResult:
        """Fetch resource from CKAN endpoint."""
        start_time = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(source_url)
                resp.raise_for_status()
                raw_bytes = resp.content
        except Exception as exc:
            raise ConnectorFetchError(f"Failed to fetch CKAN resource: {exc}") from exc

        elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0

        return ConnectorFetchResult(
            source_url=source_url,
            source_name=source_name,
            raw_content=raw_bytes,
            status_code=resp.status_code,
            content_type=resp.headers.get("content-type", "application/octet-stream"),
            headers=dict(resp.headers),
            retrieval_date=datetime.now(timezone.utc),
            detected_format="CSV" if "csv" in source_url.lower() else "JSON",
            elapsed_ms=elapsed_ms,
        )

    def validate(self, fetch_result: ConnectorFetchResult) -> None:
        """Validate payload size, non-empty content, and binary signatures."""
        if not fetch_result.raw_content:
            raise ConnectorValidationError("Fetched CKAN resource is empty (0 bytes).")
        if len(fetch_result.raw_content) > 50 * 1024 * 1024:
            raise ConnectorValidationError("Resource exceeds maximum 50 MB threshold.")

    def normalize(
        self,
        fetch_result: ConnectorFetchResult,
        *,
        dataset_name: str | None = None,
        category: str = "Public Data",
        table_name: str | None = None,
        **kwargs: Any,
    ) -> NormalizedDataset:
        """Transform CSV/JSON payload into canonical DataFrame and preview metadata."""
        if fetch_result.detected_format == "CSV":
            df = pd.read_csv(io.BytesIO(fetch_result.raw_content))
        else:
            df = pd.read_json(io.BytesIO(fetch_result.raw_content))

        # Clean column names
        df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]

        columns_metadata = [
            DatasetColumnSchema(
                name=col,
                data_type=str(dtype),
                nullable=bool(df[col].isna().any()),
            )
            for col, dtype in zip(df.columns, df.dtypes)
        ]

        safe_table = table_name or self.generate_table_name(
            fetch_result.source_name, fetch_result.source_url
        )

        preview = DatasetPreview(
            dataset_id="preview",
            name=dataset_name or fetch_result.source_name,
            format=fetch_result.detected_format,
            row_count=len(df),
            columns_count=len(df.columns),
            columns=list(df.columns),
            inferred_types={c.name: c.data_type for c in columns_metadata},
            missing_value_counts={c: int(df[c].isna().sum()) for c in df.columns},
            sample_rows=df.head(5).to_dict(orient="records"),
        )

        return NormalizedDataset(
            name=dataset_name or fetch_result.source_name,
            category=category,
            format=fetch_result.detected_format,
            dataframe=df,
            raw_bytes=fetch_result.raw_content,
            size_bytes=len(fetch_result.raw_content),
            table_name=safe_table,
            columns_metadata=columns_metadata,
            preview=preview,
        )
```

---

### Step 3.2: Register the Connector

In `backend/app/connectors/registry.py`:

```python
from app.connectors.ckan import CKANDataConnector

connector_registry.register(CKANDataConnector())
```

Once registered, the connector is automatically discovered by:
- `GET /api/v1/connectors`
- `POST /api/v1/connectors/ingest` with `{"connector_type": "ckan", ...}`

---

### Step 3.3: Write Unit & Integration Tests

Add tests in `backend/tests/test_connectors.py`:
- Test successful fetch, validate, and normalize with mock HTTP responses.
- Test error handling when payload is corrupted or oversized.
- Verify provenance metadata contains `source_url`, `source_name`, `retrieval_date`, `original_format`, and `processing_metadata`.
- Verify the table registers in DuckDB and can be queried.
