"""Comprehensive test suite for Stage 14 Evaluation Framework."""

import json
from pathlib import Path
import pytest

from app.evaluation.dataset import (
    get_benchmark_dataset,
    load_benchmark_dataset_from_json,
    save_benchmark_dataset_to_json,
)
from app.evaluation.evaluator import OpenCitizenEvaluator
from app.evaluation.metrics import (
    compute_token_f1,
    detect_unsupported_claims,
    evaluate_answer_correctness,
    evaluate_citation_correctness,
    evaluate_retrieval_success,
)
from app.evaluation.models import (
    BenchmarkItem,
    BenchmarkReport,
    QueryEvaluationResult,
)
from app.evaluation.runner import build_evaluation_pipeline, run_evaluation
from app.schemas.query import CitationItem
from app.search.models import VectorSearchResult


# ==============================================================================
# 1. Tests for Benchmark Dataset
# ==============================================================================


def test_benchmark_dataset_integrity() -> None:
    """Verify benchmark items conform to schema and ground-truth requirements."""
    items = get_benchmark_dataset()

    assert len(items) >= 10
    question_ids = [item.question_id for item in items]
    # Ensure IDs are unique
    assert len(question_ids) == len(set(question_ids))

    for item in items:
        assert item.question.strip()
        assert item.expected_answer.strip()
        assert item.category in ["budget", "healthcare", "zoning", "transit", "water", "unsupported"]

        if not item.is_refusal_expected:
            assert len(item.answer_criteria) >= 1
            assert len(item.expected_source_documents) >= 1
            assert len(item.expected_chunk_ids) >= 1
            assert len(item.expected_evidence_snippets) >= 1
        else:
            assert item.is_refusal_expected is True


def test_benchmark_dataset_json_serialization(tmp_path: Path) -> None:
    """Test saving and loading the benchmark dataset to/from a standalone JSON file."""
    json_path = tmp_path / "test_benchmark.json"
    save_benchmark_dataset_to_json(json_path)

    assert json_path.exists()
    loaded_items = load_benchmark_dataset_from_json(json_path)

    assert len(loaded_items) == len(get_benchmark_dataset())
    assert loaded_items[0].question_id == "BENCH-001"
    assert loaded_items[0].question == get_benchmark_dataset()[0].question


# ==============================================================================
# 2. Tests for Metric Calculations
# ==============================================================================


def test_retrieval_success_metric() -> None:
    """Test retrieval success, chunk recall, and document precision calculations."""
    item = BenchmarkItem(
        question_id="TEST-01",
        question="What is the park budget?",
        category="budget",
        expected_answer="12.5 million",
        answer_criteria=["12.5 million"],
        expected_source_documents=["budget.pdf"],
        expected_chunk_ids=["chk_1", "chk_2"],
    )

    # 1. Partial recall (1 of 2 chunks retrieved)
    retrieved = [
        VectorSearchResult(
            chunk_id="chk_1",
            document_id="doc-1",
            page_number=1,
            source_filename="budget.pdf",
            original_text="12.5 million for parks",
            score=0.9,
        ),
        VectorSearchResult(
            chunk_id="chk_other",
            document_id="doc-2",
            page_number=1,
            source_filename="other.pdf",
            original_text="unrelated",
            score=0.4,
        ),
    ]

    success, recall, prec = evaluate_retrieval_success(retrieved, item)
    assert success is True
    assert recall == 0.5
    assert prec == 0.5

    # 2. Complete miss
    unrelated = [
        VectorSearchResult(
            chunk_id="chk_x",
            document_id="doc-x",
            page_number=1,
            source_filename="unrelated.pdf",
            original_text="unrelated text",
            score=0.1,
        )
    ]
    succ_miss, rec_miss, prec_miss = evaluate_retrieval_success(unrelated, item)
    assert succ_miss is False
    assert rec_miss == 0.0
    assert prec_miss == 0.0


def test_citation_correctness_metric() -> None:
    """Test citation validity and excerpt grounding checks."""
    item = BenchmarkItem(
        question_id="TEST-02",
        question="What is the lead standard?",
        category="water",
        expected_answer="EPA-502.2 standard",
        expected_source_documents=["water_report.pdf"],
        expected_chunk_ids=["chk_w1"],
    )

    retrieved = [
        VectorSearchResult(
            chunk_id="chk_w1",
            document_id="doc-w",
            page_number=3,
            source_filename="water_report.pdf",
            original_text="Quarterly lead analysis complies with EPA-502.2 standard guidelines.",
            score=0.95,
        )
    ]

    # Valid grounded citation
    valid_citations = [
        CitationItem(
            document_title="water_report.pdf",
            page_number=3,
            similarity_score=0.95,
            excerpt="Quarterly lead analysis complies with EPA-502.2 standard guidelines.",
            chunk_id="chk_w1",
        )
    ]

    score, prec, rec = evaluate_citation_correctness(valid_citations, retrieved, item)
    assert score == 1.0
    assert prec == 1.0
    assert rec == 1.0

    # Fabricated citation from wrong document
    invalid_citations = [
        CitationItem(
            document_title="fabricated_document.pdf",
            page_number=1,
            similarity_score=0.2,
            excerpt="fabricated claim not in text",
            chunk_id="chk_fake",
        )
    ]
    inv_score, inv_prec, inv_rec = evaluate_citation_correctness(invalid_citations, retrieved, item)
    assert inv_score == 0.0
    assert inv_prec == 0.0
    assert inv_rec == 0.0


def test_answer_correctness_and_negative_criteria() -> None:
    """Test answer criteria verification and hallucination penalty."""
    item = BenchmarkItem(
        question_id="TEST-03",
        question="What are the setback limits?",
        category="zoning",
        expected_answer="Minimum setback is 25 feet under ORD-2023-45.",
        answer_criteria=["25 feet", "ORD-2023-45"],
        negative_criteria=["60 feet height limit", "residential R-1"],
    )

    # 1. Correct answer meeting all criteria
    correct_ans = "Under Zoning Ordinance ORD-2023-45, the minimum structural setback is 25 feet."
    score, crit_rate, f1 = evaluate_answer_correctness(correct_ans, False, item)
    assert crit_rate == 1.0
    assert score >= 0.8
    assert f1 > 0.4

    # 2. Answer containing negative forbidden criteria (hallucination)
    hallucinated_ans = "The setback is 25 feet under ORD-2023-45 but residential R-1 has 60 feet height limit."
    h_score, h_crit, _ = evaluate_answer_correctness(hallucinated_ans, False, item)
    # Penalized for negative criteria violation
    assert h_crit < 1.0


def test_token_f1_calculation() -> None:
    """Test token F1 metric between prediction and ground truth strings."""
    assert compute_token_f1("exact match string", "exact match string") == 1.0
    assert compute_token_f1("completely disjoint tokens", "apples oranges bananas") == 0.0
    f1 = compute_token_f1("the budget allocation is 12 million dollars", "12 million dollars allocated to budget")
    assert 0.5 <= f1 <= 1.0


def test_detect_unsupported_claims() -> None:
    """Test detection of numbers and identifiers absent from retrieved evidence."""
    retrieved = [
        VectorSearchResult(
            chunk_id="chk_b1",
            document_id="doc-b",
            page_number=1,
            source_filename="budget.pdf",
            original_text="City Council approved 12.5 million dollars under Resolution RES-2024-089.",
            score=0.9,
        )
    ]

    # 1. Supported answer
    supported_ans = "City Council allocated 12.5 million dollars under Resolution RES-2024-089."
    count, has_unsupp, details = detect_unsupported_claims(supported_ans, retrieved, False)
    assert count == 0
    assert has_unsupp is False
    assert len(details) == 0

    # 2. Unsupported numerical claim (e.g. inventing 99.8 million)
    unsupported_ans = "City Council allocated 99.8 million dollars under Resolution RES-2024-089."
    u_count, u_has, u_details = detect_unsupported_claims(unsupported_ans, retrieved, False)
    assert u_count >= 1
    assert u_has is True
    assert any("99.8" in d for d in u_details)


# ==============================================================================
# 3. Tests for Evaluator Engine and Reproducible Runner
# ==============================================================================


def test_open_citizen_evaluator_single_item() -> None:
    """Test evaluating a single benchmark item with the evaluation pipeline."""
    pipeline = build_evaluation_pipeline(provider_type="mock")
    evaluator = OpenCitizenEvaluator(pipeline=pipeline)

    item = get_benchmark_dataset()[0]  # BENCH-001
    result: QueryEvaluationResult = evaluator.evaluate_item(item)

    assert result.question_id == "BENCH-001"
    assert result.retrieval_success is True
    assert result.chunk_recall == 1.0
    assert result.citation_correctness == 1.0
    assert result.criteria_match_rate == 1.0
    assert result.has_unsupported_claims is False
    assert result.total_latency_ms >= 0.0


def test_open_citizen_evaluator_full_dataset_report() -> None:
    """Test executing full benchmark evaluation generates complete report."""
    pipeline = build_evaluation_pipeline(provider_type="mock")
    evaluator = OpenCitizenEvaluator(pipeline=pipeline)

    report: BenchmarkReport = evaluator.evaluate_dataset()

    assert report.benchmark_version == "1.0.0"
    assert report.overall_metrics.total_queries == 12
    assert report.overall_metrics.retrieval_success_rate == 1.0
    assert report.overall_metrics.citation_correctness_score >= 0.95
    assert report.overall_metrics.answer_correctness_score >= 0.85
    assert report.overall_metrics.unsupported_claims_rate == 0.0
    assert report.overall_metrics.refusal_accuracy == 1.0
    assert report.overall_metrics.p50_latency_ms > 0.0
    assert len(report.per_query_results) == 12


def test_reproducible_runner_json_output(tmp_path: Path) -> None:
    """Test runner writes valid machine-readable JSON to the specified path."""
    out_file = tmp_path / "eval_out.json"
    report = run_evaluation(output_path=str(out_file), quiet=True)

    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["benchmark_version"] == "1.0.0"
    assert "overall_metrics" in data
    assert "per_query_results" in data
    assert data["overall_metrics"]["retrieval_success_rate"] == 1.0
    assert data["overall_metrics"]["refusal_accuracy"] == 1.0
