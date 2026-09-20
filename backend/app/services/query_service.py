"""Service layer for evidence-grounded natural language queries and audit persistence."""

import time
import uuid

from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.citation import Citation
from app.models.query import Query
from app.rag.pipeline import RAGPipeline, get_rag_pipeline
from app.schemas.query import (
    CalculationItem,
    CitationItem,
    QueryRequest,
    QueryResponse,
)


class QueryService:
    """Service orchestrating RAG pipeline retrieval and application metadata persistence."""

    def __init__(self, rag_pipeline: RAGPipeline | None = None):
        self._rag_pipeline = rag_pipeline

    @property
    def rag_pipeline(self) -> RAGPipeline:
        if self._rag_pipeline is None:
            self._rag_pipeline = get_rag_pipeline()
        return self._rag_pipeline

    def process_query(
        self, request: QueryRequest, db: Session | None = None
    ) -> QueryResponse:
        """Process a natural language civic inquiry via the RAG pipeline."""
        start_time = time.perf_counter()
        query_id = f"qry_{uuid.uuid4().hex[:12]}"

        # Execute production RAG pipeline:
        # question -> processing -> vector retrieval -> relevant chunks -> Gemini -> grounded answer
        rag_response = self.rag_pipeline.run(question=request.question)

        answer = rag_response.answer
        citations: list[CitationItem] = []
        if request.include_citations:
            citations = rag_response.citations

        # Quantitative DuckDB SQL arithmetic is deferred to subsequent stage
        calculation: CalculationItem | None = None

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Persist query and answer audit trail in PostgreSQL if database session provided
        if db is not None:
            db_query = Query(
                id=query_id,
                session_id=request.session_id,
                question=request.question,
                status="completed",
            )
            db.add(db_query)

            db_answer = Answer(
                id=f"ans_{uuid.uuid4().hex[:12]}",
                query_id=query_id,
                answer_text=answer,
                latency_ms=elapsed_ms,
                is_placeholder=rag_response.is_insufficient_evidence,
                calculation_trace=None,
            )
            db.add(db_answer)

            for cit in citations:
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

        return QueryResponse(
            query_id=query_id,
            question=request.question,
            answer=answer,
            citations=citations,
            calculation=calculation,
            latency_ms=elapsed_ms,
            is_placeholder=rag_response.is_insufficient_evidence,
            status="completed",
            trust=rag_response.trust,
        )


query_service = QueryService()
