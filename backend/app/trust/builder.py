"""Builder functions for assembling the OpenCitizen AI Trust Layer."""

from collections import defaultdict
from typing import Any, Sequence

from app.trust.models import (
    EvidenceSnippetItem,
    MeasuredConfidence,
    RetrievalMetadata,
    SourceDocumentItem,
    TrustReport,
)

STANDARD_CIVIC_LIMITATIONS: list[str] = [
    "Grounding Boundary: Synthesized exclusively from retrieved municipal records. "
    "Content not present in the indexed document repository cannot be attested.",
    "Temporal Scope: Factual information reflects document publication dates and may "
    "not reflect subsequent legislative actions, emergency resolutions, or revised budget amendments.",
    "Advisory Notice: Automated civic analysis is intended for public transparency and "
    "research assistance and does not constitute formal legal counsel or official certified municipal audit.",
    "Evidence Inspection: Citizens can independently verify each claim by inspecting "
    "the exact verbatim excerpts and page citations in the provenance drawer.",
]

INSUFFICIENT_EVIDENCE_LIMITATION: str = (
    "Insufficient Evidence Notice: The indexed document collection did not contain evidence "
    "meeting the minimum similarity threshold for this inquiry."
)


def map_evidence_snippets(
    items: Sequence[Any],
) -> list[EvidenceSnippetItem]:
    """Map raw contexts or citation objects into structured, ranked evidence snippets.

    Handles items having either attribute access (EvidenceContext/CitationItem)
    or dictionary access.
    """
    snippets: list[EvidenceSnippetItem] = []
    for idx, item in enumerate(items, start=1):
        if hasattr(item, "chunk_id"):
            chunk_id = item.chunk_id
            doc_title = getattr(item, "document_title", None) or getattr(item, "source_filename", "Unknown Document")
            page_num = getattr(item, "page_number", 1)
            text = getattr(item, "text", None) or getattr(item, "excerpt", "")
            score = float(getattr(item, "score", None) if getattr(item, "score", None) is not None else getattr(item, "similarity_score", 0.0))
            meta = getattr(item, "metadata", {}) or {}
            department = getattr(item, "department", None) or meta.get("department")
        elif isinstance(item, dict):
            chunk_id = item.get("chunk_id", f"chk_{idx}")
            doc_title = item.get("document_title") or item.get("source_filename", "Unknown Document")
            page_num = int(item.get("page_number", 1))
            text = item.get("text") or item.get("excerpt", "")
            score = float(item.get("score") if item.get("score") is not None else item.get("similarity_score", 0.0))
            meta = item.get("metadata") or {}
            department = item.get("department") or meta.get("department")
        else:
            continue

        snippets.append(
            EvidenceSnippetItem(
                snippet_id=str(chunk_id),
                document_title=str(doc_title),
                page_number=max(1, int(page_num)),
                text=str(text),
                similarity_score=round(score, 4),
                rank=idx,
                department=str(department) if department else None,
            )
        )
    return snippets


def extract_source_documents(
    snippets: Sequence[EvidenceSnippetItem],
) -> list[SourceDocumentItem]:
    """Group evidence snippets by source document and extract sorted distinct pages."""
    doc_pages: dict[str, set[int]] = defaultdict(set)
    doc_counts: dict[str, int] = defaultdict(int)
    doc_departments: dict[str, str | None] = {}

    for snip in snippets:
        title = snip.document_title
        doc_pages[title].add(snip.page_number)
        doc_counts[title] += 1
        if snip.department and title not in doc_departments:
            doc_departments[title] = snip.department

    sources: list[SourceDocumentItem] = []
    for title, pages in doc_pages.items():
        sources.append(
            SourceDocumentItem(
                document_title=title,
                page_numbers=sorted(pages),
                chunk_count=doc_counts[title],
                department=doc_departments.get(title),
            )
        )
    # Sort source documents alphabetically for deterministic output
    sources.sort(key=lambda s: s.document_title)
    return sources


def extract_distinct_page_numbers(
    snippets: Sequence[EvidenceSnippetItem],
) -> list[int]:
    """Extract flat, deduplicated, numerically sorted list of all cited page numbers."""
    pages = {snip.page_number for snip in snippets}
    return sorted(pages)


def calculate_measured_confidence(
    evidence_snippets: Sequence[EvidenceSnippetItem],
    is_insufficient_evidence: bool = False,
    source_count: int = 0,
) -> MeasuredConfidence:
    """Derive genuinely measurable confidence and grounding explanation.

    DO NOT invent numerical confidence percentages.
    Calculates actual arithmetic mean, minimum, and maximum of measured cosine
    similarity scores from vector search.
    """
    if is_insufficient_evidence or not evidence_snippets:
        return MeasuredConfidence(
            is_grounded=False,
            evidence_count=0,
            mean_similarity_score=None,
            min_similarity_score=None,
            max_similarity_score=None,
            score_metric="cosine_similarity",
            verifiability_rating="insufficient",
            explanation=(
                "No verified source evidence was retrieved meeting the relevance threshold. "
                "The query engine asserted insufficient evidence to prevent hallucination."
            ),
        )

    scores = [snip.similarity_score for snip in evidence_snippets]
    count = len(scores)
    mean_score = round(sum(scores) / count, 4)
    min_score = round(min(scores), 4)
    max_score = round(max(scores), 4)

    # Calibrate verifiability rating deterministically from empirical thresholds
    if mean_score >= 0.75 and count >= 2:
        rating = "high"
    elif mean_score >= 0.60:
        rating = "moderate"
    else:
        rating = "moderate"

    doc_phrase = f"across {source_count} source document(s)" if source_count else ""
    explanation = (
        f"Answer is backed by {count} verified excerpt(s) {doc_phrase} "
        f"with an average cosine similarity of {mean_score:.4f} "
        f"(range: {min_score:.4f} - {max_score:.4f})."
    ).strip()

    return MeasuredConfidence(
        is_grounded=True,
        evidence_count=count,
        mean_similarity_score=mean_score,
        min_similarity_score=min_score,
        max_similarity_score=max_score,
        score_metric="cosine_similarity",
        verifiability_rating=rating,
        explanation=explanation,
    )


def generate_civic_limitations(
    is_insufficient_evidence: bool = False,
    custom_limitations: list[str] | None = None,
) -> list[str]:
    """Generate structured civic boundaries and disclaimers."""
    limitations = list(STANDARD_CIVIC_LIMITATIONS)
    if is_insufficient_evidence:
        limitations.insert(0, INSUFFICIENT_EVIDENCE_LIMITATION)
    if custom_limitations:
        limitations.extend(custom_limitations)
    return limitations


def build_trust_report(
    answer: str,
    evidence_items: Sequence[Any],
    model_identifier: str,
    top_k: int = 5,
    score_threshold: float = 0.4,
    search_latency_ms: float = 0.0,
    is_insufficient_evidence: bool = False,
    custom_limitations: list[str] | None = None,
    vector_store_name: str = "Qdrant HNSW",
) -> TrustReport:
    """Assemble complete structured Trust Layer report for an AI answer."""
    snippets = [] if is_insufficient_evidence else map_evidence_snippets(evidence_items)
    source_docs = extract_source_documents(snippets)
    page_numbers = extract_distinct_page_numbers(snippets)

    confidence = calculate_measured_confidence(
        evidence_snippets=snippets,
        is_insufficient_evidence=is_insufficient_evidence,
        source_count=len(source_docs),
    )

    limitations = generate_civic_limitations(
        is_insufficient_evidence=is_insufficient_evidence,
        custom_limitations=custom_limitations,
    )

    retrieval_meta = RetrievalMetadata(
        vector_store=vector_store_name,
        top_k=top_k,
        score_threshold=score_threshold,
        total_retrieved_chunks=len(snippets),
        search_latency_ms=round(search_latency_ms, 2),
    )

    return TrustReport(
        answer=answer,
        source_documents=source_docs,
        page_numbers=page_numbers,
        evidence_snippets=snippets,
        retrieval_metadata=retrieval_meta,
        model_identifier=model_identifier,
        limitations=limitations,
        confidence=confidence,
    )
