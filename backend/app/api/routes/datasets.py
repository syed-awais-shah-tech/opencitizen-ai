"""API routes for tabular datasets and DuckDB tables."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.errors import EntityNotFoundError
from app.db.session import get_db
from app.schemas.datasets import DatasetCreate, DatasetItem, DatasetListResponse
from app.services.datasets_service import datasets_service

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get(
    "",
    response_model=DatasetListResponse,
    status_code=status.HTTP_200_OK,
    summary="List registered datasets",
    description="Retrieve collection of registered tabular datasets from the metadata database.",
)
async def list_datasets(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> DatasetListResponse:
    """Retrieve collection of civic datasets."""
    return datasets_service.get_datasets(db=db, limit=limit, offset=offset)


@router.post(
    "",
    response_model=DatasetItem,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new dataset",
    description="Register metadata for a civic tabular dataset in the PostgreSQL database.",
)
async def create_dataset(
    payload: DatasetCreate,
    db: Session = Depends(get_db),
) -> DatasetItem:
    """Create a new dataset entry."""
    return datasets_service.create_dataset(db=db, payload=payload)


@router.get(
    "/{dataset_id}",
    response_model=DatasetItem,
    status_code=status.HTTP_200_OK,
    summary="Get dataset by ID",
    description="Retrieve a single dataset by its unique identifier.",
)
async def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
) -> DatasetItem:
    """Retrieve dataset by ID."""
    dataset = datasets_service.get_dataset_by_id(db=db, dataset_id=dataset_id)
    if not dataset:
        raise EntityNotFoundError("Dataset", dataset_id)
    return dataset
