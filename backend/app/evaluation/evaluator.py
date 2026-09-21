"""Core evaluation engine for OpenCitizen AI benchmark."""

from __future__ import annotations

import logging
import statistics
import time
import uuid
from typing import Optional

from app.evaluation.dataset import get_benchmark_dataset
from app.evaluation.metrics import (
    detect_unsupported_claims,
    evaluate_answer_correctness,
    evaluate_citation_correctness,
    evaluate_retrieval_success,
)
from app.evaluation.models import (
    BenchmarkItem,
    BenchmarkReport,
    OverallMetrics,
    QueryEvaluationResult,
)
from app.rag.models import RAGResponse
from app.rag.pipeline import RAGPipeline, get_rag_pipeline
from app.search.evaluation import get_evaluation_corpus

logger = logging.getLogger(__name__)


class OpenCitizenEvaluator:
    """Evaluates RAG pipeline and query orchestrator against benchmark datasets."""

    def __init__(self, pipeline: RAGPipeline | None = None) -> None:
        self.pipeline = pipeline or get_rag_pipeline()

    def evaluate_item(
        self,
        item: BenchmarkItem,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> QueryEvaluationResult:
        """Evaluate a single benchmark item and compute all metrics."""
        start_time = time.perf_counter()

        # Ensure corpus is populated in vector service if empty
        if self.pipeline.vector_service.count() == 0:
            self.pipeline.vector_service.index_chunks(get_evaluation_corpus())

        # Step 1: Run RAG pipeline
        response: RAGResponse = self.pipeline.run(
            question=item.question,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        search_latency_ms = (
            response.trust.retrieval_metadata.search_latency_ms
            if (response.trust and response.trust.retrieval_metadata)
            else 0.0
        )

        # Retrieve raw chunks from vector service to perform evidence alignment
        # (the pipeline already retrieved them, let's also fetch them directly for metric checking)
        retrieved_chunks = self.pipeline.vector_service.search(
            query=item.question,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        actual_source_documents = list(
            {c.source_filename for c in retrieved_chunks}
        )
        actual_chunk_ids = [c.chunk_id for c in retrieved_chunks]
        cited_document_titles = [c.document_title for c in response.citations]

        # Step 2: Compute Retrieval Success
        retrieval_success, chunk_recall, doc_prec = evaluate_retrieval_success(
            retrieved_chunks=retrieved_chunks,
            item=item,
        )

        # Step 3: Compute Citation Correctness
        cit_score, cit_prec, cit_rec = evaluate_citation_correctness(
            citations=response.citations,
            retrieved_chunks=retrieved_chunks,
            item=item,
        )

        # Step 4: Compute Answer Correctness
        ans_score, crit_rate, token_f1 = evaluate_answer_correctness(
            actual_answer=response.answer,
            is_insufficient_evidence=response.is_insufficient_evidence,
            item=item,
        )

        # Step 5: Detect Unsupported Claims
        unsupp_count, has_unsupp, unsupp_details = detect_unsupported_claims(
            actual_answer=response.answer,
            retrieved_chunks=retrieved_chunks,
            is_insufficient_evidence=response.is_insufficient_evidence,
        )

        return QueryEvaluationResult(
            question_id=item.question_id,
            question=item.question,
            category=item.category,
            is_refusal_expected=item.is_refusal_expected,
            actual_answer=response.answer,
            actual_source_documents=actual_source_documents,
            actual_chunk_ids=actual_chunk_ids,
            cited_document_titles=cited_document_titles,
            is_insufficient_evidence=response.is_insufficient_evidence,
            retrieval_success=retrieval_success,
            chunk_recall=chunk_recall,
            document_precision=doc_prec,
            citation_correctness=cit_score,
            citation_precision=cit_prec,
            citation_recall=cit_rec,
            answer_correctness=ans_score,
            criteria_match_rate=crit_rate,
            token_f1=token_f1,
            unsupported_claims_count=unsupp_count,
            has_unsupported_claims=has_unsupp,
            unsupported_claims_detail=unsupp_details,
            search_latency_ms=search_latency_ms,
            total_latency_ms=total_latency_ms,
        )

    def evaluate_dataset(
        self,
        dataset: list[BenchmarkItem] | None = None,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> BenchmarkReport:
        """Run evaluation across all benchmark questions and compute aggregate statistics."""
        items = dataset if dataset is not None else get_benchmark_dataset()

        # Pre-index evaluation corpus into pipeline vector service if needed
        corpus = get_evaluation_corpus()
        self.pipeline.vector_service.index_chunks(corpus)

        results: list[QueryEvaluationResult] = []
        for item in items:
            logger.info("Evaluating benchmark inquiry %s: '%s'", item.question_id, item.question)
            res = self.evaluate_item(item, top_k=top_k, score_threshold=score_threshold)
            results.append(res)

        # Compute aggregate metrics
        n = len(results)
        if n == 0:
            raise ValueError("Cannot compute metrics over an empty benchmark dataset.")

        retrieval_successes = sum(1 for r in results if r.retrieval_success)
        retrieval_success_rate = round(retrieval_successes / n, 4)
        mean_chunk_recall = round(statistics.mean(r.chunk_recall for r in results), 4)
        mean_doc_precision = round(statistics.mean(r.document_precision for r in results), 4)

        citation_correctness_score = round(statistics.mean(r.citation_correctness for r in results), 4)
        mean_citation_precision = round(statistics.mean(r.citation_precision for r in results), 4)
        mean_citation_recall = round(statistics.mean(r.citation_recall for r in results), 4)

        answer_correctness_score = round(statistics.mean(r.answer_correctness for r in results), 4)
        mean_criteria_match_rate = round(statistics.mean(r.criteria_match_rate for r in results), 4)
        mean_token_f1 = round(statistics.mean(r.token_f1 for r in results), 4)

        unsupported_count_total = sum(r.unsupported_claims_count for r in results)
        has_unsupported_count = sum(1 for r in results if r.has_unsupported_claims)
        unsupported_claims_rate = round(has_unsupported_count / n, 4)

        # Refusal accuracy
        refusal_items = [r for r in results if r.is_refusal_expected]
        if refusal_items:
            correct_refusals = sum(1 for r in refusal_items if r.is_insufficient_evidence)
            refusal_accuracy = round(correct_refusals / len(refusal_items), 4)
        else:
            refusal_accuracy = 1.0

        # Latency statistics
        latencies = [r.total_latency_ms for r in results]
        latencies_sorted = sorted(latencies)
        mean_lat = round(statistics.mean(latencies), 2)
        p50_lat = round(statistics.median(latencies), 2)

        def percentile(sorted_vals: list[float], pct: float) -> float:
            k = (len(sorted_vals) - 1) * pct
            f = int(k)
            c = min(f + 1, len(sorted_vals) - 1)
            d0 = sorted_vals[f] * (c - k)
            d1 = sorted_vals[c] * (k - f)
            return round(d0 + d1, 2)

        p90_lat = percentile(latencies_sorted, 0.90)
        p95_lat = percentile(latencies_sorted, 0.95)

        overall = OverallMetrics(
            total_queries=n,
            retrieval_success_rate=retrieval_success_rate,
            mean_chunk_recall=mean_chunk_recall,
            mean_document_precision=mean_doc_precision,
            citation_correctness_score=citation_correctness_score,
            mean_citation_precision=mean_citation_precision,
            mean_citation_recall=mean_citation_recall,
            answer_correctness_score=answer_correctness_score,
            mean_criteria_match_rate=mean_criteria_match_rate,
            mean_token_f1=mean_token_f1,
            unsupported_claims_rate=unsupported_claims_rate,
            total_unsupported_claims=unsupported_count_total,
            refusal_accuracy=refusal_accuracy,
            mean_latency_ms=mean_lat,
            p50_latency_ms=p50_lat,
            p90_latency_ms=p90_lat,
            p95_latency_ms=p95_lat,
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
        )

        report_id = f"eval_{uuid.uuid4().hex[:10]}"
        return BenchmarkReport(
            report_id=report_id,
            benchmark_version="1.0.0",
            retrieval_mode="hybrid",
            top_k=top_k,
            score_threshold=score_threshold,
            overall_metrics=overall,
            per_query_results=results,
        )
