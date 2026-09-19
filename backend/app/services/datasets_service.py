"""Service layer for civic tabular datasets database operations."""

import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.schemas.datasets import DatasetColumnSchema, DatasetCreate, DatasetItem, DatasetListResponse


class DatasetsService:
    """Service handling dataset registration, retrieval, and schema metadata in PostgreSQL."""

    def get_datasets(
        self, db: Session, limit: int = 50, offset: int = 0
    ) -> DatasetListResponse:
        """Retrieve paginated collection of registered datasets from the database."""
        total_stmt = select(func.count()).select_from(Dataset)
        total = db.scalar(total_stmt) or 0

        stmt = (
            select(Dataset)
            .order_by(Dataset.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        datasets = db.scalars(stmt).all()

        items = [
            DatasetItem(
                id=ds.id,
                name=ds.name,
                category=ds.category,
                format=ds.format,  # type: ignore[arg-type]
                row_count=ds.row_count,
                columns_count=ds.columns_count,
                table_name=ds.table_name,
                status=ds.status,  # type: ignore[arg-type]
                size_bytes=0,
                created_at=ds.created_at,
                columns=[
                    DatasetColumnSchema(name=c["name"], type=c["type"])
                    for c in (ds.columns_metadata or [])
                ],
            )
            for ds in datasets
        ]

        return DatasetListResponse(items=items, total=total)

    def get_dataset_by_id(self, db: Session, dataset_id: str) -> DatasetItem | None:
        """Retrieve single dataset by ID."""
        ds = db.get(Dataset, dataset_id)
        if not ds:
            return None
        return DatasetItem(
            id=ds.id,
            name=ds.name,
            category=ds.category,
            format=ds.format,  # type: ignore[arg-type]
            row_count=ds.row_count,
            columns_count=ds.columns_count,
            table_name=ds.table_name,
            status=ds.status,  # type: ignore[arg-type]
            size_bytes=0,
            created_at=ds.created_at,
            columns=[
                DatasetColumnSchema(name=c["name"], type=c["type"])
                for c in (ds.columns_metadata or [])
            ],
        )

    def create_dataset(self, db: Session, payload: DatasetCreate) -> DatasetItem:
        """Register new dataset metadata in the database."""
        dataset = Dataset(
            id=f"ds_{uuid.uuid4().hex[:12]}",
            name=payload.name,
            category=payload.category,
            format=payload.format,
            row_count=payload.row_count,
            columns_count=payload.columns_count,
            table_name=payload.table_name,
            status="registered",
            columns_metadata=[c.model_dump() for c in payload.columns],
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return DatasetItem(
            id=dataset.id,
            name=dataset.name,
            category=dataset.category,
            format=dataset.format,  # type: ignore[arg-type]
            row_count=dataset.row_count,
            columns_count=dataset.columns_count,
            table_name=dataset.table_name,
            status=dataset.status,  # type: ignore[arg-type]
            size_bytes=payload.size_bytes,
            created_at=dataset.created_at,
            columns=payload.columns,
        )


datasets_service = DatasetsService()
