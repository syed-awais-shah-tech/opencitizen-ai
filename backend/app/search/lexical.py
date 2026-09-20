"""Lexical (keyword-based) document retrieval using Okapi BM25.

Provides exact token matching for alphanumeric codes, resolution numbers,
acronyms, proper nouns, and municipal legal terms where pure semantic
embeddings may suffer from vocabulary mismatch or vector dilution.
"""

from __future__ import annotations

import math
import re
import threading
from collections import Counter
from collections.abc import Sequence
from typing import Any, Optional

from app.ingestion.models import DocumentChunk
from app.search.models import VectorSearchResult

# Standard English stopwords to filter unless query consists solely of stopwords
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves",
}

# Regex to capture alphanumeric tokens while preserving hyphens and underscores within words
# e.g., '2024-089', 'CTR-2023-142', 'PRJ-011', 'CEAP'
TOKEN_PATTERN = re.compile(r"\b[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*\b")


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    """Tokenize input text into lowercase alphanumeric tokens, preserving identifiers."""
    if not text:
        return []
    tokens = [t.lower() for t in TOKEN_PATTERN.findall(text)]
    if remove_stopwords:
        filtered = [t for t in tokens if t not in STOPWORDS]
        # If all tokens were stopwords, preserve original tokens
        return filtered if filtered else tokens
    return tokens


class BM25Index:
    """In-memory Okapi BM25 lexical index supporting incremental indexing and provenance preservation."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._lock = threading.RLock()

        # Inverted index: term -> {chunk_id: term_frequency}
        self.inverted_index: dict[str, dict[str, int]] = {}
        # Document length: chunk_id -> token_count
        self.doc_lengths: dict[str, int] = {}
        # Stored chunk metadata: chunk_id -> DocumentChunk
        self.chunks: dict[str, DocumentChunk] = {}
        # Total number of indexed chunks
        self.total_docs: int = 0
        # Average document length across the corpus
        self.avg_doc_len: float = 0.0

    def _recalculate_stats(self) -> None:
        """Update corpus statistics (total_docs, avg_doc_len)."""
        self.total_docs = len(self.chunks)
        if self.total_docs > 0:
            self.avg_doc_len = sum(self.doc_lengths.values()) / self.total_docs
        else:
            self.avg_doc_len = 0.0

    def index_chunks(self, chunks: Sequence[DocumentChunk]) -> int:
        """Index a batch of DocumentChunks into the BM25 inverted index."""
        with self._lock:
            indexed_count = 0
            for chunk in chunks:
                tokens = tokenize(chunk.text)
                term_counts = Counter(tokens)

                chunk_id = chunk.chunk_id
                self.chunks[chunk_id] = chunk
                self.doc_lengths[chunk_id] = len(tokens)

                for term, count in term_counts.items():
                    if term not in self.inverted_index:
                        self.inverted_index[term] = {}
                    self.inverted_index[term][chunk_id] = count

                indexed_count += 1

            self._recalculate_stats()
            return indexed_count

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_document_id: Optional[str] = None,
    ) -> list[VectorSearchResult]:
        """Perform lexical BM25 retrieval over indexed chunks.

        Returns ranked list of VectorSearchResult with raw BM25 scores.
        """
        with self._lock:
            if not query or not query.strip() or self.total_docs == 0:
                return []

            query_tokens = tokenize(query)
            if not query_tokens:
                return []

            # Calculate BM25 score for each candidate document
            scores: dict[str, float] = {}

            for term in query_tokens:
                if term not in self.inverted_index:
                    continue

                postings = self.inverted_index[term]
                doc_freq = len(postings)
                # Standard Okapi BM25 IDF with smoothing
                idf = math.log(1.0 + (self.total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

                for chunk_id, tf in postings.items():
                    chunk = self.chunks[chunk_id]
                    if filter_document_id and chunk.document_id != filter_document_id:
                        continue

                    doc_len = self.doc_lengths.get(chunk_id, 1)
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(self.avg_doc_len, 1.0)))
                    term_score = idf * ((tf * (self.k1 + 1.0)) / max(denom, 1e-6))

                    scores[chunk_id] = scores.get(chunk_id, 0.0) + term_score

            if not scores:
                return []

            # Sort descending by BM25 score
            sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

            results = []
            for chunk_id, score in sorted_candidates:
                chunk = self.chunks[chunk_id]
                metadata = dict(chunk.metadata) if chunk.metadata else {}
                metadata["retrieval_method"] = "lexical"
                metadata["lexical_raw_score"] = round(score, 4)

                results.append(
                    VectorSearchResult(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        page_number=chunk.page_number,
                        source_filename=chunk.source_filename,
                        original_text=chunk.text,
                        score=round(score, 4),
                        metadata=metadata,
                    )
                )

            return results

    def delete_document(self, document_id: str) -> int:
        """Remove all indexed chunks belonging to a document ID."""
        with self._lock:
            chunks_to_remove = [
                cid for cid, chk in self.chunks.items() if chk.document_id == document_id
            ]

            for cid in chunks_to_remove:
                del self.chunks[cid]
                if cid in self.doc_lengths:
                    del self.doc_lengths[cid]

                # Remove from inverted index
                for term, postings in list(self.inverted_index.items()):
                    if cid in postings:
                        del postings[cid]
                    if not postings:
                        del self.inverted_index[term]

            self._recalculate_stats()
            return len(chunks_to_remove)

    def count(self) -> int:
        """Return total number of indexed chunks."""
        with self._lock:
            return self.total_docs

    def clear(self) -> None:
        """Reset the BM25 index."""
        with self._lock:
            self.inverted_index.clear()
            self.doc_lengths.clear()
            self.chunks.clear()
            self.total_docs = 0
            self.avg_doc_len = 0.0
