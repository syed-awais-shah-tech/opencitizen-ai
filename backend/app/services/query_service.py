"""Service layer for evidence-grounded natural language queries and audit persistence."""

import time
import uuid
from sqlalchemy.orm import Session

from app.models.answer import Answer
from app.models.citation import Citation
from app.models.query import Query
from app.schemas.query import (
    CalculationItem,
    CitationItem,
    QueryRequest,
    QueryResponse,
)


class QueryService:
    """Service orchestrating dual retrieval and application metadata persistence."""

    def process_query(
        self, request: QueryRequest, db: Session | None = None
    ) -> QueryResponse:
        """Process a natural language civic inquiry and persist execution metadata."""
        start_time = time.perf_counter()

        query_id = f"qry_{uuid.uuid4().hex[:12]}"

        # Synthesize Stage 4 placeholder answer
        answer = (
            f"[Stage 4 API Query] Inquiry: '{request.question}'. "
            "In subsequent stages, this response will be synthesized by the Gemini AI provider "
            "strictly bounded by Qdrant vector text chunks and DuckDB SQL arithmetic derivations."
        )

        citations: list[CitationItem] = []
        if request.include_citations:
            citations.append(
                CitationItem(
                    document_title="City_Adopted_Budget_2024.pdf",
                    page_number=14,
                    similarity_score=0.912,
                    excerpt=(
                        "Section 3.2 - Parks, Recreation & Community Facilities: "
                        "Authorized operational allocation for fiscal year 2023 was adjusted to $4,250,000."
                    ),
                    chunk_id="chk_city_budget_p14_003",
                    department="Office of Management & Budget",
                )
            )

        calculation: CalculationItem | None = None
        if request.include_calculations:
            calculation = CalculationItem(
                query="SELECT department, SUM(amount) AS total_spent FROM dept_expenses WHERE department = 'Parks & Rec' GROUP BY department;",
                execution_time_ms=18.4,
                rows_scanned=14280,
                table_name="dept_expenses",
                raw_rows=[{"department": "Parks & Rec", "total_spent": 4250000}],
                derivation="SUM(amount) grouped by department where department = 'Parks & Rec' -> $4,250,000.",
            )

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
                is_placeholder=True,
                calculation_trace=calculation.model_dump() if calculation else None,
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
            is_placeholder=True,
            status="completed",
        )


query_service = QueryService()
