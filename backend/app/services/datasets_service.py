import json
import os
import uuid
from pathlib import Path
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingestion.dataset_pipeline import dataset_pipeline
from app.models.dataset import Dataset
from app.schemas.datasets import (
    DatasetColumnSchema,
    DatasetCreate,
    DatasetItem,
    DatasetListResponse,
    DatasetPreview,
)

DATASETS_STORAGE_DIR = Path("storage/datasets")


class DatasetsService:
    """Service handling dataset registration, retrieval, schema metadata, and file ingestion in PostgreSQL."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or DATASETS_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

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
                    DatasetColumnSchema(
                        name=c["name"],
                        type=c["type"],
                        missing_count=c.get("missing_count", 0),
                        null_percentage=c.get("null_percentage", 0.0),
                    )
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
                DatasetColumnSchema(
                    name=c["name"],
                    type=c["type"],
                    missing_count=c.get("missing_count", 0),
                    null_percentage=c.get("null_percentage", 0.0),
                )
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

    def ingest_dataset_file(
        self,
        db: Session,
        content: bytes,
        filename: str,
        category: str = "General",
        table_name: str | None = None,
    ) -> tuple[DatasetItem, DatasetPreview]:
        """Execute ingestion pipeline: detect format, inspect schema, infer types, validate, and persist."""
        result = dataset_pipeline.process_bytes(
            content=content,
            filename=filename,
            category=category,
            table_name=table_name,
        )

        # Persist metadata to database
        dataset = Dataset(
            id=result.dataset_id,
            name=result.name,
            category=result.category,
            format=result.format,
            row_count=result.row_count,
            columns_count=result.columns_count,
            table_name=result.table_name,
            status="ready",
            columns_metadata=[c.model_dump() for c in result.columns_metadata],
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        # Persist raw file and cached preview to storage
        ds_dir = self.storage_dir / dataset.id
        ds_dir.mkdir(parents=True, exist_ok=True)

        file_ext = result.format.lower()
        file_path = ds_dir / f"data.{file_ext}"
        file_path.write_bytes(content)

        preview_path = ds_dir / "preview.json"
        preview_path.write_text(result.preview.model_dump_json(indent=2), encoding="utf-8")

        dataset_item = DatasetItem(
            id=dataset.id,
            name=dataset.name,
            category=dataset.category,
            format=dataset.format,  # type: ignore[arg-type]
            row_count=dataset.row_count,
            columns_count=dataset.columns_count,
            table_name=dataset.table_name,
            status="ready",
            size_bytes=result.size_bytes,
            created_at=dataset.created_at,
            columns=result.columns_metadata,
        )

        return dataset_item, result.preview

    def get_dataset_preview(self, db: Session, dataset_id: str) -> DatasetPreview | None:
        """Retrieve cached or computed preview showing columns, inferred types, missing counts, and sample rows."""
        ds = db.get(Dataset, dataset_id)
        if not ds:
            return None

        preview_path = self.storage_dir / dataset_id / "preview.json"
        if preview_path.exists():
            try:
                data = json.loads(preview_path.read_text(encoding="utf-8"))
                return DatasetPreview(**data)
            except Exception:
                pass

        # Reconstruct preview from metadata if preview.json is absent
        cols = [c["name"] for c in (ds.columns_metadata or [])]
        inferred = {c["name"]: c["type"] for c in (ds.columns_metadata or [])}
        missing = {c["name"]: c.get("missing_count", 0) for c in (ds.columns_metadata or [])}

        return DatasetPreview(
            dataset_id=ds.id,
            name=ds.name,
            format=ds.format,
            row_count=ds.row_count,
            columns_count=ds.columns_count,
            columns=cols,
            inferred_types=inferred,
            missing_value_counts=missing,
            sample_rows=[],
        )


datasets_service = DatasetsService()
