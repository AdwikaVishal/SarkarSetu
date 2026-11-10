"""Semantic embedding generation using sentence-transformers.

Loads sentence-transformers/all-MiniLM-L6-v2 once (singleton) and
reuses it for all embedding requests. Handles empty text, batch
processing, dimension validation, and model-loading failures.
"""

from __future__ import annotations

import logging
import threading
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from rag.config.logging_config import get_logger
from rag.config.settings import settings

logger = get_logger("embedder")


class EmbeddingError(Exception):
    """Raised when embedding generation or model loading fails."""


class _Embedder:
    """Internal singleton that owns the SentenceTransformer model."""

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None
        self._lock = threading.Lock()
        self._dimension: int | None = None
        self._load_error: str | None = None

    def _ensure_loaded(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model
        if self._load_error is not None:
            raise EmbeddingError(f"Embedding model failed to load: {self._load_error}")
        with self._lock:
            if self._model is not None:
                return self._model
            if self._load_error is not None:
                raise EmbeddingError(f"Embedding model failed to load: {self._load_error}")
            try:
                logger.info(
                    "Loading embedding model: %s", settings.embedding_model
                )
                model = SentenceTransformer(settings.embedding_model)
                self._model = model
                # Probe dimension with a single embedding
                probe = model.encode(["dimension probe"], convert_to_numpy=True)
                self._dimension = int(probe.shape[1])
                logger.info(
                    "Embedding model loaded (dimension=%d)", self._dimension
                )
            except Exception as exc:  # noqa: BLE001 - surface as EmbeddingError
                self._load_error = str(exc)
                logger.exception("Failed to load embedding model")
                raise EmbeddingError(
                    f"Failed to load embedding model '{settings.embedding_model}': {exc}"
                ) from exc
        return self._model

    @property
    def dimension(self) -> int:
        self._ensure_loaded()
        assert self._dimension is not None
        return self._dimension

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        model = self._ensure_loaded()
        clean_texts = [t if t is not None else "" for t in texts]
        embeddings = model.encode(
            clean_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)


# Module-level singleton
_embeder = _Embedder()


class Embedder:
    """Public embedding API. Reuses a single loaded model instance."""

    def __init__(self) -> None:
        self._backend = _embeder

    def load_embedding_model(self) -> None:
        """Explicitly load (and validate) the embedding model now."""
        self._backend._ensure_loaded()  # noqa: SLF001 - intentional access

    def generate_embedding(self, text: str) -> list[float]:
        """Generate a normalized embedding for a single text.

        Empty text returns a zero vector of the correct dimension.
        """
        if not text or not text.strip():
            dim = self._backend.dimension
            return [0.0] * dim
        vec = self._backend.encode([text])
        return [float(x) for x in vec[0]]

    def generate_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate normalized embeddings for a batch of texts.

        Empty strings produce zero vectors. The batch is processed in a
        single model call for efficiency.
        """
        if not texts:
            return []
        dim = self._backend.dimension
        result: list[list[float]] = []
        # Process in batches to avoid excessive memory on very large inputs
        batch_size = 64
        for i in range(0, len(texts), batch_size):
            batch = list(texts[i : i + batch_size])
            vecs = self._backend.encode(batch)
            for vec in vecs:
                result.append([float(x) for x in vec])
        # Validate dimensions
        for vec in result:
            if len(vec) != dim:
                raise EmbeddingError(
                    f"Embedding dimension mismatch: expected {dim}, got {len(vec)}"
                )
        return result

    def generate_query_embedding(self, query: str) -> list[float]:
        """Generate an embedding for a user query.

        Delegates to generate_embedding; kept as a separate named
        function for contract clarity.
        """
        return self.generate_embedding(query)

    @property
    def dimension(self) -> int:
        return self._backend.dimension

    @property
    def model_loaded(self) -> bool:
        return self._backend._model is not None  # noqa: SLF001

    @property
    def load_error(self) -> str | None:
        return self._backend._load_error  # noqa: SLF001
