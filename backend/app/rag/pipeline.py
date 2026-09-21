"""Production-oriented Retrieval-Augmented Generation (RAG) Pipeline.

Flow:
user question
-> question processing
-> vector retrieval
-> relevant chunks
-> Gemini (AI provider)
-> grounded answer
"""

import logging
import time

from app.ai.models import EvidenceContext
from app.ai.prompts import INSUFFICIENT_EVIDENCE_PHRASE
from app.ai.provider import BaseAIProvider, get_ai_provider
from app.core.config import settings
from app.rag.models import RAGResponse
from app.schemas.query import CitationItem
from app.search.dependencies import get_vector_search_service
from app.search.models import VectorSearchResult
from app.search.service import VectorSearchService
from app.trust.builder import build_trust_report

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates question processing, vector search, and grounded AI generation."""

    def __init__(
        self,
        vector_service: VectorSearchService | None = None,
        ai_provider: BaseAIProvider | None = None,
        top_k: int | None = None,
        score_threshold: float | None = None,
    ):
        self.vector_service = vector_service or get_vector_search_service()
        self.ai_provider = ai_provider or get_ai_provider()
        self.top_k = top_k or settings.RAG_TOP_K
        self.score_threshold = (
            score_threshold
            if score_threshold is not None
            else settings.RAG_SCORE_THRESHOLD
        )

    def process_question(self, question: str) -> str:
        """Step 1: Sanitize and preprocess natural language inquiry."""
        if not question or not question.strip():
            raise ValueError("User question cannot be empty or whitespace only.")
        return question.strip()

    def run(
        self,
        question: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
        filter_document_id: str | None = None,
    ) -> RAGResponse:
        """Execute the end-to-end RAG pipeline:

        question -> process -> vector retrieval -> relevant chunks -> Gemini -> grounded answer
        """
        start_time = time.perf_counter()

        # Step 1: Question processing
        processed_question = self.process_question(question)

        # Step 2: Vector retrieval
        k = top_k or self.top_k
        threshold = (
            score_threshold if score_threshold is not None else self.score_threshold
        )

        logger.info(
            "Executing vector retrieval for query '%s' (top_k=%d, threshold=%s)",
            processed_question,
            k,
            threshold,
        )

        search_start = time.perf_counter()
        search_results: list[VectorSearchResult] = self.vector_service.search(
            query=processed_question,
            top_k=k,
            score_threshold=threshold,
            filter_document_id=filter_document_id,
        )
        search_latency_ms = round((time.perf_counter() - search_start) * 1000, 2)

        # Step 3: Extract relevant chunks into evidence contexts
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

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Step 4: Handle zero retrieval results immediately
        if not contexts:
            logger.info("No relevant chunks retrieved; asserting insufficient evidence")
            trust_report = build_trust_report(
                answer=INSUFFICIENT_EVIDENCE_PHRASE,
                evidence_items=[],
                model_identifier=self.ai_provider.model_name,
                top_k=k,
                score_threshold=threshold,
                search_latency_ms=search_latency_ms,
                is_insufficient_evidence=True,
            )
            return RAGResponse(
                question=processed_question,
                answer=INSUFFICIENT_EVIDENCE_PHRASE,
                citations=[],
                retrieved_chunks_count=0,
                is_insufficient_evidence=True,
                model_name=self.ai_provider.model_name,
                latency_ms=elapsed_ms,
                trust=trust_report,
            )

        # Step 5: Send evidence to Gemini / AI Provider
        logger.info(
            "Sending %d evidence chunks to AI provider '%s'",
            len(contexts),
            self.ai_provider.model_name,
        )

        llm_answer = self.ai_provider.generate_grounded_answer(
            question=processed_question,
            contexts=contexts,
        )

        total_elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Step 6: Format citations and grounded answer
        if llm_answer.is_insufficient_evidence:
            logger.info("AI provider indicated evidence was insufficient to answer")
            trust_report = build_trust_report(
                answer=INSUFFICIENT_EVIDENCE_PHRASE,
                evidence_items=contexts,
                model_identifier=llm_answer.model_name,
                top_k=k,
                score_threshold=threshold,
                search_latency_ms=search_latency_ms,
                is_insufficient_evidence=True,
            )
            return RAGResponse(
                question=processed_question,
                answer=INSUFFICIENT_EVIDENCE_PHRASE,
                citations=[],
                retrieved_chunks_count=len(contexts),
                is_insufficient_evidence=True,
                model_name=llm_answer.model_name,
                latency_ms=total_elapsed_ms,
                trust=trust_report,
            )

        # Build citation items preserving source and page metadata
        # Filter citations to documents referenced by the AI model
        referenced_titles = {ref.lower() for ref in llm_answer.citation_references}
        if referenced_titles:
            active_contexts = [
                ctx for ctx in contexts
                if ctx.document_title.lower() in referenced_titles
            ]
            if not active_contexts:
                active_contexts = contexts
        else:
            active_contexts = contexts

        citations: list[CitationItem] = []
        for ctx in active_contexts:
            citations.append(
                CitationItem(
                    document_title=ctx.document_title,
                    page_number=ctx.page_number,
                    similarity_score=round(ctx.score, 4),
                    excerpt=ctx.text,
                    chunk_id=ctx.chunk_id,
                    department=ctx.metadata.get("department"),
                )
            )

        trust_report = build_trust_report(
            answer=llm_answer.answer_text,
            evidence_items=contexts,
            model_identifier=llm_answer.model_name,
            top_k=k,
            score_threshold=threshold,
            search_latency_ms=search_latency_ms,
            is_insufficient_evidence=False,
        )

        return RAGResponse(
            question=processed_question,
            answer=llm_answer.answer_text,
            citations=citations,
            retrieved_chunks_count=len(contexts),
            is_insufficient_evidence=False,
            model_name=llm_answer.model_name,
            latency_ms=total_elapsed_ms,
            trust=trust_report,
        )


def get_rag_pipeline(
    vector_service: VectorSearchService | None = None,
    ai_provider: BaseAIProvider | None = None,
) -> RAGPipeline:
    """Factory helper creating RAG pipeline with default dependencies."""
    return RAGPipeline(
        vector_service=vector_service,
        ai_provider=ai_provider,
    )
