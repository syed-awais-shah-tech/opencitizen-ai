# Extending Retrieval Strategies: Hybrid Search, Reranking & Vector Stores

OpenCitizen AI implements a hybrid document retrieval architecture combining dense vector similarity with lexical keyword search (BM25), merged and prioritized through Reciprocal Rank Fusion (RRF).

This guide describes how the retrieval pipeline operates and how to extend it with custom vector stores, alternative rerankers, or specialized domain retrievers.

---

## 1. Architectural Retrieval Pipeline

When a user submits a question across municipal records or uploaded policy documents, the `VectorSearchService` in `backend/app/search/service.py` coordinates:

```
                            User Query
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
       ┌───────────────────┐         ┌───────────────────┐
       │   Dense Vector    │         │   Lexical BM25    │
       │  Semantic Search  │         │  Inverted Index   │
       │     (Qdrant)      │         │  (Keyword Match)  │
       └─────────┬─────────┘         └─────────┬─────────┘
                 │ Top-K Candidates            │ Top-K Candidates
                 └──────────────┬──────────────┘
                                ▼
                 ┌─────────────────────────────┐
                 │    Reciprocal Rank Fusion   │
                 │      (RRF Reranker)         │
                 └──────────────┬──────────────┘
                                ▼
                 Top-K Grounded Evidence Chunks
```

### Preservation Invariant
Every chunk candidate preserves its metadata through all stages:
- `chunk_id`: Unique chunk identifier
- `document_id`: Parent document identifier
- `page_number`: 1-indexed document page
- `source_filename`: Original uploaded filename
- `document_title`: Human-readable document title
- `text`: Complete text content of the chunk

---

## 2. Implementing an Alternative Vector Store

All vector stores implement the `BaseVectorStore` abstract class in `backend/app/search/vector_store.py`:

```python
class BaseVectorStore(ABC):
    @abstractmethod
    def create_collection(self, collection_name: str) -> None:
        """Create or initialize vector collection."""

    @abstractmethod
    def index_chunks(
        self,
        chunks: Sequence[DocumentChunk],
        vectors: Sequence[Sequence[float]],
        collection_name: str | None = None,
    ) -> VectorIndexResult:
        """Store chunk vectors and metadata payload."""

    @abstractmethod
    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        score_threshold: float | None = None,
        filter_document_id: str | None = None,
        collection_name: str | None = None,
    ) -> list[VectorSearchResult]:
        """Search top-k nearest neighbors."""

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Delete collection."""
```

### Example: Implementing a PGVector Store (PostgreSQL vector extension)

```python
from typing import Sequence
from app.search.vector_store import BaseVectorStore
from app.search.models import VectorSearchResult, VectorIndexResult
from app.ingestion.models import DocumentChunk


class PGVectorStore(BaseVectorStore):
    def __init__(self, db_url: str, dimension: int = 768):
        self.db_url = db_url
        self.dimension = dimension

    def create_collection(self, collection_name: str) -> None:
        # CREATE EXTENSION IF NOT EXISTS vector;
        # CREATE TABLE IF NOT EXISTS ... (id TEXT, embedding vector(768), metadata JSONB);
        ...

    def index_chunks(self, chunks: Sequence[DocumentChunk], vectors: Sequence[Sequence[float]], collection_name: str | None = None) -> VectorIndexResult:
        ...

    def search(self, query_vector: Sequence[float], top_k: int = 5, score_threshold: float | None = None, filter_document_id: str | None = None, collection_name: str | None = None) -> list[VectorSearchResult]:
        # SELECT chunk_id, document_id, 1 - (embedding <=> query_vector) AS score FROM ... ORDER BY embedding <=> query_vector LIMIT top_k;
        ...
```

---

## 3. Customizing the Reranking Strategy

The default reranker uses Reciprocal Rank Fusion (`ReciprocalRankFusionReranker` in `backend/app/search/reranker.py`):

$$RRF\_Score(d) = \sum_{r \in R} \frac{1}{k + rank_r(d)}$$

Where:
- $k$ is the smoothing constant (default: `60`)
- $rank_r(d)$ is the 1-based rank of document $d$ in result list $r$

### Adding a Cross-Encoder Reranker (e.g. Cohere or BGE Reranker)

You can subclass or replace the reranker by implementing the reranking protocol:

```python
class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        candidates: list[VectorSearchResult],
        top_k: int = 5,
    ) -> list[VectorSearchResult]:
        if not candidates:
            return []

        pairs = [[query, c.text] for c in candidates]
        scores = self.model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate.score = float(score)

        return sorted(candidates, key=lambda c: c.score, reverse=True)[:top_k]
```

Pass the custom reranker into `VectorSearchService(reranker=CrossEncoderReranker())`.

---

## 4. Evaluating Retrieval Quality

Before merging a new retrieval or reranking strategy, benchmark its performance against the existing baseline using the built-in evaluation framework:

```bash
pytest backend/tests/test_evaluation_framework.py -v
```

Compare metrics across:
- **Retrieval Success Rate**: Percentage of questions where relevant ground-truth chunks appear in top-k.
- **Mean Reciprocal Rank (MRR)**: Position of the first relevant passage.
- **Latency (ms)**: Computation overhead introduced by the new strategy.

Document your benchmark findings in your pull request!
