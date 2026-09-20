"""Query orchestration engine coordinating controlled routing, tool execution, and synthesis."""

import logging
import time
import uuid
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.ai.models import EvidenceContext
from app.ai.provider import BaseAIProvider, get_ai_provider
from app.analytics.schemas import AnalyticalResult
from app.core.config import settings
from app.orchestration.models import RouteCategory, RoutingDecision
from app.orchestration.router import QueryRouter, query_router_service
from app.orchestration.tools import (
    DataAnalysisInput,
    DataAnalysisTool,
    DocumentRetrievalInput,
    DocumentRetrievalTool,
    ToolRegistry,
    tool_registry,
)
from app.rag.pipeline import RAGPipeline, get_rag_pipeline
from app.schemas.query import CalculationItem, CitationItem, QueryRequest, QueryResponse
from app.services.analytics_service import AnalyticsService, analytics_service
from app.trust.builder import build_trust_report
from app.trust.models import TrustReport

logger = logging.getLogger(__name__)

UNSUPPORTED_RESPONSE_TEXT = (
    "I am unable to answer this inquiry. OpenCitizen AI is an evidence-grounded civic intelligence "
    "platform designed to answer inquiries using verified municipal policy documents and structured civic datasets. "
    "Your question does not appear to reference supported civic documents or datasets."
)


class QueryOrchestrator:
    """Orchestrates query classification, tool invocation, and multi-source evidence synthesis."""

    def __init__(
        self,
        router: QueryRouter | None = None,
        tools: ToolRegistry | None = None,
        rag_pipeline: RAGPipeline | None = None,
        analytics_svc: AnalyticsService | None = None,
        ai_provider: BaseAIProvider | None = None,
    ) -> None:
        self._router = router
        self._tools = tools
        self._rag_pipeline = rag_pipeline
        self._analytics_svc = analytics_svc
        self._ai_provider = ai_provider

    @property
    def router(self) -> QueryRouter:
        if self._router is not None:
            return self._router
        return query_router_service

    @property
    def tools(self) -> ToolRegistry:
        if self._tools is not None:
            return self._tools
        return tool_registry

    @property
    def rag_pipeline(self) -> RAGPipeline:
        if self._rag_pipeline is not None:
            return self._rag_pipeline
        return get_rag_pipeline()

    @property
    def analytics_svc(self) -> AnalyticsService:
        if self._analytics_svc is not None:
            return self._analytics_svc
        return analytics_service

    @property
    def ai_provider(self) -> BaseAIProvider:
        if self._ai_provider is not None:
            return self._ai_provider
        return get_ai_provider()

    def orchestrate(
        self,
        request: QueryRequest,
        db: Session | None = None,
    ) -> QueryResponse:
        """Route and execute a civic inquiry across document retrieval and structured analytics."""
        start_time = time.perf_counter()
        query_id = f"qry_{uuid.uuid4().hex[:12]}"

        # Step 1: Query Router classifies the question into one of 4 categories
        routing_decision: RoutingDecision = self.router.classify(request.question)
        logger.info(
            "Orchestrator routed inquiry '%s' to '%s' (confidence=%.2f): %s",
            request.question,
            routing_decision.route.value,
            routing_decision.confidence,
            routing_decision.reasoning,
        )

        route = routing_decision.route

        # Respect explicit client configuration flags
        if not request.include_calculations and request.include_citations:
            if route in (RouteCategory.DATA_ANALYSIS, RouteCategory.BOTH):
                route = RouteCategory.DOCUMENT_RETRIEVAL
        elif not request.include_citations and request.include_calculations:
            if route == RouteCategory.BOTH:
                route = RouteCategory.DATA_ANALYSIS

        # Step 2: Dispatch based on routing category
        if route == RouteCategory.UNSUPPORTED:
            return self._handle_unsupported(query_id, request, routing_decision, start_time)

        if route == RouteCategory.DOCUMENT_RETRIEVAL:
            return self._handle_document_retrieval(query_id, request, routing_decision, start_time)

        if route == RouteCategory.DATA_ANALYSIS:
            return self._handle_data_analysis(query_id, request, routing_decision, start_time, db)

        if route == RouteCategory.BOTH:
            return self._handle_both(query_id, request, routing_decision, start_time, db)

        # Fallback safeguard
        return self._handle_unsupported(query_id, request, routing_decision, start_time)

    def _handle_unsupported(
        self,
        query_id: str,
        request: QueryRequest,
        decision: RoutingDecision,
        start_time: float,
    ) -> QueryResponse:
        """Category 4: Neither / Unsupported. Zero DB and zero vector queries executed."""
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        trust = build_trust_report(
            answer=UNSUPPORTED_RESPONSE_TEXT,
            evidence_items=[],
            model_identifier=self.ai_provider.model_name,
            top_k=0,
            score_threshold=0.0,
            is_insufficient_evidence=True,
            custom_limitations=[
                "Unsupported Inquiry: The submitted question does not reference supported civic datasets or indexed municipal documents."
            ],
        )
        return QueryResponse(
            query_id=query_id,
            question=request.question,
            answer=UNSUPPORTED_RESPONSE_TEXT,
            citations=[],
            calculation=None,
            latency_ms=elapsed_ms,
            is_placeholder=False,
            status="completed",
            trust=trust,
            route=decision.route.value,
            routing_reasoning=decision.reasoning,
        )

    def _handle_document_retrieval(
        self,
        query_id: str,
        request: QueryRequest,
        decision: RoutingDecision,
        start_time: float,
    ) -> QueryResponse:
        """Category 1: Document Retrieval (Qdrant semantic search)."""
        rag_res = self.rag_pipeline.run(question=request.question)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return QueryResponse(
            query_id=query_id,
            question=request.question,
            answer=rag_res.answer,
            citations=rag_res.citations if request.include_citations else [],
            calculation=None,
            latency_ms=elapsed_ms,
            is_placeholder=rag_res.is_insufficient_evidence,
            status="completed",
            trust=rag_res.trust,
            route=decision.route.value,
            routing_reasoning=decision.reasoning,
        )

    def _handle_data_analysis(
        self,
        query_id: str,
        request: QueryRequest,
        decision: RoutingDecision,
        start_time: float,
        db: Session | None,
    ) -> QueryResponse:
        """Category 2: Structured Data Analysis (DuckDB analytical pipeline)."""
        data_tool: DataAnalysisTool = self.tools.get_tool("data_analysis")  # type: ignore[assignment]
        analytical_res: AnalyticalResult = data_tool.execute(
            DataAnalysisInput(
                question=request.question,
                table_name=decision.target_table,
            ),
            db=db,
        )

        calculation_item = self.analytics_svc.to_calculation_item(analytical_res)
        answer_text = self._format_analytical_answer(analytical_res)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        trust = build_trust_report(
            answer=answer_text,
            evidence_items=[],
            model_identifier=self.ai_provider.model_name,
            top_k=0,
            score_threshold=0.0,
            is_insufficient_evidence=False,
            vector_store_name="DuckDB In-Memory Catalog",
            custom_limitations=[
                f"Data Provenance: Grounded strictly in validated SQL query results from DuckDB analytical table '{analytical_res.table_name}'."
            ],
        )

        return QueryResponse(
            query_id=query_id,
            question=request.question,
            answer=answer_text,
            citations=[],
            calculation=calculation_item if request.include_calculations else None,
            latency_ms=elapsed_ms,
            is_placeholder=False,
            status="completed",
            trust=trust,
            route=decision.route.value,
            routing_reasoning=decision.reasoning,
        )

    def _handle_both(
        self,
        query_id: str,
        request: QueryRequest,
        decision: RoutingDecision,
        start_time: float,
        db: Session | None,
    ) -> QueryResponse:
        """Category 3: Both (Hybrid: DuckDB quantitative calculation + Qdrant narrative context)."""
        # Step 3a: Run structured data analysis
        data_tool: DataAnalysisTool = self.tools.get_tool("data_analysis")  # type: ignore[assignment]
        analytical_res: AnalyticalResult = data_tool.execute(
            DataAnalysisInput(
                question=request.question,
                table_name=decision.target_table,
            ),
            db=db,
        )
        calculation_item = self.analytics_svc.to_calculation_item(analytical_res)
        data_fact = self._format_analytical_answer(analytical_res)

        # Step 3b: Run document retrieval for narrative explanations/policy context
        doc_tool: DocumentRetrievalTool = self.tools.get_tool("document_retrieval")  # type: ignore[assignment]
        search_results = doc_tool.execute(
            DocumentRetrievalInput(
                query=decision.search_query or request.question,
                top_k=settings.RAG_TOP_K,
                score_threshold=settings.RAG_SCORE_THRESHOLD,
            )
        )

        contexts: list[EvidenceContext] = [
            EvidenceContext(
                document_title=res.source_filename,
                page_number=res.page_number,
                chunk_id=res.chunk_id,
                text=res.original_text,
                score=res.score,
                metadata=res.metadata,
            )
            for res in search_results
        ]

        citations: list[CitationItem] = [
            CitationItem(
                document_title=ctx.document_title,
                page_number=ctx.page_number,
                similarity_score=round(ctx.score, 4),
                excerpt=ctx.text,
                chunk_id=ctx.chunk_id,
                department=ctx.metadata.get("department"),
            )
            for ctx in contexts
        ]

        # Step 3c: Synthesize combined answer
        if contexts:
            doc_ans = self.ai_provider.generate_grounded_answer(
                question=request.question,
                contexts=contexts,
            )
            if doc_ans.is_insufficient_evidence:
                answer_text = data_fact
            else:
                answer_text = (
                    f"{data_fact} "
                    f"According to municipal reports: {doc_ans.answer_text}"
                )
        else:
            answer_text = (
                f"{data_fact} "
                "However, no supplementary policy documents or reports were found providing narrative context."
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        trust = build_trust_report(
            answer=answer_text,
            evidence_items=contexts,
            model_identifier=self.ai_provider.model_name,
            top_k=settings.RAG_TOP_K,
            score_threshold=settings.RAG_SCORE_THRESHOLD,
            is_insufficient_evidence=False,
            custom_limitations=[
                f"Hybrid Provenance: Combines structured data analysis from DuckDB table '{analytical_res.table_name}' with qualitative excerpts from municipal policy documents in Qdrant."
            ],
        )

        return QueryResponse(
            query_id=query_id,
            question=request.question,
            answer=answer_text,
            citations=citations if request.include_citations else [],
            calculation=calculation_item if request.include_calculations else None,
            latency_ms=elapsed_ms,
            is_placeholder=False,
            status="completed",
            trust=trust,
            route=decision.route.value,
            routing_reasoning=decision.reasoning,
        )

    @staticmethod
    def _format_analytical_answer(result: AnalyticalResult) -> str:
        """Format DuckDB structured results into a factual, human-readable summary."""
        if not result.rows:
            return f"No records found in table '{result.table_name}' matching query criteria."

        if len(result.rows) == 1:
            row = result.rows[0]
            # Single value or superlative result
            items = [f"{k}: {v}" for k, v in row.items()]
            return f"Based on structured records in '{result.table_name}': {', '.join(items)} (Derivation: {result.derivation})."

        # Multi-row summary
        first_row = result.rows[0]
        return (
            f"Based on structured records in '{result.table_name}', returned {result.row_count} rows. "
            f"Top result: {first_row} (Derivation: {result.derivation})."
        )


# Global singleton orchestrator
query_orchestrator = QueryOrchestrator()
