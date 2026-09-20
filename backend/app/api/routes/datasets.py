from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.errors import EntityNotFoundError
from app.db.session import get_db
from app.schemas.datasets import (
    DatasetCreate,
    DatasetItem,
    DatasetListResponse,
    DatasetPreview,
    DatasetUploadResponse,
)
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


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest structured dataset",
    description="Upload CSV, XLSX, or JSON files. Detects format, inspects schema, identifies columns, infers data types, validates records, and generates preview.",
)
async def upload_dataset(
    file: UploadFile = File(..., description="Tabular data file (CSV, XLSX, or JSON)"),
    category: str = Form(default="General", description="Civic domain category"),
    table_name: str | None = Form(default=None, description="Optional target table name"),
    db: Session = Depends(get_db),
) -> DatasetUploadResponse:
    """Ingest tabular dataset file into metadata repository and generate interactive preview."""
    content = await file.read()
    filename = file.filename or "uploaded_dataset.csv"
    dataset_item, preview = datasets_service.ingest_dataset_file(
        db=db,
        content=content,
        filename=filename,
        category=category,
        table_name=table_name,
    )
    return DatasetUploadResponse(dataset=dataset_item, preview=preview)


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


@router.get(
    "/{dataset_id}/preview",
    response_model=DatasetPreview,
    status_code=status.HTTP_200_OK,
    summary="Inspect dataset preview and schema",
    description="Returns columns, inferred types, row count, missing value counts, and sample rows.",
)
async def get_dataset_preview(
    dataset_id: str,
    db: Session = Depends(get_db),
) -> DatasetPreview:
    """Retrieve schema preview, column data types, missing counts, and sample records."""
    preview = datasets_service.get_dataset_preview(db=db, dataset_id=dataset_id)
    if not preview:
        raise EntityNotFoundError("Dataset", dataset_id)
    return preview
