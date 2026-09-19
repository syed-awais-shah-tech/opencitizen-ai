"""Service layer for evidence-grounded natural language queries."""

import time
import uuid
from app.schemas.query import (
    CalculationItem,
    CitationItem,
    QueryRequest,
    QueryResponse,
)


class QueryService:
    """Service orchestrating dual retrieval (Qdrant semantic search + DuckDB SQL execution)."""

    def process_query(self, request: QueryRequest) -> QueryResponse:
        """Process a natural language civic inquiry.

        In Stage 3, this returns a clearly marked placeholder response
        with schema-compliant citation and calculation structures.
        """
        start_time = time.perf_counter()

        query_id = f"qry_{uuid.uuid4().hex[:12]}"

        # Synthesize Stage 3 placeholder answer
        answer = (
            f"[Stage 3 API Placeholder] Inquiry: '{request.question}'. "
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
