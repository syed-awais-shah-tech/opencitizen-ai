"""API routes for external public-data connectors and automated dataset ingestion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.connectors.registry import get_connector_registry
from app.db.session import get_db
from app.schemas.datasets import (
    ConnectorListResponse,
    DatasetProvenance,
    IngestExternalDatasetRequest,
    IngestExternalDatasetResponse,
)

router = APIRouter(prefix="/connectors", tags=["Connectors"])


@router.get(
    "",
    response_model=ConnectorListResponse,
    status_code=status.HTTP_200_OK,
    summary="List registered public data connectors",
    description="Retrieve available public data connectors, supported formats, and active capabilities.",
)
async def list_connectors() -> ConnectorListResponse:
    """List available external public data connectors."""
    registry = get_connector_registry()
    items = registry.list_connectors()
    return ConnectorListResponse(items=items, total=len(items))


@router.post(
    "/ingest",
    response_model=IngestExternalDatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest external public dataset via connector",
    description="Fetch, validate, normalize, record provenance, and persist a civic dataset from an external open-data source.",
)
async def ingest_external_dataset(
    payload: IngestExternalDatasetRequest,
    db: Session = Depends(get_db),
) -> IngestExternalDatasetResponse:
    """Execute end-to-end ingestion from external public data source retaining provenance."""
    registry = get_connector_registry()
    connector = registry.get(payload.connector_type)

    dataset_item, preview = await connector.ingest(
        source_url=payload.source_url,
        source_name=payload.source_name,
        db=db,
        category=payload.category,
        dataset_name=payload.dataset_name,
        table_name=payload.table_name,
    )

    provenance = DatasetProvenance(
        source_url=dataset_item.source_url or payload.source_url,
        source_name=dataset_item.source_name or payload.source_name,
        retrieval_date=dataset_item.retrieval_date or dataset_item.created_at,
        original_format=dataset_item.original_format or dataset_item.format,
        processing_metadata=dataset_item.processing_metadata or {},
    )

    return IngestExternalDatasetResponse(
        dataset=dataset_item,
        preview=preview,
        provenance=provenance,
    )
