"""Embedding provider abstraction and implementations.

Allows swappable embedding providers (e.g. deterministic local, Gemini API, or custom models)
without coupling vector storage or application logic to any specific embedding runtime.
"""

import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import ClassVar

from app.core.config import settings


class BaseEmbeddingProvider(ABC):
    """Abstract base class establishing the contract for embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the vector embeddings produced."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifying name of the embedding model."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate a normalized embedding vector for a single text string."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate normalized embedding vectors for multiple text strings."""


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic, lightweight embedding provider for local development, CI, and testing.

    Projects text tokens and n-grams into a fixed-dimensional unit hypersphere.
    Semantically overlapping texts produce high cosine similarity, while unrelated
    texts produce low similarity, guaranteeing reproducible vector search without
    requiring external network calls or heavy multi-gigabyte models.
    """

    DEFAULT_DIMENSION: ClassVar[int] = 384
    DEFAULT_MODEL_NAME: ClassVar[str] = "deterministic-hashing-384"

    def __init__(
        self,
        dimension: int = DEFAULT_DIMENSION,
        model_name: str = DEFAULT_MODEL_NAME,
    ):
        if dimension <= 0:
            raise ValueError(f"Embedding dimension must be positive, got {dimension}")
        self._dimension = dimension
        self._model_name = model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _hash_token(self, token: str, seed: int = 0) -> int:
        """Deterministic integer hash for a token string."""
        data = f"{seed}:{token}".encode()
        return int(hashlib.md5(data).hexdigest(), 16)

    def _generate_vector(self, text: str) -> list[float]:
        """Generate a unit-normalized vector for the given text."""
        vec = [0.0] * self._dimension
        if not text or not text.strip():
            # Return unit vector along first dimension for non-empty norm
            vec[0] = 1.0
            return vec

        # Tokenize normalized alphanumeric sequences
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            vec[0] = 1.0
            return vec

        # Accumulate unigrams and bigrams
        for i, token in enumerate(tokens):
            # Unigram feature
            h1 = self._hash_token(token, seed=1)
            idx1 = h1 % self._dimension
            sign1 = 1.0 if ((h1 >> 8) & 1) == 0 else -1.0
            vec[idx1] += sign1

            # Bigram feature to capture local context/order
            if i + 1 < len(tokens):
                bigram = f"{token}_{tokens[i + 1]}"
                h2 = self._hash_token(bigram, seed=2)
                idx2 = h2 % self._dimension
                sign2 = 1.0 if ((h2 >> 8) & 1) == 0 else -1.0
                vec[idx2] += sign2 * 1.5

        # L2-normalize to unit length
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0.0:
            return [v / norm for v in vec]

        vec[0] = 1.0
        return vec

    def embed_text(self, text: str) -> list[float]:
        return self._generate_vector(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._generate_vector(text) for text in texts]


def get_embedding_provider(
    provider_type: str | None = None,
    dimension: int | None = None,
) -> BaseEmbeddingProvider:
    """Factory function to resolve and instantiate the configured embedding provider.

    Args:
        provider_type: Optional override ('deterministic', etc.)
        dimension: Optional override for vector dimensionality

    Returns:
        Instance implementing BaseEmbeddingProvider
    """
    resolved_type = (provider_type or settings.EMBEDDING_PROVIDER).lower()
    resolved_dim = dimension or settings.EMBEDDING_DIMENSION

    if resolved_type in ("deterministic", "mock", "test", "local"):
        return DeterministicEmbeddingProvider(dimension=resolved_dim)

    # Extension point for future providers (e.g. Gemini, SentenceTransformers)
    raise ValueError(f"Unsupported embedding provider type: {resolved_type}")
