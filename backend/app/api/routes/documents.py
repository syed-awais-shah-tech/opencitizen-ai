"""API routes for municipal documents and vector chunks."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.errors import EntityNotFoundError
from app.db.session import get_db
from app.schemas.documents import DocumentCreate, DocumentItem, DocumentListResponse
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
