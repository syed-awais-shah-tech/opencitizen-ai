"""API routes for natural language queries and dual retrieval."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import sanitize_prompt_input
from app.db.session import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_service

router = APIRouter(prefix="/query", tags=["Query"])


@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit natural language inquiry",
    description="Submit a question to be answered with evidence grounding via Qdrant semantic search and DuckDB SQL arithmetic.",
)
async def execute_query(
    payload: QueryRequest,
    db: Session = Depends(get_db),
) -> QueryResponse:
    """Execute evidence-grounded civic inquiry and persist execution metadata."""
    payload.question = sanitize_prompt_input(payload.question)
    return query_service.process_query(payload, db=db)
