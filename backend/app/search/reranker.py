"""Reciprocal Rank Fusion (RRF) and hybrid candidate reranking.

Merges candidate document chunks from dual retrieval channels (semantic vector
search and lexical BM25 retrieval) while rigorously preserving chunk provenance
and source metadata.
"""

from __future__ import annotations

from typing import Any, Optional
from app.search.models import VectorSearchResult


class ReciprocalRankFusionReranker:
    """Combines and reranks search results using Reciprocal Rank Fusion (RRF).

    RRF formula:
        RRF_score(d) = sum_{m in {semantic, lexical}} (w_m / (k + rank_m(d)))

    Where:
        - k: smoothing constant (standard k=60 to avoid excessive bias toward top ranks)
        - rank_m(d): 1-indexed position of document d in the results of channel m
        - w_m: channel weight factor (e.g. w_sem=0.6, w_lex=0.4)
    """

    def __init__(
        self,
        rrf_k: int = 60,
        weight_semantic: float = 0.6,
        weight_lexical: float = 0.4,
    ):
        self.rrf_k = rrf_k
        self.weight_semantic = weight_semantic
        self.weight_lexical = weight_lexical

    def rerank(
        self,
        semantic_results: list[VectorSearchResult],
        lexical_results: list[VectorSearchResult],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> list[VectorSearchResult]:
        """Merge and rerank candidates from semantic and lexical searches.

        Preserves all source metadata, page citations, and provenance records.
        """
        # Collect candidate pool indexed by chunk_id
        candidates: dict[str, VectorSearchResult] = {}
        semantic_ranks: dict[str, int] = {}
        semantic_scores: dict[str, float] = {}
        lexical_ranks: dict[str, int] = {}
        lexical_scores: dict[str, float] = {}

        # 1. Process Semantic candidates
        for rank_0, res in enumerate(semantic_results):
            cid = res.chunk_id
            candidates[cid] = res
            semantic_ranks[cid] = rank_0 + 1
            semantic_scores[cid] = res.score

        # 2. Process Lexical candidates
        max_bm25 = max([r.score for r in lexical_results], default=1.0)
        if max_bm25 <= 0.0:
            max_bm25 = 1.0

        for rank_0, res in enumerate(lexical_results):
            cid = res.chunk_id
            if cid not in candidates:
                candidates[cid] = res
            lexical_ranks[cid] = rank_0 + 1
            lexical_scores[cid] = res.score

        # 3. Calculate RRF and calibrated normalized scores for all candidates
        scored_candidates: list[tuple[float, float, str, VectorSearchResult]] = []

        for cid, candidate in candidates.items():
            rrf_score = 0.0
            sem_norm = 0.0
            lex_norm = 0.0

            if cid in semantic_ranks:
                rrf_score += self.weight_semantic / (self.rrf_k + semantic_ranks[cid])
                sem_norm = max(0.0, semantic_scores[cid])

            if cid in lexical_ranks:
                rrf_score += self.weight_lexical / (self.rrf_k + lexical_ranks[cid])
                lex_norm = max(0.0, lexical_scores[cid]) / max_bm25

            # Calibrated score in [0.0, 1.0] for downstream thresholding
            if cid in semantic_ranks and cid in lexical_ranks:
                calibrated_score = (self.weight_semantic * sem_norm) + (self.weight_lexical * lex_norm)
                retrieval_method = "hybrid"
            elif cid in semantic_ranks:
                calibrated_score = sem_norm * self.weight_semantic
                retrieval_method = "semantic_only"
            else:
                calibrated_score = lex_norm * self.weight_lexical
                retrieval_method = "lexical_only"

            # Filter out pure noise candidates with zero/negative similarity and no lexical match
            if cid in semantic_ranks and cid not in lexical_ranks and semantic_scores[cid] <= 0.0:
                continue

            # Optional threshold filter
            if score_threshold is not None and calibrated_score < score_threshold:
                continue

            # Enrich metadata with detailed ranking provenance
            metadata = dict(candidate.metadata) if candidate.metadata else {}
            metadata["retrieval_method"] = retrieval_method
            metadata["retrieval_meta"] = {
                "method": retrieval_method,
                "rrf_score": round(rrf_score, 6),
                "calibrated_score": round(calibrated_score, 4),
                "semantic_rank": semantic_ranks.get(cid),
                "lexical_rank": lexical_ranks.get(cid),
                "semantic_score": round(semantic_scores[cid], 4) if cid in semantic_scores else None,
                "lexical_score": round(lexical_scores[cid], 4) if cid in lexical_scores else None,
            }

            merged_result = VectorSearchResult(
                chunk_id=candidate.chunk_id,
                document_id=candidate.document_id,
                page_number=candidate.page_number,
                source_filename=candidate.source_filename,
                original_text=candidate.original_text,
                score=round(calibrated_score, 4),
                metadata=metadata,
            )

            scored_candidates.append((rrf_score, calibrated_score, cid, merged_result))

        # Sort primarily by RRF score descending, then by calibrated score
        scored_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

        return [item[3] for item in scored_candidates[:top_k]]
