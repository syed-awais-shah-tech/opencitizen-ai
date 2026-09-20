"""Evaluation harness for comparing semantic, lexical, and hybrid document retrieval.

Measures empirical Information Retrieval metrics (Hit@1, Hit@3, Hit@5, MRR,
Precision@5, Recall@5) across a realistic municipal civic document benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.ingestion.models import DocumentChunk
from app.search.embeddings import DeterministicEmbeddingProvider
from app.search.service import VectorSearchService
from app.search.vector_store import QdrantVectorStore
from qdrant_client import QdrantClient


@dataclass
class QueryTestCase:
    """A single evaluation query with ground-truth relevant chunk IDs and query type."""

    query_id: str
    query: str
    query_type: str  # "exact_code", "conceptual", "mixed"
    expected_chunk_ids: list[str]
    description: str


@dataclass
class ModeEvaluationResult:
    """Aggregated evaluation metrics for a specific retrieval mode."""

    mode: str
    query_count: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    precision_at_5: float
    recall_at_5: float
    per_query_ranks: dict[str, int | None] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Full benchmark report comparing multiple retrieval modes."""

    dataset_size_chunks: int
    query_count: int
    results: dict[str, ModeEvaluationResult]
    summary_table: str


def get_evaluation_corpus() -> list[DocumentChunk]:
    """Provide a diverse, realistic 5-document municipal corpus (10 chunks total)."""
    return [
        DocumentChunk(
            chunk_id="chk_budget_01",
            document_id="doc-budget-2024",
            source_filename="city_annual_budget_2024.pdf",
            page_number=1,
            chunk_index=0,
            text=(
                "Under Resolution RES-2024-089, City Council approved the annual municipal budget, "
                "allocating 12.5 million dollars to public park maintenance and civic recreation facilities."
            ),
            character_count=180,
            word_count=23,
            metadata={"fiscal_year": 2024, "code": "RES-2024-089"},
        ),
        DocumentChunk(
            chunk_id="chk_budget_02",
            document_id="doc-budget-2024",
            source_filename="city_annual_budget_2024.pdf",
            page_number=2,
            chunk_index=1,
            text=(
                "The transportation department received emergency capital funding of 45 million dollars "
                "specifically earmarked for critical pothole repairs, roadway resurfacing, and bridge safety overhauls."
            ),
            character_count=200,
            word_count=24,
            metadata={"fiscal_year": 2024, "department": "Transportation"},
        ),
        DocumentChunk(
            chunk_id="chk_health_01",
            document_id="doc-health-2024",
            source_filename="public_health_initiative.pdf",
            page_number=1,
            chunk_index=0,
            text=(
                "Municipal community healthcare clinics will offer free pediatric wellness examinations "
                "and comprehensive routine immunizations for children under age 12 throughout the summer."
            ),
            character_count=187,
            word_count=23,
            metadata={"department": "Public Health", "program": "Pediatric Wellness"},
        ),
        DocumentChunk(
            chunk_id="chk_health_02",
            document_id="doc-health-2024",
            source_filename="public_health_initiative.pdf",
            page_number=2,
            chunk_index=1,
            text=(
                "Adult preventive care programs will provide free blood pressure, cholesterol, and diabetes "
                "screenings at community centers every second Saturday under the Community Wellness Initiative CWI-24."
            ),
            character_count=206,
            word_count=26,
            metadata={"department": "Public Health", "program": "CWI-24"},
        ),
        DocumentChunk(
            chunk_id="chk_zoning_01",
            document_id="doc-zoning-2023",
            source_filename="municipal_zoning_code.pdf",
            page_number=1,
            chunk_index=0,
            text=(
                "Zoning Ordinance ORD-2023-45 regulates commercial structural setbacks, establishing a minimum "
                "building setback of 25 feet from arterial roadways and a maximum roofline height limit of 60 feet."
            ),
            character_count=203,
            word_count=26,
            metadata={"code": "ORD-2023-45", "category": "Commercial Zoning"},
        ),
        DocumentChunk(
            chunk_id="chk_zoning_02",
            document_id="doc-zoning-2023",
            source_filename="municipal_zoning_code.pdf",
            page_number=2,
            chunk_index=1,
            text=(
                "Residential zoning district R-1 permits single-family detached dwellings with a maximum "
                "residential building height restriction of 35 feet and mandatory rear yard depth of 20 feet."
            ),
            character_count=192,
            word_count=25,
            metadata={"district": "R-1", "category": "Residential Zoning"},
        ),
        DocumentChunk(
            chunk_id="chk_transit_01",
            document_id="doc-transit-2024",
            source_filename="transit_electrification_plan.pdf",
            page_number=1,
            chunk_index=0,
            text=(
                "Under procurement contract CTR-2023-142, the Metropolitan Transit Authority authorized "
                "the acquisition of thirty zero-emission battery-electric heavy-duty transit buses."
            ),
            character_count=185,
            word_count=21,
            metadata={"contract": "CTR-2023-142", "agency": "MTA"},
        ),
        DocumentChunk(
            chunk_id="chk_transit_02",
            document_id="doc-transit-2024",
            source_filename="transit_electrification_plan.pdf",
            page_number=2,
            chunk_index=1,
            text=(
                "Full route electrification for urban transit Line-42 is slated for completion in Q3 2025, "
                "including overhead pantograph rapid-charging stations at the East Terminus."
            ),
            character_count=177,
            word_count=24,
            metadata={"route": "Line-42", "agency": "MTA"},
        ),
        DocumentChunk(
            chunk_id="chk_water_01",
            document_id="doc-water-2024",
            source_filename="drinking_water_quality_report.pdf",
            page_number=1,
            chunk_index=0,
            text=(
                "In compliance with EPA-502.2 regulatory guidelines, quarterly chemical analyses detected zero "
                "trace lead or copper contamination exceeding federal action thresholds across all municipal taps."
            ),
            character_count=207,
            word_count=26,
            metadata={"standard": "EPA-502.2", "compliance": "EPA"},
        ),
        DocumentChunk(
            chunk_id="chk_water_02",
            document_id="doc-water-2024",
            source_filename="drinking_water_quality_report.pdf",
            page_number=2,
            chunk_index=1,
            text=(
                "Continuous automated turbidity sensors and biological monitors at the North Reservoir confirmed "
                "drinking water clarity and purity consistently exceeded state environmental benchmarks."
            ),
            character_count=197,
            word_count=23,
            metadata={"facility": "North Reservoir", "compliance": "State"},
        ),
    ]


def get_evaluation_queries() -> list[QueryTestCase]:
    """Provide 10 representative civic test queries across exact codes, conceptual, and mixed types."""
    return [
        QueryTestCase(
            query_id="Q1",
            query="Resolution RES-2024-089 park infrastructure allocation",
            query_type="exact_code",
            expected_chunk_ids=["chk_budget_01"],
            description="Exact resolution code query for budget allocation",
        ),
        QueryTestCase(
            query_id="Q2",
            query="CTR-2023-142 electric bus procurement contract",
            query_type="exact_code",
            expected_chunk_ids=["chk_transit_01"],
            description="Exact contract code query for transit bus acquisition",
        ),
        QueryTestCase(
            query_id="Q3",
            query="ORD-2023-45 commercial setback height limits",
            query_type="exact_code",
            expected_chunk_ids=["chk_zoning_01"],
            description="Exact ordinance code query for commercial setback",
        ),
        QueryTestCase(
            query_id="Q4",
            query="EPA-502.2 drinking water lead testing compliance",
            query_type="exact_code",
            expected_chunk_ids=["chk_water_01"],
            description="Exact standard compliance query for lead testing",
        ),
        QueryTestCase(
            query_id="Q5",
            query="children healthcare free immunizations",
            query_type="conceptual",
            expected_chunk_ids=["chk_health_01"],
            description="Conceptual natural language query for pediatric vaccines",
        ),
        QueryTestCase(
            query_id="Q6",
            query="road repairs and bridge pothole emergency funding",
            query_type="conceptual",
            expected_chunk_ids=["chk_budget_02"],
            description="Conceptual natural language query for highway maintenance",
        ),
        QueryTestCase(
            query_id="Q7",
            query="reservoir water clarity purity contaminant monitoring",
            query_type="conceptual",
            expected_chunk_ids=["chk_water_02"],
            description="Conceptual natural language query for reservoir sensors",
        ),
        QueryTestCase(
            query_id="Q8",
            query="transit electrification rapid charging for Line-42",
            query_type="mixed",
            expected_chunk_ids=["chk_transit_02"],
            description="Mixed conceptual and identifier query for transit route",
        ),
        QueryTestCase(
            query_id="Q9",
            query="residential zoning single family building height restrictions",
            query_type="mixed",
            expected_chunk_ids=["chk_zoning_02"],
            description="Mixed zoning conceptual and district code query",
        ),
        QueryTestCase(
            query_id="Q10",
            query="preventive care cholesterol blood pressure Community Wellness Initiative",
            query_type="mixed",
            expected_chunk_ids=["chk_health_02"],
            description="Mixed health program title and symptom screening query",
        ),
    ]


def evaluate_retrieval(
    service: VectorSearchService,
    modes: list[str] | None = None,
    top_k: int = 5,
) -> EvaluationReport:
    """Run empirical retrieval evaluation comparing semantic, lexical, and hybrid modes.

    Args:
        service: An initialized and populated VectorSearchService
        modes: Modes to compare (defaults to ['semantic', 'lexical', 'hybrid'])
        top_k: Number of retrieved candidates per query (default 5)

    Returns:
        EvaluationReport containing metrics and markdown comparison table
    """
    if modes is None:
        modes = ["semantic", "lexical", "hybrid"]

    corpus = get_evaluation_corpus()
    queries = get_evaluation_queries()

    # Ensure corpus is indexed in service
    service.index_chunks(corpus)

    results: dict[str, ModeEvaluationResult] = {}

    for mode in modes:
        hits_1 = 0
        hits_3 = 0
        hits_5 = 0
        reciprocal_ranks: list[float] = []
        precisions_5: list[float] = []
        recalls_5: list[float] = []
        per_query_ranks: dict[str, int | None] = {}

        for test in queries:
            search_hits = service.search(
                query=test.query,
                top_k=top_k,
                mode=mode,
            )

            retrieved_chunk_ids = [hit.chunk_id for hit in search_hits]

            # Find rank of first relevant chunk (1-indexed)
            first_rank: int | None = None
            for idx, cid in enumerate(retrieved_chunk_ids):
                if cid in test.expected_chunk_ids:
                    first_rank = idx + 1
                    break

            per_query_ranks[test.query_id] = first_rank

            if first_rank is not None:
                if first_rank == 1:
                    hits_1 += 1
                if first_rank <= 3:
                    hits_3 += 1
                if first_rank <= 5:
                    hits_5 += 1
                reciprocal_ranks.append(1.0 / first_rank)
            else:
                reciprocal_ranks.append(0.0)

            # Calculate Precision@5 and Recall@5
            relevant_retrieved = sum(
                1 for cid in retrieved_chunk_ids if cid in test.expected_chunk_ids
            )
            precisions_5.append(
                relevant_retrieved / max(len(retrieved_chunk_ids), 1)
            )
            recalls_5.append(
                relevant_retrieved / max(len(test.expected_chunk_ids), 1)
            )

        n = len(queries)
        mode_res = ModeEvaluationResult(
            mode=mode,
            query_count=n,
            hit_at_1=round(hits_1 / n, 4),
            hit_at_3=round(hits_3 / n, 4),
            hit_at_5=round(hits_5 / n, 4),
            mrr=round(sum(reciprocal_ranks) / n, 4),
            precision_at_5=round(sum(precisions_5) / n, 4),
            recall_at_5=round(sum(recalls_5) / n, 4),
            per_query_ranks=per_query_ranks,
        )
        results[mode] = mode_res

    # Build summary markdown table
    header = "| Metric | Semantic (Original) | Lexical (BM25) | Hybrid (RRF) |"
    divider = "|:---|:---:|:---:|:---:|"
    rows = [
        f"| Hit@1 | {results.get('semantic', ModeEvaluationResult('semantic', 0, 0, 0, 0, 0, 0, 0)).hit_at_1:.1%} | {results.get('lexical', ModeEvaluationResult('lexical', 0, 0, 0, 0, 0, 0, 0)).hit_at_1:.1%} | {results.get('hybrid', ModeEvaluationResult('hybrid', 0, 0, 0, 0, 0, 0, 0)).hit_at_1:.1%} |",
        f"| Hit@3 | {results.get('semantic', ModeEvaluationResult('semantic', 0, 0, 0, 0, 0, 0, 0)).hit_at_3:.1%} | {results.get('lexical', ModeEvaluationResult('lexical', 0, 0, 0, 0, 0, 0, 0)).hit_at_3:.1%} | {results.get('hybrid', ModeEvaluationResult('hybrid', 0, 0, 0, 0, 0, 0, 0)).hit_at_3:.1%} |",
        f"| Hit@5 | {results.get('semantic', ModeEvaluationResult('semantic', 0, 0, 0, 0, 0, 0, 0)).hit_at_5:.1%} | {results.get('lexical', ModeEvaluationResult('lexical', 0, 0, 0, 0, 0, 0, 0)).hit_at_5:.1%} | {results.get('hybrid', ModeEvaluationResult('hybrid', 0, 0, 0, 0, 0, 0, 0)).hit_at_5:.1%} |",
        f"| MRR (Mean Reciprocal Rank) | {results.get('semantic', ModeEvaluationResult('semantic', 0, 0, 0, 0, 0, 0, 0)).mrr:.4f} | {results.get('lexical', ModeEvaluationResult('lexical', 0, 0, 0, 0, 0, 0, 0)).mrr:.4f} | {results.get('hybrid', ModeEvaluationResult('hybrid', 0, 0, 0, 0, 0, 0, 0)).mrr:.4f} |",
        f"| Recall@5 | {results.get('semantic', ModeEvaluationResult('semantic', 0, 0, 0, 0, 0, 0, 0)).recall_at_5:.1%} | {results.get('lexical', ModeEvaluationResult('lexical', 0, 0, 0, 0, 0, 0, 0)).recall_at_5:.1%} | {results.get('hybrid', ModeEvaluationResult('hybrid', 0, 0, 0, 0, 0, 0, 0)).recall_at_5:.1%} |",
    ]
    summary_table = "\n".join([header, divider] + rows)

    return EvaluationReport(
        dataset_size_chunks=len(corpus),
        query_count=len(queries),
        results=results,
        summary_table=summary_table,
    )


def run_standalone_evaluation() -> EvaluationReport:
    """Convenience runner constructing isolated in-memory service and executing evaluation."""
    qdrant = QdrantClient(location=":memory:")
    embed_provider = DeterministicEmbeddingProvider(dimension=64)
    store = QdrantVectorStore(
        client=qdrant,
        default_collection="eval_benchmark_collection",
        dimension=64,
    )
    service = VectorSearchService(
        vector_store=store,
        embedding_provider=embed_provider,
        collection_name="eval_benchmark_collection",
    )
    return evaluate_retrieval(service)


if __name__ == "__main__":
    report = run_standalone_evaluation()
    print("=== OpenCitizen AI Retrieval Evaluation Benchmark ===")
    print(report.summary_table)
    print("\nPer-Query Ranks (1-indexed, None=not retrieved in top 5):")
    queries = get_evaluation_queries()
    for q in queries:
        sem_rank = report.results["semantic"].per_query_ranks.get(q.query_id)
        lex_rank = report.results["lexical"].per_query_ranks.get(q.query_id)
        hyb_rank = report.results["hybrid"].per_query_ranks.get(q.query_id)
        print(
            f"  {q.query_id} [{q.query_type}]: Semantic rank={sem_rank}, Lexical rank={lex_rank}, Hybrid rank={hyb_rank} | Query: '{q.query}'"
        )
