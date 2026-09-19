"""API routes for municipal documents and vector chunks."""

from fastapi import APIRouter, Query, status
from app.schemas.documents import DocumentListResponse
from app.services.documents_service import documents_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List ingested documents",
    description="Retrieve the collection of ingested municipal PDF documents indexed into Qdrant vector storage.",
)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> DocumentListResponse:
    """Retrieve collection of ingested municipal documents."""
    return documents_service.get_documents(limit=limit, offset=offset)
