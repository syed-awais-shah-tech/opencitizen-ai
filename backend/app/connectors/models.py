"""Data structures and representations for public-data connectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.schemas.datasets import DatasetColumnSchema, DatasetPreview


@dataclass
class ConnectorProvenance:
    """Provenance audit metadata retained for every external dataset.

    Required fields:
    - source_url: External location/endpoint
    - source_name: Origin publisher or portal name
    - retrieval_date: Timestamp of retrieval
    - original_format: Raw format prior to normalization (CSV, JSON, SODA, CKAN, etc.)
    - processing_metadata: Checksums, HTTP headers, normalization logs, row counts
    """

    source_url: str
    source_name: str
    retrieval_date: datetime
    original_format: str
    processing_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert provenance record to JSON-serializable dictionary."""
        return {
            "source_url": self.source_url,
            "source_name": self.source_name,
            "retrieval_date": self.retrieval_date.isoformat(),
            "original_format": self.original_format,
            "processing_metadata": self.processing_metadata,
        }


@dataclass
class ConnectorFetchResult:
    """Raw payload and network transport metadata from an external data source."""

    source_url: str
    source_name: str
    raw_content: bytes
    content_type: str
    detected_format: str
    status_code: int
    headers: dict[str, str]
    elapsed_ms: float
    retrieval_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedDataset:
    """Standardized tabular dataset ready for persistence and analytical registration."""

    dataframe: pd.DataFrame
    name: str
    category: str
    table_name: str
    format: str
    columns_metadata: list[DatasetColumnSchema]
    preview: DatasetPreview
    provenance: ConnectorProvenance
    raw_bytes: bytes
    size_bytes: int
