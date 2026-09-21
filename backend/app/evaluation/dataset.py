"""Benchmark dataset definitions and loaders for OpenCitizen AI evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from app.evaluation.models import BenchmarkItem
from app.ingestion.models import DocumentChunk
from app.search.evaluation import get_evaluation_corpus


def get_benchmark_dataset() -> list[BenchmarkItem]:
    """Provide a curated set of 12 representative civic queries with ground truth criteria.

    Includes exact code inquiries, conceptual municipal questions, multi-part synthesis,
    and out-of-scope/unsupported negative test cases.
    """
    return [
        BenchmarkItem(
            question_id="BENCH-001",
            question="What is the budget allocation approved under Resolution RES-2024-089 for public parks?",
            category="budget",
            expected_answer=(
                "Under Resolution RES-2024-089, City Council allocated 12.5 million dollars "
                "to public park maintenance and civic recreation facilities."
            ),
            answer_criteria=["12.5 million", "RES-2024-089", "park maintenance"],
            negative_criteria=["45 million", "highway", "CTR-2023-142"],
            expected_source_documents=["city_annual_budget_2024.pdf"],
            expected_chunk_ids=["chk_budget_01"],
            expected_evidence_snippets=[
                "allocating 12.5 million dollars to public park maintenance and civic recreation facilities"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-002",
            question="How much emergency funding did the transportation department receive for road and bridge repairs?",
            category="budget",
            expected_answer=(
                "The transportation department received emergency capital funding of 45 million dollars "
                "earmarked for critical pothole repairs, roadway resurfacing, and bridge safety overhauls."
            ),
            answer_criteria=["45 million", "pothole", "bridge"],
            negative_criteria=["12.5 million", "park maintenance"],
            expected_source_documents=["city_annual_budget_2024.pdf"],
            expected_chunk_ids=["chk_budget_02"],
            expected_evidence_snippets=[
                "emergency capital funding of 45 million dollars specifically earmarked for critical pothole repairs"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-003",
            question="What healthcare and wellness services are available for children during the summer?",
            category="healthcare",
            expected_answer=(
                "Municipal community healthcare clinics offer free pediatric wellness examinations "
                "and comprehensive routine immunizations for children under age 12 throughout the summer."
            ),
            answer_criteria=["pediatric", "immunizations", "under age 12", "free"],
            negative_criteria=["cholesterol", "adult preventive", "blood pressure"],
            expected_source_documents=["public_health_initiative.pdf"],
            expected_chunk_ids=["chk_health_01"],
            expected_evidence_snippets=[
                "free pediatric wellness examinations and comprehensive routine immunizations for children under age 12"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-004",
            question="What adult preventive care screenings are offered under Community Wellness Initiative CWI-24?",
            category="healthcare",
            expected_answer=(
                "Under the Community Wellness Initiative CWI-24, free blood pressure, cholesterol, "
                "and diabetes screenings are provided at community centers every second Saturday."
            ),
            answer_criteria=["blood pressure", "cholesterol", "diabetes", "second Saturday", "CWI-24"],
            negative_criteria=["under age 12", "pediatric wellness"],
            expected_source_documents=["public_health_initiative.pdf"],
            expected_chunk_ids=["chk_health_02"],
            expected_evidence_snippets=[
                "free blood pressure, cholesterol, and diabetes screenings at community centers every second Saturday"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-005",
            question="What are the commercial structural setback and height limits under Zoning Ordinance ORD-2023-45?",
            category="zoning",
            expected_answer=(
                "Zoning Ordinance ORD-2023-45 mandates a minimum building setback of 25 feet "
                "from arterial roadways and a maximum roofline height limit of 60 feet for commercial structures."
            ),
            answer_criteria=["ORD-2023-45", "25 feet", "60 feet", "setback"],
            negative_criteria=["35 feet", "single-family", "R-1"],
            expected_source_documents=["municipal_zoning_code.pdf"],
            expected_chunk_ids=["chk_zoning_01"],
            expected_evidence_snippets=[
                "minimum building setback of 25 feet from arterial roadways and a maximum roofline height limit of 60 feet"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-006",
            question="What building height and rear yard requirements apply to residential district R-1?",
            category="zoning",
            expected_answer=(
                "In residential zoning district R-1, detached single-family homes have a maximum building "
                "height restriction of 35 feet and a mandatory rear yard depth of 20 feet."
            ),
            answer_criteria=["R-1", "35 feet", "20 feet", "rear yard"],
            negative_criteria=["60 feet", "25 feet setback", "commercial"],
            expected_source_documents=["municipal_zoning_code.pdf"],
            expected_chunk_ids=["chk_zoning_02"],
            expected_evidence_snippets=[
                "maximum residential building height restriction of 35 feet and mandatory rear yard depth of 20 feet"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-007",
            question="What vehicle procurement was authorized under contract CTR-2023-142?",
            category="transit",
            expected_answer=(
                "Under contract CTR-2023-142, the Metropolitan Transit Authority authorized the acquisition "
                "of thirty zero-emission battery-electric heavy-duty transit buses."
            ),
            answer_criteria=["CTR-2023-142", "thirty", "battery-electric", "buses"],
            negative_criteria=["diesel", "Line-42", "Q3 2025"],
            expected_source_documents=["transit_electrification_plan.pdf"],
            expected_chunk_ids=["chk_transit_01"],
            expected_evidence_snippets=[
                "acquisition of thirty zero-emission battery-electric heavy-duty transit buses"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-008",
            question="When will full route electrification for Line-42 be completed, and what infrastructure is included?",
            category="transit",
            expected_answer=(
                "Full route electrification for urban transit Line-42 is scheduled for completion in Q3 2025, "
                "including overhead pantograph rapid-charging stations at the East Terminus."
            ),
            answer_criteria=["Line-42", "Q3 2025", "overhead pantograph", "East Terminus"],
            negative_criteria=["thirty buses", "CTR-2023-142"],
            expected_source_documents=["transit_electrification_plan.pdf"],
            expected_chunk_ids=["chk_transit_02"],
            expected_evidence_snippets=[
                "slated for completion in Q3 2025, including overhead pantograph rapid-charging stations at the East Terminus"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-009",
            question="What were the quarterly findings regarding drinking water lead and copper under EPA-502.2?",
            category="water",
            expected_answer=(
                "In compliance with EPA-502.2 regulatory guidelines, quarterly chemical analyses detected zero "
                "trace lead or copper contamination exceeding federal action thresholds across municipal taps."
            ),
            answer_criteria=["EPA-502.2", "lead", "copper", "zero"],
            negative_criteria=["turbidity", "North Reservoir"],
            expected_source_documents=["drinking_water_quality_report.pdf"],
            expected_chunk_ids=["chk_water_01"],
            expected_evidence_snippets=[
                "quarterly chemical analyses detected zero trace lead or copper contamination exceeding federal action thresholds"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-010",
            question="How is drinking water clarity and purity verified at the North Reservoir?",
            category="water",
            expected_answer=(
                "Drinking water clarity and purity at the North Reservoir are monitored continuously using automated "
                "turbidity sensors and biological monitors, consistently exceeding state environmental benchmarks."
            ),
            answer_criteria=["North Reservoir", "turbidity sensors", "biological monitors"],
            negative_criteria=["EPA-502.2", "lead or copper"],
            expected_source_documents=["drinking_water_quality_report.pdf"],
            expected_chunk_ids=["chk_water_02"],
            expected_evidence_snippets=[
                "Continuous automated turbidity sensors and biological monitors at the North Reservoir"
            ],
            is_refusal_expected=False,
        ),
        BenchmarkItem(
            question_id="BENCH-011",
            question="What is the municipal budget allocated for deep space satellite launches and orbital research?",
            category="unsupported",
            expected_answer=(
                "I am unable to answer this inquiry based on the available municipal documents. "
                "No evidence regarding deep space satellite launches or orbital research exists in municipal records."
            ),
            answer_criteria=["unable to answer", "insufficient evidence"],
            negative_criteria=["allocated", "million dollars", "orbital research program"],
            expected_source_documents=[],
            expected_chunk_ids=[],
            expected_evidence_snippets=[],
            is_refusal_expected=True,
        ),
        BenchmarkItem(
            question_id="BENCH-012",
            question="Which Hollywood actors were paid by the city for commercial filming permits in 2024?",
            category="unsupported",
            expected_answer=(
                "I am unable to answer this inquiry based on the available evidence. "
                "The verified municipal records do not contain information on Hollywood actor salaries or filming permits."
            ),
            answer_criteria=["unable to answer", "insufficient evidence"],
            negative_criteria=["salary", "Tom Cruise", "Leonardo DiCaprio"],
            expected_source_documents=[],
            expected_chunk_ids=[],
            expected_evidence_snippets=[],
            is_refusal_expected=True,
        ),
    ]


def save_benchmark_dataset_to_json(filepath: Path | str) -> None:
    """Export the benchmark dataset to a standalone JSON file."""
    items = get_benchmark_dataset()
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2)


def load_benchmark_dataset_from_json(filepath: Path | str) -> list[BenchmarkItem]:
    """Load benchmark dataset from an external JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)
    return [BenchmarkItem.model_validate(item) for item in raw_items]
