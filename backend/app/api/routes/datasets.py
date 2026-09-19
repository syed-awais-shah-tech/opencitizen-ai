"""API routes for tabular datasets and DuckDB tables."""

from fastapi import APIRouter, Query, status
from app.schemas.datasets import DatasetListResponse
from app.services.datasets_service import datasets_service

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get(
    "",
    response_model=DatasetListResponse,
    status_code=status.HTTP_200_OK,
    summary="List registered datasets",
    description="Retrieve the collection of registered tabular datasets (CSV/Parquet) available for DuckDB SQL analytics.",
)
async def list_datasets(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> DatasetListResponse:
    """Retrieve collection of civic datasets."""
    return datasets_service.get_datasets(limit=limit, offset=offset)
