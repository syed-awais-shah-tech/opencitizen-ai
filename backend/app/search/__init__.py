"""OpenCitizen AI search, vector, and lexical retrieval module."""

from app.search.embeddings import (
    BaseEmbeddingProvider,
    DeterministicEmbeddingProvider,
    get_embedding_provider,
)
from app.search.lexical import BM25Index, tokenize
from app.search.models import (
    SearchQuery,
    VectorIndexResult,
    VectorSearchResult,
)
from app.search.reranker import ReciprocalRankFusionReranker
from app.search.service import VectorSearchService
from app.search.vector_store import (
    BaseVectorStore,
    QdrantVectorStore,
)

__all__ = [
    "BM25Index",
    "BaseEmbeddingProvider",
    "BaseVectorStore",
    "DeterministicEmbeddingProvider",
    "QdrantVectorStore",
    "ReciprocalRankFusionReranker",
    "SearchQuery",
    "VectorIndexResult",
    "VectorSearchResult",
    "VectorSearchService",
    "get_embedding_provider",
    "tokenize",
]
