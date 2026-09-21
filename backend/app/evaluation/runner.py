"""Reproducible evaluation runner CLI for OpenCitizen AI benchmark.

Usage:
    python -m app.evaluation.runner [--output <path>] [--top-k <int>] [--provider <mock|gemini>]

Outputs a formatted evaluation table and writes machine-readable JSON results.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from app.ai.provider import MockAIProvider, get_ai_provider
from app.evaluation.dataset import get_benchmark_dataset, load_benchmark_dataset_from_json
from app.evaluation.evaluator import OpenCitizenEvaluator
from app.evaluation.models import BenchmarkReport
from app.rag.pipeline import RAGPipeline
from app.search.embeddings import DeterministicEmbeddingProvider, get_embedding_provider
from app.search.service import VectorSearchService
from app.search.vector_store import QdrantVectorStore
from qdrant_client import QdrantClient


def build_evaluation_pipeline(
    provider_type: str = "mock",
    embedding_type: str = "deterministic",
) -> RAGPipeline:
    """Construct an isolated evaluation pipeline with reproducible state."""
    qdrant = QdrantClient(location=":memory:")

    if embedding_type == "deterministic":
        embed_provider = DeterministicEmbeddingProvider(dimension=64)
    else:
        embed_provider = get_embedding_provider()

    store = QdrantVectorStore(
        client=qdrant,
        default_collection="benchmark_eval_collection",
        dimension=embed_provider.dimension,
    )

    vector_service = VectorSearchService(
        vector_store=store,
        embedding_provider=embed_provider,
        collection_name="benchmark_eval_collection",
    )

    if provider_type == "mock":
        ai_provider = MockAIProvider()
    else:
        ai_provider = get_ai_provider(provider_type=provider_type)

    return RAGPipeline(
        vector_service=vector_service,
        ai_provider=ai_provider,
    )


def format_markdown_report(report: BenchmarkReport) -> str:
    """Format benchmark report into a clean, GitHub-Flavored Markdown summary table."""
    m = report.overall_metrics
    lines = [
        "# OpenCitizen AI - Benchmark Evaluation Report",
        "",
        f"- **Report ID**: `{report.report_id}`",
        f"- **Timestamp**: `{report.timestamp}`",
        f"- **Benchmark Version**: `{report.benchmark_version}`",
        f"- **Total Queries**: `{m.total_queries}`",
        f"- **Retrieval Mode**: `{report.retrieval_mode}` (top_k={report.top_k})",
        "",
        "## Overall Metric Summary",
        "",
        "| Metric Dimension | Measured Value | Target / Benchmark Standard | Evaluation Status |",
        "|:---|:---:|:---:|:---:|",
        f"| **Retrieval Success Rate** | **{m.retrieval_success_rate:.1%}** | >= 90.0% | {'PASS' if m.retrieval_success_rate >= 0.9 else 'FAIL'} |",
        f"| **Mean Chunk Recall** | **{m.mean_chunk_recall:.1%}** | >= 85.0% | {'PASS' if m.mean_chunk_recall >= 0.85 else 'FAIL'} |",
        f"| **Mean Document Precision** | **{m.mean_document_precision:.1%}** | >= 70.0% | {'PASS' if m.mean_document_precision >= 0.7 else 'FAIL'} |",
        f"| **Citation Correctness** | **{m.citation_correctness_score:.1%}** | >= 90.0% | {'PASS' if m.citation_correctness_score >= 0.9 else 'FAIL'} |",
        f"| **Mean Citation Precision** | **{m.mean_citation_precision:.1%}** | >= 90.0% | {'PASS' if m.mean_citation_precision >= 0.9 else 'FAIL'} |",
        f"| **Answer Correctness Score** | **{m.answer_correctness_score:.1%}** | >= 80.0% | {'PASS' if m.answer_correctness_score >= 0.8 else 'FAIL'} |",
        f"| **Criteria Match Rate** | **{m.mean_criteria_match_rate:.1%}** | >= 85.0% | {'PASS' if m.mean_criteria_match_rate >= 0.85 else 'FAIL'} |",
        f"| **Token F1 Score** | **{m.mean_token_f1:.4f}** | >= 0.4000 | {'PASS' if m.mean_token_f1 >= 0.4 else 'FAIL'} |",
        f"| **Unsupported Claims Rate** | **{m.unsupported_claims_rate:.1%}** | <= 5.0% | {'PASS' if m.unsupported_claims_rate <= 0.05 else 'FAIL'} |",
        f"| **Refusal Accuracy** | **{m.refusal_accuracy:.1%}** | 100.0% | {'PASS' if m.refusal_accuracy >= 1.0 else 'FAIL'} |",
        "",
        "## Latency Profile",
        "",
        "| Latency Metric | Milliseconds (ms) |",
        "|:---|:---:|",
        f"| **Mean Latency** | {m.mean_latency_ms:.2f} ms |",
        f"| **p50 (Median)** | {m.p50_latency_ms:.2f} ms |",
        f"| **p90 Percentile** | {m.p90_latency_ms:.2f} ms |",
        f"| **p95 Percentile** | {m.p95_latency_ms:.2f} ms |",
        f"| **Min Latency** | {m.min_latency_ms:.2f} ms |",
        f"| **Max Latency** | {m.max_latency_ms:.2f} ms |",
        "",
        "## Per-Query Evaluation Breakdown",
        "",
        "| ID | Category | Retrieval | Citations | Criteria Match | Unsupported Claims | Latency |",
        "|:---|:---|:---:|:---:|:---:|:---:|:---:|",
    ]

    for q in report.per_query_results:
        ret_icon = "PASS" if q.retrieval_success else "FAIL"
        cit_str = f"{q.citation_correctness:.0%}"
        crit_str = f"{q.criteria_match_rate:.0%}"
        unsupp_str = "0" if not q.has_unsupported_claims else str(q.unsupported_claims_count)
        lines.append(
            f"| `{q.question_id}` | {q.category} | {ret_icon} ({q.chunk_recall:.0%}) | {cit_str} | {crit_str} | {unsupp_str} | {q.total_latency_ms:.1f}ms |"
        )

    return "\n".join(lines)


def run_evaluation(
    output_path: str = "storage/evaluation/evaluation_results.json",
    dataset_path: str | None = None,
    top_k: int = 5,
    provider_type: str = "mock",
    embedding_type: str = "deterministic",
    quiet: bool = False,
) -> BenchmarkReport:
    """Execute the full evaluation benchmark, format results, and write machine-readable JSON."""
    pipeline = build_evaluation_pipeline(
        provider_type=provider_type,
        embedding_type=embedding_type,
    )
    evaluator = OpenCitizenEvaluator(pipeline=pipeline)

    if dataset_path:
        dataset = load_benchmark_dataset_from_json(dataset_path)
    else:
        dataset = get_benchmark_dataset()

    report = evaluator.evaluate_dataset(dataset=dataset, top_k=top_k)

    # Ensure output directory exists and write machine-readable JSON
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    if not quiet:
        markdown_table = format_markdown_report(report)
        print("\n" + markdown_table + "\n")
        print(f"Machine-readable results written to: {out_file.resolve()}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run reproducible benchmark evaluation for OpenCitizen AI",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="storage/evaluation/evaluation_results.json",
        help="Target path for machine-readable JSON report",
    )
    parser.add_argument(
        "--dataset",
        "-d",
        type=str,
        default=None,
        help="Optional path to custom benchmark JSON dataset",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=5,
        help="Top-K retrieval depth parameter",
    )
    parser.add_argument(
        "--provider",
        "-p",
        type=str,
        default="mock",
        choices=["mock", "gemini"],
        help="AI Provider to evaluate (default: mock)",
    )
    parser.add_argument(
        "--embedding",
        "-e",
        type=str,
        default="deterministic",
        choices=["deterministic", "gemini"],
        help="Embedding provider type (default: deterministic)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress markdown table console output",
    )

    args = parser.parse_args()

    run_evaluation(
        output_path=args.output,
        dataset_path=args.dataset,
        top_k=args.top_k,
        provider_type=args.provider,
        embedding_type=args.embedding,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
