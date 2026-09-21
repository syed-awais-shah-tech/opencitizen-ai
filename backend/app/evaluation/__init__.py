"""OpenCitizen AI benchmark evaluation framework."""

from app.evaluation.dataset import (
    get_benchmark_dataset,
    load_benchmark_dataset_from_json,
    save_benchmark_dataset_to_json,
)
from app.evaluation.evaluator import OpenCitizenEvaluator
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

__all__ = [
    "BenchmarkItem",
    "BenchmarkReport",
    "OpenCitizenEvaluator",
    "OverallMetrics",
    "QueryEvaluationResult",
    "detect_unsupported_claims",
    "evaluate_answer_correctness",
    "evaluate_citation_correctness",
    "evaluate_retrieval_success",
    "get_benchmark_dataset",
    "load_benchmark_dataset_from_json",
    "save_benchmark_dataset_to_json",
]
