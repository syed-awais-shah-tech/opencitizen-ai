"""API routes for municipal documents, vector chunks, background ingestion jobs, and status polling."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.errors import EntityNotFoundError
from app.core.security import sanitize_filename, validate_entity_id, validate_file_upload
from app.db.session import get_db
from app.models.document import Document
from app.models.ingestion_job import IngestionJob
from app.schemas.documents import (
    DocumentCreate,
    DocumentItem,
    DocumentListResponse,
    UploadDocumentResponse,
)
from app.schemas.jobs import DocumentStatusResponse, IngestionJobResponse
from app.services.documents_service import documents_service
from app.services.ingestion_worker import ingestion_worker

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List ingested documents",
    description="Retrieve collection of ingested municipal PDF documents from the metadata database.",
)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    """Retrieve collection of ingested municipal documents."""
    return documents_service.get_documents(db=db, limit=limit, offset=offset)


@router.post(
    "",
    response_model=DocumentItem,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new document",
    description="Register metadata for an ingested municipal PDF document in the PostgreSQL database.",
)
async def create_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
) -> DocumentItem:
    """Create a new document entry."""
    return documents_service.create_document(db=db, payload=payload)


@router.post(
    "/upload",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a PDF document",
    description="Upload a municipal PDF document. Creates a background processing job for extraction, chunking, embedding, and vector storage.",
)
async def upload_document(
    file: UploadFile = File(..., description="User-uploaded PDF document"),
    department: str = Form(default="General", description="Issuing municipal department"),
    category: str = Form(default="Report", description="Document category"),
    summary: str = Form(default="", description="Optional executive summary"),
    sync: bool = Form(
        default=False,
        description="If True, process synchronously before returning (useful for CLI/testing). Defaults to False (non-blocking).",
    ),
    db: Session = Depends(get_db),
) -> UploadDocumentResponse:
    """Upload PDF document, create an ingestion job, and dispatch to background worker without blocking."""
    source_filename = sanitize_filename(file.filename, default_name="uploaded_document.pdf")
    content = await validate_file_upload(file=file, allowed_extensions={".pdf"})

    document_id = f"doc_{uuid.uuid4().hex[:12]}"

    # Persist document metadata in PostgreSQL with initial 'queued' status
    doc = Document(
        id=document_id,
        title=source_filename,
        department=department,
        category=category,
        page_count=0,
        chunk_count=0,
        file_size_bytes=len(content),
        status="queued",
        summary=summary,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Initialize tracking job
    job = ingestion_worker.create_job(db=db, document_id=doc.id)

    # Dispatch to worker (either asynchronously in background thread pool or synchronously if requested)
    ingestion_worker.dispatch_job(
        job_id=job.id,
        document_id=doc.id,
        content=content,
        source_filename=source_filename,
        metadata={"department": department, "category": category},
        sync=sync,
        db=db if sync else None,
    )

    if sync:
        db.refresh(doc)
        db.refresh(job)
        document_item = DocumentItem(
            id=doc.id,
            title=doc.title,
            category=doc.category,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
            size_bytes=doc.file_size_bytes,
            status=doc.status,  # type: ignore[arg-type]
            department=doc.department,
            summary=doc.summary or "",
            created_at=doc.created_at,
        )
        return UploadDocumentResponse(
            job_id=job.id,
            job_status=job.status,  # type: ignore[arg-type]
            document=document_item,
            total_pages=job.total_pages,
            processed_pages=job.processed_pages,
            total_chunks=job.total_chunks,
            warnings=[],
            processing_time_ms=job.processing_time_ms,
        )

    # Non-blocking HTTP return: job is queued/processing in the background
    document_item = DocumentItem(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        size_bytes=doc.file_size_bytes,
        status="queued",
        department=doc.department,
        summary=doc.summary or "",
        created_at=doc.created_at,
    )
    return UploadDocumentResponse(
        job_id=job.id,
        job_status="queued",
        document=document_item,
        total_pages=0,
        processed_pages=0,
        total_chunks=0,
        warnings=[],
        processing_time_ms=0.0,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ingestion job status",
    description="Retrieve lifecycle status, current pipeline stage, progress percentage, and metrics for a background ingestion job.",
)
async def get_ingestion_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> IngestionJobResponse:
    """Retrieve detailed status of an ingestion background job."""
    valid_id = validate_entity_id(job_id)
    job = ingestion_worker.get_job(db=db, job_id=valid_id)
    if not job:
        raise EntityNotFoundError("IngestionJob", valid_id)

    return IngestionJobResponse(
        id=job.id,
        document_id=job.document_id,
        status=job.status,  # type: ignore[arg-type]
        stage=job.stage,
        progress_pct=job.progress_pct,
        total_pages=job.total_pages,
        processed_pages=job.processed_pages,
        total_chunks=job.total_chunks,
        error_message=job.error_message,
        processing_time_ms=job.processing_time_ms,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
    )


@router.get(
    "/{document_id}/jobs",
    response_model=list[IngestionJobResponse],
    status_code=status.HTTP_200_OK,
    summary="List jobs for document",
    description="Retrieve all background processing jobs associated with a document identifier.",
)
async def list_document_jobs(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[IngestionJobResponse]:
    """List historical and active ingestion jobs for a document."""
    valid_id = validate_entity_id(document_id)
    jobs = ingestion_worker.get_document_jobs(db=db, document_id=valid_id)
    return [
        IngestionJobResponse(
            id=j.id,
            document_id=j.document_id,
            status=j.status,  # type: ignore[arg-type]
            stage=j.stage,
            progress_pct=j.progress_pct,
            total_pages=j.total_pages,
            processed_pages=j.processed_pages,
            total_chunks=j.total_chunks,
            error_message=j.error_message,
            processing_time_ms=j.processing_time_ms,
            created_at=j.created_at,
            updated_at=j.updated_at,
            completed_at=j.completed_at,
        )
        for j in jobs
    ]


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document processing status",
    description="Lightweight endpoint exposing current processing status and progress for frontend polling.",
)
async def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentStatusResponse:
    """Retrieve combined document and active job status for real-time frontend indicators."""
    valid_id = validate_entity_id(document_id)
    doc = db.get(Document, valid_id)
    if not doc:
        raise EntityNotFoundError("Document", valid_id)

    latest_jobs = ingestion_worker.get_document_jobs(db=db, document_id=valid_id)
    latest_job = latest_jobs[0] if latest_jobs else None

    return DocumentStatusResponse(
        document_id=doc.id,
        title=doc.title,
        status=doc.status,
        job_id=latest_job.id if latest_job else None,
        job_status=latest_job.status if latest_job else None,
        stage=latest_job.stage if latest_job else None,
        progress_pct=latest_job.progress_pct if latest_job else (100 if doc.status == "ready" else 0),
        total_pages=latest_job.total_pages if latest_job else doc.page_count,
        chunk_count=latest_job.total_chunks if latest_job else doc.chunk_count,
        error_message=latest_job.error_message if latest_job else None,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentItem,
    status_code=status.HTTP_200_OK,
    summary="Get document by ID",
    description="Retrieve a single document by its unique identifier.",
)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentItem:
    """Retrieve document by ID."""
    valid_id = validate_entity_id(document_id)
    document = documents_service.get_document_by_id(db=db, document_id=valid_id)
    if not document:
        raise EntityNotFoundError("Document", valid_id)
    return document
