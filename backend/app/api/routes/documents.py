"""API routes for municipal documents, vector chunks, and PDF ingestion."""

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.errors import EntityNotFoundError
from app.db.session import get_db
from app.ingestion.pipeline import pipeline
from app.models.document import Document
from app.schemas.documents import (
    DocumentCreate,
    DocumentItem,
    DocumentListResponse,
    UploadDocumentResponse,
)
from app.services.documents_service import documents_service

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
    description="Extracts page-by-page text, sanitizes content, splits into structured chunks, and persists metadata.",
)
async def upload_document(
    file: UploadFile = File(..., description="User-uploaded PDF document"),
    department: str = Form(default="General", description="Issuing municipal department"),
    category: str = Form(default="Report", description="Document category"),
    summary: str = Form(default="", description="Optional executive summary"),
    db: Session = Depends(get_db),
) -> UploadDocumentResponse:
    """Execute PDF ingestion pipeline over uploaded file."""
    content = await file.read()
    source_filename = file.filename or "uploaded_document.pdf"

    # Execute ingestion pipeline
    result = pipeline.process_bytes(
        content=content,
        source_filename=source_filename,
        metadata={"department": department, "category": category},
    )

    # Persist document metadata in PostgreSQL
    doc = Document(
        id=result.document_id,
        title=source_filename,
        department=department,
        category=category,
        page_count=result.total_pages,
        chunk_count=result.total_chunks,
        file_size_bytes=len(content),
        status="ready",
        summary=summary,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

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
        document=document_item,
        total_pages=result.total_pages,
        processed_pages=result.processed_pages,
        total_chunks=result.total_chunks,
        warnings=result.warnings,
        processing_time_ms=result.processing_time_ms,
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
    document = documents_service.get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise EntityNotFoundError("Document", document_id)
    return document
