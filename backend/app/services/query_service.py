"""Service layer for evidence-grounded natural language queries and audit persistence."""

import time
import uuid

from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.citation import Citation
from app.models.query import Query
from app.orchestration.orchestrator import QueryOrchestrator, query_orchestrator
from app.rag.pipeline import RAGPipeline, get_rag_pipeline
from app.schemas.query import (
    CalculationItem,
    CitationItem,
    QueryRequest,
    QueryResponse,
)


class QueryService:
    """Service orchestrating controlled query routing, multi-source execution, and audit persistence."""

    def __init__(
        self,
        rag_pipeline: RAGPipeline | None = None,
        orchestrator: QueryOrchestrator | None = None,
    ):
        self._rag_pipeline = rag_pipeline
        self._orchestrator = orchestrator

    @property
    def rag_pipeline(self) -> RAGPipeline:
        if self._rag_pipeline is None:
            self._rag_pipeline = get_rag_pipeline()
        return self._rag_pipeline

    @property
    def orchestrator(self) -> QueryOrchestrator:
        if self._orchestrator is None:
            if self._rag_pipeline is not None:
                self._orchestrator = QueryOrchestrator(rag_pipeline=self._rag_pipeline)
            else:
                self._orchestrator = query_orchestrator
        return self._orchestrator

    def process_query(
        self, request: QueryRequest, db: Session | None = None
    ) -> QueryResponse:
        """Process a natural language civic inquiry via the query orchestration layer."""
        response = self.orchestrator.orchestrate(request=request, db=db)

        # Persist query and answer audit trail in PostgreSQL if database session provided
        if db is not None:
            db_query = Query(
                id=response.query_id,
                session_id=request.session_id,
                question=request.question,
                status=response.status,
            )
            db.add(db_query)

            db_answer = Answer(
                id=f"ans_{uuid.uuid4().hex[:12]}",
                query_id=response.query_id,
                answer_text=response.answer,
                latency_ms=response.latency_ms,
                is_placeholder=response.is_placeholder,
                calculation_trace=response.calculation.model_dump() if response.calculation else None,
            )
            db.add(db_answer)

            for cit in response.citations:
                db_citation = Citation(
                    id=f"cit_{uuid.uuid4().hex[:12]}",
                    answer_id=db_answer.id,
                    document_title=cit.document_title,
                    page_number=cit.page_number,
                    similarity_score=cit.similarity_score,
                    excerpt=cit.excerpt,
                    chunk_id=cit.chunk_id,
                    department=cit.department,
                )
                db.add(db_citation)

            db.commit()

        return response


query_service = QueryService()
