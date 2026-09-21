"""Base connector abstraction for external public-data sources.

Implements the template pipeline:
fetch → validate → normalize → record provenance → store

Every external dataset retains:
- source URL
- source name
- retrieval date
- original format
- processing metadata
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.engine import duckdb_engine
from app.connectors.exceptions import ConnectorValidationError
from app.connectors.models import (
    ConnectorFetchResult,
    ConnectorProvenance,
    NormalizedDataset,
)
from app.ingestion.dataset_pipeline import dataset_pipeline
from app.models.dataset import Dataset
from app.schemas.datasets import (
    DatasetColumnSchema,
    DatasetItem,
    DatasetPreview,
)

logger = logging.getLogger(__name__)

DEFAULT_CONNECTOR_STORAGE_DIR = Path("storage/datasets")


class BasePublicDataConnector(ABC):
    """Abstract base class defining the contract for all external public-data connectors.

    Future integrations (e.g. CKAN, Socrata, US Census, OpenDataSoft, Eurostat)
    extend this class by providing source-specific fetch, validate, and normalize logic
    while inheriting standardized provenance tracking and storage integration.
    """

    connector_id: str = "base_connector"
    connector_name: str = "Base Public Data Connector"
    description: str = "Abstract base connector for external public tabular datasets"
    supported_formats: list[str] = ["CSV", "JSON"]

    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or DEFAULT_CONNECTOR_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Core Pipeline Step 1: FETCH
    # -------------------------------------------------------------------------
    @abstractmethod
    async def fetch(
        self,
        source_url: str,
        source_name: str,
        **kwargs: Any,
    ) -> ConnectorFetchResult:
        """Retrieve raw payload and transport headers from the external data source.

        Args:
            source_url: Target resource URL or API endpoint.
            source_name: Publisher or portal identifier.
            kwargs: Connector-specific parameters (e.g. auth headers, query params, pagination).

        Returns:
            ConnectorFetchResult with raw bytes and network metadata.
        """
        ...

    # -------------------------------------------------------------------------
    # Core Pipeline Step 2: VALIDATE
    # -------------------------------------------------------------------------
    @abstractmethod
    def validate(self, fetch_result: ConnectorFetchResult) -> None:
        """Validate fetched data structure, byte signatures, status codes, and security limits.

        Raises:
            ConnectorValidationError: If data is corrupted, empty, oversized, or non-tabular.
        """
        ...

    # -------------------------------------------------------------------------
    # Core Pipeline Step 3: NORMALIZE
    # -------------------------------------------------------------------------
    @abstractmethod
    def normalize(
        self,
        fetch_result: ConnectorFetchResult,
        *,
        dataset_name: str | None = None,
        category: str = "Public Data",
        table_name: str | None = None,
        **kwargs: Any,
    ) -> NormalizedDataset:
        """Transform source-specific raw records or tables into canonical Pandas DataFrame.

        Standardizes:
        - Column headers into clean alphanumeric identifiers
        - Cell string trimming and sentinel null values
        - Inferred SQL/DuckDB data types
        """
        ...

    # -------------------------------------------------------------------------
    # Core Pipeline Step 4: RECORD PROVENANCE
    # -------------------------------------------------------------------------
    def record_provenance(
        self,
        fetch_result: ConnectorFetchResult,
        normalized_df: pd.DataFrame,
        transformations: list[str] | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> ConnectorProvenance:
        """Assemble comprehensive provenance tracking information.

        Mandatory fields:
        - source URL
        - source name
        - retrieval date
        - original format
        - processing metadata (checksum, size, timing, transformations)
        """
        content_hash = hashlib.sha256(fetch_result.raw_content).hexdigest()
        meta: dict[str, Any] = {
            "content_sha256": content_hash,
            "content_length_bytes": len(fetch_result.raw_content),
            "http_status_code": fetch_result.status_code,
            "content_type": fetch_result.content_type,
            "fetch_elapsed_ms": fetch_result.elapsed_ms,
            "retrieved_at": fetch_result.retrieval_date.isoformat(),
            "connector_id": self.connector_id,
            "row_count": len(normalized_df),
            "column_count": len(normalized_df.columns),
            "columns": list(normalized_df.columns),
            "transformations": transformations or ["standard_normalization"],
        }

        # Include standard HTTP cache headers if present
        for h in ("etag", "last-modified", "server", "cache-control"):
            if h in fetch_result.headers:
                meta[f"header_{h.replace('-', '_')}"] = fetch_result.headers[h]

        if extra_metadata:
            meta.update(extra_metadata)

        return ConnectorProvenance(
            source_url=fetch_result.source_url,
            source_name=fetch_result.source_name,
            retrieval_date=fetch_result.retrieval_date,
            original_format=fetch_result.detected_format,
            processing_metadata=meta,
        )

    # -------------------------------------------------------------------------
    # Core Pipeline Step 5: STORE
    # -------------------------------------------------------------------------
    def store(
        self,
        normalized: NormalizedDataset,
        db: Session,
    ) -> tuple[DatasetItem, DatasetPreview]:
        """Persist normalized dataset to disk storage, PostgreSQL database, and DuckDB engine.

        Guarantees:
        - Filesystem persistence under storage/datasets/{dataset_id}/
        - Metadata record in PostgreSQL with all 5 provenance attributes
        - Immediate table/view registration in DuckDB for SQL analytics
        """
        dataset_id = f"ds_{uuid.uuid4().hex[:12]}"
        safe_table_name = normalized.table_name

        # 1. Persist metadata record with provenance in PostgreSQL
        dataset = Dataset(
            id=dataset_id,
            name=normalized.name,
            category=normalized.category,
            format=normalized.format,
            row_count=len(normalized.dataframe),
            columns_count=len(normalized.dataframe.columns),
            table_name=safe_table_name,
            status="ready",
            columns_metadata=[c.model_dump() for c in normalized.columns_metadata],
            source_url=normalized.provenance.source_url,
            source_name=normalized.provenance.source_name,
            retrieval_date=normalized.provenance.retrieval_date,
            original_format=normalized.provenance.original_format,
            processing_metadata=normalized.provenance.processing_metadata,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        # 2. Write raw file and cached preview to storage
        ds_dir = self.storage_dir / dataset.id
        ds_dir.mkdir(parents=True, exist_ok=True)

        file_ext = normalized.format.lower()
        file_path = ds_dir / f"data.{file_ext}"
        file_path.write_bytes(normalized.raw_bytes)

        # Also write preview
        preview_payload = normalized.preview
        preview_payload.dataset_id = dataset.id
        preview_path = ds_dir / "preview.json"
        preview_path.write_text(preview_payload.model_dump_json(indent=2), encoding="utf-8")

        # 3. Register table directly in DuckDB analytical engine
        try:
            duckdb_engine.register_dataframe(table_name=safe_table_name, df=normalized.dataframe)
            logger.info("Registered external dataset table '%s' in DuckDB engine.", safe_table_name)
        except Exception as err:
            logger.warning("Failed to register table '%s' into DuckDB engine: %s", safe_table_name, err)

        # 4. Construct response schemas
        dataset_item = DatasetItem(
            id=dataset.id,
            name=dataset.name,
            category=dataset.category,
            format=dataset.format,  # type: ignore[arg-type]
            row_count=dataset.row_count,
            columns_count=dataset.columns_count,
            table_name=dataset.table_name,
            status="ready",
            size_bytes=normalized.size_bytes,
            created_at=dataset.created_at,
            columns=normalized.columns_metadata,
            source_url=dataset.source_url,
            source_name=dataset.source_name,
            retrieval_date=dataset.retrieval_date,
            original_format=dataset.original_format,
            processing_metadata=dataset.processing_metadata,
        )

        return dataset_item, preview_payload

    # -------------------------------------------------------------------------
    # Template Method: INGEST
    # -------------------------------------------------------------------------
    async def ingest(
        self,
        source_url: str,
        source_name: str,
        db: Session,
        *,
        category: str = "Public Data",
        dataset_name: str | None = None,
        table_name: str | None = None,
        **kwargs: Any,
    ) -> tuple[DatasetItem, DatasetPreview]:
        """Execute the complete connector lifecycle:

        fetch → validate → normalize → record provenance → store
        """
        logger.info(
            "Starting ingestion for external dataset from '%s' via connector '%s'",
            source_url,
            self.connector_id,
        )

        # Step 1: Fetch
        fetch_result = await self.fetch(source_url=source_url, source_name=source_name, **kwargs)

        # Step 2: Validate
        self.validate(fetch_result)

        # Step 3: Normalize
        normalized = self.normalize(
            fetch_result,
            dataset_name=dataset_name,
            category=category,
            table_name=table_name,
            **kwargs,
        )

        # Step 4: Record Provenance
        provenance = self.record_provenance(fetch_result, normalized.dataframe)
        normalized.provenance = provenance

        # Step 5: Store
        return self.store(normalized, db=db)

    # -------------------------------------------------------------------------
    # Shared Helper Utilities
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_table_name(source_name: str, source_url: str) -> str:
        """Derive safe SQL table identifier from source name and URL."""
        base = f"{source_name}_{Path(source_url).stem}"
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", base.lower()).strip("_")
        if not clean or not clean[0].isalpha():
            clean = f"table_{clean}"
        suffix = uuid.uuid4().hex[:6]
        return f"{clean}_{suffix}"[:63]
