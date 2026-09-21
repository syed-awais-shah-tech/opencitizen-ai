"""Pydantic schemas for tabular datasets and DuckDB tables."""

from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field


class DatasetColumnSchema(BaseModel):
    """Schema definition for an individual column in a registered dataset."""

    name: str = Field(..., description="Column identifier")
    type: Literal["VARCHAR", "DOUBLE", "INTEGER", "DATE", "BOOLEAN"] = Field(
        ..., description="Inferred DuckDB SQL column type"
    )
    missing_count: int = Field(
        default=0, ge=0, description="Count of null or missing values in column"
    )
    null_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Percentage of missing values in column"
    )


class DatasetCreate(BaseModel):
    """Payload for registering a new civic dataset."""

    name: str = Field(..., min_length=1, max_length=255, description="File or dataset name")
    category: str = Field(default="General", description="Civic domain category")
    format: Literal["CSV", "XLSX", "JSON", "PARQUET"] = Field(
        default="CSV", description="Source tabular file format"
    )
    row_count: int = Field(default=0, ge=0, description="Total number of rows")
    columns_count: int = Field(default=0, ge=0, description="Total number of columns")
    table_name: str = Field(
        ..., min_length=1, max_length=100, description="Target DuckDB in-memory table identifier"
    )
    size_bytes: int = Field(default=0, ge=0, description="Filesystem size in bytes")
    columns: list[DatasetColumnSchema] = Field(
        default_factory=list, description="List of columns and inferred types"
    )


class DatasetItem(BaseModel):
    """Schema representing an individual registered civic dataset."""

    id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="File or dataset name")
    category: str = Field(..., description="Civic domain category")
    format: Literal["CSV", "XLSX", "JSON", "PARQUET"] = Field(
        ..., description="Source tabular file format"
    )
    row_count: int = Field(default=0, description="Total number of rows")
    columns_count: int = Field(default=0, description="Total number of columns")
    table_name: str = Field(..., description="Target DuckDB in-memory table identifier")
    status: Literal["active", "registered", "processing", "ready"] = Field(
        default="registered", description="Lifecycle state"
    )
    size_bytes: int = Field(default=0, description="Filesystem size in bytes")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Registration timestamp"
    )
    columns: list[DatasetColumnSchema] = Field(
        default_factory=list, description="List of columns and inferred types"
    )
    # Provenance fields for external public-data sources (Stage 17)
    source_url: str | None = Field(
        default=None, description="External origin URL if ingested via connector"
    )
    source_name: str | None = Field(
        default=None, description="Public data portal or agency name"
    )
    retrieval_date: datetime | None = Field(
        default=None, description="Timestamp when data was retrieved from external source"
    )
    original_format: str | None = Field(
        default=None, description="Original external format before normalization"
    )
    processing_metadata: dict[str, Any] | None = Field(
        default=None, description="Audit and normalization processing metadata"
    )


class DatasetProvenance(BaseModel):
    """Provenance tracking record for external public-data sources."""

    source_url: str = Field(..., description="External source URL where dataset was retrieved")
    source_name: str = Field(..., description="Name of external publisher, portal, or agency")
    retrieval_date: datetime = Field(..., description="Timestamp when data was fetched")
    original_format: str = Field(..., description="Original format of data before normalization")
    processing_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Audit metadata including HTTP status, checksums, transformation steps",
    )


class IngestExternalDatasetRequest(BaseModel):
    """Payload for importing an external public data resource via connector."""

    source_url: str = Field(..., min_length=5, description="Public data source URL (HTTP/HTTPS)")
    source_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the public data source / agency"
    )
    category: str = Field(default="Public Data", description="Civic domain category")
    dataset_name: str | None = Field(
        default=None, description="Optional custom name for dataset"
    )
    table_name: str | None = Field(
        default=None, description="Optional target table identifier"
    )
    connector_type: str = Field(
        default="civic_open_data", description="Identifier of the connector to use"
    )


class IngestExternalDatasetResponse(BaseModel):
    """Response payload returned when an external public dataset is ingested."""

    dataset: DatasetItem = Field(..., description="Persisted dataset metadata record")
    preview: DatasetPreview = Field(
        ..., description="Interactive schema inspection and preview"
    )
    provenance: DatasetProvenance = Field(
        ..., description="Retained source provenance and processing audit metadata"
    )


class ConnectorInfo(BaseModel):
    """Information regarding an available public-data connector."""

    id: str = Field(..., description="Connector identifier (e.g. civic_open_data)")
    name: str = Field(..., description="Human-readable connector name")
    description: str = Field(..., description="Capabilities and data formats supported")
    supported_formats: list[str] = Field(..., description="List of supported source formats")
    enabled: bool = Field(default=True, description="Whether connector is active")


class ConnectorListResponse(BaseModel):
    """Response payload listing registered external public data connectors."""

    items: list[ConnectorInfo] = Field(..., description="Available connectors")
    total: int = Field(..., description="Total count of available connectors")


class DatasetPreview(BaseModel):
    """Dataset preview payload containing schema, inferred types, missing counts, and sample rows."""

    dataset_id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Dataset name")
    format: str = Field(..., description="Detected tabular file format (CSV, XLSX, JSON)")
    row_count: int = Field(..., ge=0, description="Total number of rows")
    columns_count: int = Field(..., ge=0, description="Total number of columns")
    columns: list[str] = Field(..., description="List of column names")
    inferred_types: dict[str, str] = Field(
        ..., description="Mapping of column names to inferred SQL/DuckDB types"
    )
    missing_value_counts: dict[str, int] = Field(
        ..., description="Mapping of column names to count of null/missing values"
    )
    sample_rows: list[dict[str, Any]] = Field(
        default_factory=list, description="Sample rows (top records from dataset)"
    )


class DatasetUploadResponse(BaseModel):
    """Response payload returned when a structured dataset is ingested."""

    dataset: DatasetItem = Field(..., description="Persisted dataset metadata record")
    preview: DatasetPreview = Field(
        ..., description="Interactive schema inspection and preview"
    )


class DatasetListResponse(BaseModel):
    """Response payload for listing civic tabular datasets."""

    items: list[DatasetItem] = Field(
        default_factory=list, description="Collection of registered datasets"
    )
    total: int = Field(default=0, description="Total count of datasets registered")
