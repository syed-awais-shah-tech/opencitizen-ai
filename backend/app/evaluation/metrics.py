"""Metric calculation algorithms for OpenCitizen AI evaluation framework.

Implements rigorous, objective measurement of:
- Retrieval Success & Recall
- Citation Correctness, Precision, and Grounding
- Answer Correctness (Criteria Match Rate and Token F1)
- Unsupported Claims Detection
"""

from __future__ import annotations

import re
from collections import Counter
from app.evaluation.models import BenchmarkItem
from app.schemas.query import CitationItem
from app.search.models import VectorSearchResult

# Regex for extracting numerical/quantitative assertions and alphanumeric municipal codes
QUANTITATIVE_PATTERN = re.compile(r"\b(?:\$?\d+(?:\.\d+)?(?:%|\s*(?:million|billion|thousand|dollars|feet|meters|buses|hours))?)\b", re.IGNORECASE)
IDENTIFIER_PATTERN = re.compile(r"\b[A-Za-z]{2,}(?:[-_][A-Za-z0-9]+)+\b")


def tokenize_words(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*\b", text.lower())


def evaluate_retrieval_success(
    retrieved_chunks: list[VectorSearchResult],
    item: BenchmarkItem,
) -> tuple[bool, float, float]:
    """Calculate retrieval success, chunk recall, and document precision.

    Returns:
        (retrieval_success: bool, chunk_recall: float, document_precision: float)
    """
    if item.is_refusal_expected:
        # For refusal cases, success means no false-positive hallucinations
        # If no chunks were retrieved or low relevance, success is True
        return True, 1.0, 1.0

    if not retrieved_chunks:
        return False, 0.0, 0.0

    retrieved_chunk_ids = {c.chunk_id for c in retrieved_chunks}
    retrieved_docs = {c.source_filename for c in retrieved_chunks}

    expected_chunk_ids = set(item.expected_chunk_ids)
    expected_docs = set(item.expected_source_documents)

    # Chunk Recall
    matched_chunks = retrieved_chunk_ids & expected_chunk_ids
    chunk_recall = len(matched_chunks) / max(len(expected_chunk_ids), 1)

    # Document Precision
    matched_docs = retrieved_docs & expected_docs
    document_precision = len(matched_docs) / max(len(retrieved_docs), 1)

    # Retrieval Success is True if at least one expected chunk or document was found
    retrieval_success = len(matched_chunks) > 0 or len(matched_docs) > 0

    return (
        retrieval_success,
        round(chunk_recall, 4),
        round(document_precision, 4),
    )


def evaluate_citation_correctness(
    citations: list[CitationItem],
    retrieved_chunks: list[VectorSearchResult],
    item: BenchmarkItem,
) -> tuple[float, float, float]:
    """Evaluate citation accuracy, precision, and alignment with source evidence.

    Returns:
        (citation_score: float, citation_precision: float, citation_recall: float)
    """
    if item.is_refusal_expected:
        # Refusal cases should return zero citations
        if not citations:
            return 1.0, 1.0, 1.0
        return 0.0, 0.0, 0.0

    if not citations:
        return 0.0, 0.0, 0.0

    retrieved_texts = [c.original_text for c in retrieved_chunks]
    expected_docs = set(item.expected_source_documents)

    valid_citations = 0
    cited_expected_docs: set[str] = set()

    for cite in citations:
        doc_matches = cite.document_title in expected_docs
        page_valid = cite.page_number >= 1

        # Check citation excerpt is non-fabricated (actually exists in retrieved context)
        excerpt_grounded = False
        if cite.excerpt and cite.excerpt.strip():
            excerpt_lower = cite.excerpt.strip().lower()
            for r_text in retrieved_texts:
                if excerpt_lower in r_text.lower() or r_text.lower() in excerpt_lower:
                    excerpt_grounded = True
                    break
        else:
            excerpt_grounded = True

        if doc_matches and page_valid and excerpt_grounded:
            valid_citations += 1
            cited_expected_docs.add(cite.document_title)

    citation_precision = valid_citations / max(len(citations), 1)
    citation_recall = len(cited_expected_docs) / max(len(expected_docs), 1)

    # Balanced harmonic citation score
    citation_score = round(0.5 * citation_precision + 0.5 * citation_recall, 4)

    return (
        citation_score,
        round(citation_precision, 4),
        round(citation_recall, 4),
    )


def compute_token_f1(predicted: str, ground_truth: str) -> float:
    """Compute token-level precision, recall, and F1 between two strings."""
    pred_tokens = tokenize_words(predicted)
    gold_tokens = tokenize_words(ground_truth)

    if not pred_tokens or not gold_tokens:
        return 1.0 if pred_tokens == gold_tokens else 0.0

    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())

    if num_same == 0:
        return 0.0

    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return round(f1, 4)


def evaluate_answer_correctness(
    actual_answer: str,
    is_insufficient_evidence: bool,
    item: BenchmarkItem,
) -> tuple[float, float, float]:
    """Calculate answer correctness against expected criteria and gold standard text.

    Returns:
        (answer_correctness: float, criteria_match_rate: float, token_f1: float)
    """
    answer_lower = actual_answer.lower()

    if item.is_refusal_expected:
        refusal_phrases = [
            "unable to answer",
            "insufficient evidence",
            "not found",
            "no evidence",
            "not mentioned",
            "cannot answer",
        ]
        has_refusal = is_insufficient_evidence or any(
            p in answer_lower for p in refusal_phrases
        )
        if has_refusal:
            return 1.0, 1.0, 1.0
        return 0.0, 0.0, 0.0

    if is_insufficient_evidence or not actual_answer.strip():
        return 0.0, 0.0, 0.0

    # 1. Answer Criteria Match Rate
    criteria_matches = 0
    if item.answer_criteria:
        for crit in item.answer_criteria:
            if crit.lower() in answer_lower:
                criteria_matches += 1
        criteria_match_rate = criteria_matches / len(item.answer_criteria)
    else:
        criteria_match_rate = 1.0

    # 2. Negative criteria penalty (hallucination penalty)
    if item.negative_criteria:
        for neg in item.negative_criteria:
            if neg.lower() in answer_lower:
                criteria_match_rate = max(0.0, criteria_match_rate - 0.5)

    # 3. Token F1 against expected answer
    token_f1 = compute_token_f1(actual_answer, item.expected_answer)

    # Combined answer correctness score: 70% criteria match, 30% lexical overlap
    answer_correctness = round(0.7 * criteria_match_rate + 0.3 * token_f1, 4)

    return (
        answer_correctness,
        round(criteria_match_rate, 4),
        token_f1,
    )


def detect_unsupported_claims(
    actual_answer: str,
    retrieved_chunks: list[VectorSearchResult],
    is_insufficient_evidence: bool,
) -> tuple[int, bool, list[str]]:
    """Detect factual, numerical, or identifier claims in the answer not supported by retrieved evidence.

    Returns:
        (unsupported_count: int, has_unsupported: bool, unsupported_entities: list[str])
    """
    if is_insufficient_evidence or not actual_answer.strip():
        return 0, False, []

    # Strip citation metadata footers (e.g. [Source: doc.pdf, Page: 1]) before inspecting claims
    body_text = re.sub(r"\[Source:[^\]]+\]", "", actual_answer, flags=re.IGNORECASE)

    # Combined evidence contains all chunk text and source filenames
    combined_evidence = " ".join(
        f"{c.source_filename} {c.original_text}" for c in retrieved_chunks
    ).lower()

    unsupported_entities: list[str] = []

    # 1. Extract quantitative entities (numbers, dollar figures, percentages)
    quant_candidates = QUANTITATIVE_PATTERN.findall(body_text)
    for quant in quant_candidates:
        cleaned = quant.strip()
        # Discard generic small digits like 1, 2, 3, 4 if standalone enumeration
        if cleaned.isdigit() and int(cleaned) < 5:
            continue
        # Check if the number appears anywhere in the evidence
        digits_only = re.findall(r"\d+(?:\.\d+)?", cleaned)
        for num in digits_only:
            if num not in combined_evidence:
                unsupported_entities.append(f"Number '{cleaned}' absent from evidence")
                break

    # 2. Extract municipal codes and uppercase identifiers
    id_candidates = IDENTIFIER_PATTERN.findall(body_text)
    for ident in id_candidates:
        if ident.lower() not in combined_evidence:
            unsupported_entities.append(f"Identifier '{ident}' absent from evidence")

    unsupported_count = len(unsupported_entities)
    has_unsupported = unsupported_count > 0

    return unsupported_count, has_unsupported, unsupported_entities
