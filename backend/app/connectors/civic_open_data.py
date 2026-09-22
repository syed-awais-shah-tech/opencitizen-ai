"""Civic Open Data Connector for municipal portals, Data.gov resources, and civic APIs.

Supports public CSV and JSON tabular data endpoints.
"""

from __future__ import annotations

import io
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any
from pathlib import Path
from urllib.parse import urlparse

import httpx
import numpy as np
import pandas as pd

from app.connectors.base import BasePublicDataConnector
from app.connectors.exceptions import (
    ConnectorFetchError,
    ConnectorNormalizationError,
    ConnectorValidationError,
)
from app.connectors.models import (
    ConnectorFetchResult,
    NormalizedDataset,
)
from app.core.security import DEFAULT_MAX_UPLOAD_SIZE_BYTES
from app.ingestion.dataset_pipeline import dataset_pipeline

logger = logging.getLogger(__name__)

USER_AGENT = "OpenCitizen-AI/1.0 (Public Data Connector; Civic Intelligence Engine)"


class CivicOpenDataConnector(BasePublicDataConnector):
    """First-party connector for retrieving tabular data from public open data portals.

    Capable of fetching and parsing:
    - CSV endpoints from municipal open data sites (e.g. data.gov, Socrata CSV exports, CKAN resource downloads)
    - JSON endpoints containing arrays of records or tabular wrappers (e.g. SODA API, CKAN datastore queries)
    """

    connector_id: str = "civic_open_data"
    connector_name: str = "Civic Open Data Connector"
    description: str = "Pulls public municipal datasets from open-data portals and civic APIs (CSV, JSON)"
    supported_formats: list[str] = ["CSV", "JSON"]

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        max_bytes: int = DEFAULT_MAX_UPLOAD_SIZE_BYTES,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__()
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes
        self._transport = transport

    # -------------------------------------------------------------------------
    # 1. FETCH
    # -------------------------------------------------------------------------
    async def fetch(
        self,
        source_url: str,
        source_name: str,
        **kwargs: Any,
    ) -> ConnectorFetchResult:
        """Fetch remote civic dataset over HTTP/HTTPS with audit timing and header capture."""
        parsed_url = urlparse(source_url.strip())
        if parsed_url.scheme not in ("http", "https"):
            raise ConnectorFetchError(
                f"Unsupported URL scheme '{parsed_url.scheme}'. Only 'http' and 'https' are supported."
            )
        if not parsed_url.netloc:
            raise ConnectorFetchError(f"Invalid URL '{source_url}': Missing domain or hostname.")

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/csv, application/json, text/plain, */*",
        }
        custom_headers = kwargs.get("headers")
        if isinstance(custom_headers, dict):
            headers.update(custom_headers)

        start_time = time.perf_counter()
        retrieval_date = datetime.now(timezone.utc)

        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=self.timeout_seconds,
                follow_redirects=True,
            ) as client:
                response = await client.get(source_url, headers=headers)

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            content = response.content
            content_type = response.headers.get("content-type", "").lower()

            # Detect format based on content-type or URL extension
            detected_format = self._detect_format(
                content=content,
                content_type=content_type,
                url_path=parsed_url.path,
            )

            # Check HTTP status
            if response.status_code >= 400:
                raise ConnectorFetchError(
                    f"Remote server returned HTTP {response.status_code} for URL '{source_url}'.",
                    status_code=502 if response.status_code >= 500 else 400,
                )

            return ConnectorFetchResult(
                source_url=source_url,
                source_name=source_name,
                raw_content=content,
                content_type=content_type,
                detected_format=detected_format,
                status_code=response.status_code,
                headers=dict(response.headers),
                elapsed_ms=elapsed_ms,
                retrieval_date=retrieval_date,
            )

        except httpx.TimeoutException as exc:
            raise ConnectorFetchError(
                f"Timed out after {self.timeout_seconds}s fetching dataset from '{source_url}'."
            ) from exc
        except httpx.RequestError as exc:
            raise ConnectorFetchError(
                f"Network transport error connecting to '{source_url}': {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # 2. VALIDATE
    # -------------------------------------------------------------------------
    def validate(self, fetch_result: ConnectorFetchResult) -> None:
        """Enforce size, signature, and structural integrity boundaries."""
        content = fetch_result.raw_content

        # Size checks
        if not content or len(content) == 0:
            raise ConnectorValidationError("External public dataset is empty (0 bytes).")
        if len(content) > self.max_bytes:
            max_mb = self.max_bytes / (1024 * 1024)
            size_mb = len(content) / (1024 * 1024)
            raise ConnectorValidationError(
                f"External dataset size ({size_mb:.2f} MB) exceeds maximum permitted limit of {max_mb:.2f} MB."
            )

        # Check for HTML responses (e.g. 404/login portals returned with 200 OK)
        sample = content[:1024].strip().lower()
        if sample.startswith(b"<!doctype html") or sample.startswith(b"<html"):
            raise ConnectorValidationError(
                "Remote URL returned an HTML webpage instead of tabular CSV or JSON data."
            )

        # Format-specific validations
        fmt = fetch_result.detected_format
        if fmt == "CSV":
            if b"\x00" in content[:4096]:
                raise ConnectorValidationError("Binary null bytes detected in external CSV stream.")
        elif fmt == "JSON":
            stripped = content.strip()
            if not (stripped.startswith(b"{") or stripped.startswith(b"[")):
                raise ConnectorValidationError("External JSON response does not have a valid array or object root.")
            try:
                parsed = json.loads(content.decode("utf-8"))
                if not isinstance(parsed, (list, dict)):
                    raise ConnectorValidationError("External JSON root must be a list of records or dictionary.")
            except Exception as exc:
                raise ConnectorValidationError(f"Invalid JSON payload: {exc}") from exc
        else:
            raise ConnectorValidationError(
                f"Unsupported format '{fmt}'. CivicOpenDataConnector only supports CSV and JSON."
            )

    # -------------------------------------------------------------------------
    # 3. NORMALIZE
    # -------------------------------------------------------------------------
    def normalize(
        self,
        fetch_result: ConnectorFetchResult,
        *,
        dataset_name: str | None = None,
        category: str = "Public Data",
        table_name: str | None = None,
        **kwargs: Any,
    ) -> NormalizedDataset:
        """Parse raw content into canonical pandas DataFrame with standardized schema and types."""
        fmt = fetch_result.detected_format
        content = fetch_result.raw_content
        transformations: list[str] = []

        try:
            if fmt == "CSV":
                df = self._load_csv(content)
                transformations.append("parsed_csv")
            elif fmt == "JSON":
                df = self._load_json(content)
                transformations.append("parsed_json_tabular")
            else:
                raise ConnectorNormalizationError(f"Cannot normalize unrecognized format '{fmt}'.")
        except Exception as exc:
            raise ConnectorNormalizationError(f"Failed to parse tabular data: {exc}") from exc

        if df.empty or len(df.columns) == 0:
            raise ConnectorNormalizationError("Normalized dataset contains no tabular rows or columns.")

        # Header normalization: alphanumeric and underscores only
        df, header_transform = self._normalize_headers(df)
        transformations.append(header_transform)

        # Cell normalization: trim strings, normalize missing values
        df, cell_transform = self._normalize_cells(df)
        transformations.append(cell_transform)

        # Infer column types and schema metadata
        inferred_types, missing_counts, columns_metadata = dataset_pipeline.infer_column_types(df)
        transformations.append("inferred_column_types")

        # Resolve dataset name and table name
        name = dataset_name or self._derive_dataset_name(fetch_result)
        safe_table_name = table_name or self.generate_table_name(fetch_result.source_name, fetch_result.source_url)

        # Assemble preview
        sample_rows = dataset_pipeline.extract_sample_rows(df, max_rows=5)
        preview = dataset_pipeline.generate_preview(
            df=df,
            dataset_id="pending",
            name=name,
            file_format=fmt,
            max_sample_rows=5,
        )

        provenance = self.record_provenance(
            fetch_result=fetch_result,
            normalized_df=df,
            transformations=transformations,
        )

        return NormalizedDataset(
            dataframe=df,
            name=name,
            category=category,
            table_name=safe_table_name,
            format=fmt,
            columns_metadata=columns_metadata,
            preview=preview,
            provenance=provenance,
            raw_bytes=content,
            size_bytes=len(content),
        )

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    def _detect_format(self, content: bytes, content_type: str, url_path: str) -> str:
        """Heuristically identify whether data is CSV or JSON."""
        path_lower = url_path.lower()
        if path_lower.endswith(".csv") or "text/csv" in content_type:
            return "CSV"
        if path_lower.endswith(".json") or "application/json" in content_type:
            return "JSON"

        # Content inspection
        stripped = content.strip()
        if stripped.startswith(b"{") or stripped.startswith(b"["):
            return "JSON"
        if b"," in stripped[:1024] or b"\n" in stripped[:1024]:
            return "CSV"

        return "CSV"

    def _load_csv(self, content: bytes) -> pd.DataFrame:
        """Load CSV content handling multiple text encodings."""
        buffer = io.BytesIO(content)
        for enc in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
            try:
                buffer.seek(0)
                return pd.read_csv(buffer, encoding=enc)
            except UnicodeDecodeError:
                continue
        buffer.seek(0)
        return pd.read_csv(buffer, encoding="utf-8", errors="replace")

    def _load_json(self, content: bytes) -> pd.DataFrame:
        """Extract DataFrame from JSON, supporting flat arrays, CKAN datastore, and Socrata SODA."""
        text = content.decode("utf-8")
        parsed = json.loads(text)

        if isinstance(parsed, list):
            return pd.DataFrame(parsed)

        if isinstance(parsed, dict):
            # CKAN format: {"result": {"records": [...]}}
            if "result" in parsed and isinstance(parsed["result"], dict) and "records" in parsed["result"]:
                return pd.DataFrame(parsed["result"]["records"])

            # Socrata or generic wrappers: {"data": [...]}, {"records": [...]}, {"rows": [...]}
            for key in ("data", "records", "rows", "items", "results"):
                if key in parsed and isinstance(parsed[key], list):
                    return pd.DataFrame(parsed[key])

            # Fallback for pandas json
            return pd.read_json(io.StringIO(text))

        raise ConnectorNormalizationError("JSON root must be an array of records or tabular container object.")

    def _normalize_headers(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        """Convert headers to safe alphanumeric SQL identifiers."""
        cleaned_columns: list[str] = []
        seen: dict[str, int] = {}

        for idx, col in enumerate(df.columns):
            raw = str(col).strip()
            # Replace spaces and punctuation with underscores
            clean = re.sub(r"[^a-zA-Z0-9_]", "_", raw).strip("_").lower()
            if not clean or not clean[0].isalpha():
                clean = f"col_{clean or idx + 1}"
            clean = clean[:60]

            if clean in seen:
                seen[clean] += 1
                clean = f"{clean}_{seen[clean]}"
            else:
                seen[clean] = 0

            cleaned_columns.append(clean)

        df.columns = cleaned_columns
        return df, "normalized_column_identifiers"

    def _normalize_cells(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        """Trim string cells and standardize null sentinels."""
        null_sentinels = {"", "n/a", "na", "null", "none", "nan", "-"}
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                # Strip string whitespace
                df[col] = df[col].apply(
                    lambda v: v.strip() if isinstance(v, str) else v
                )
                # Map null sentinels
                df[col] = df[col].apply(
                    lambda v: np.nan if isinstance(v, str) and v.lower() in null_sentinels else v
                )
        return df, "trimmed_cells_standardized_nulls"

    def _derive_dataset_name(self, fetch_result: ConnectorFetchResult) -> str:
        """Produce user-friendly dataset title from URL or source name."""
        stem = Path(urlparse(fetch_result.source_url).path).stem
        if stem and stem != "/":
            return f"{fetch_result.source_name} - {stem.replace('_', ' ').replace('-', ' ').title()}"
        return f"{fetch_result.source_name} Dataset"
