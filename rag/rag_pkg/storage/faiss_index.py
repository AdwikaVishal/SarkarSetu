"""FAISS CPU vector index with persistence and metadata mapping.

Vectors are stored in FAISS; chunk ids are stored in parallel so every
vector remains mapped to its source chunk metadata.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import faiss
import numpy as np

from rag.config.logging_config import get_logger
from rag.config.settings import settings

logger = get_logger("faiss_index")


class FaissIndex:
    """Persistent FAISS IndexFlatIP (cosine via normalized vectors) index."""

    def __init__(self, dimension: int | None = None) -> None:
        self.dimension = dimension or settings.embedding_dim
        self._index: faiss.IndexFlatIP | None = None
        self._id_map: list[str] = []  # position -> chunk_id

    def _ensure_index(self) -> faiss.IndexFlatIP:
        if self._index is None:
            self._index = faiss.IndexFlatIP(self.dimension)
        return self._index

    def add(
        self,
        embeddings: Sequence[Sequence[float]],
        ids: Sequence[str],
    ) -> int:
        """Add embeddings with corresponding ids. Returns number added."""
        if not embeddings:
            return 0
        vectors = np.asarray(
            [[float(x) for x in vec] for vec in embeddings], dtype=np.float32
        )
        if vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dimension {vectors.shape[1]} != index dimension {self.dimension}"
            )
        index = self._ensure_index()
        index.add(vectors)
        self._id_map.extend(ids)
        logger.info("Added %d vectors to FAISS index", len(ids))
        return len(ids)

    def search(
        self,
        query_embedding: Sequence[float],
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """Search the index. Returns [(chunk_id, similarity_score)] sorted desc."""
        index = self._ensure_index()
        if index.ntotal == 0:
            return []
        query = np.asarray(
            [[float(x) for x in query_embedding]], dtype=np.float32
        )
        if query.shape[1] != self.dimension:
            raise ValueError(
                f"Query dimension {query.shape[1]} != index dimension {self.dimension}"
            )
        k = min(top_k, index.ntotal)
        scores, indices = index.search(query, k)
        results: list[tuple[str, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._id_map):
                continue
            results.append((self._id_map[idx], float(score)))
        return results

    def rebuild(
        self,
        embeddings: Sequence[Sequence[float]],
        ids: Sequence[str],
    ) -> int:
        """Fully rebuild the index from scratch (used after source changes)."""
        self._index = faiss.IndexFlatIP(self.dimension)
        self._id_map = []
        return self.add(embeddings, ids)

    def save(self, path: str | Path) -> None:
        """Persist the index and id map to disk."""
        index = self._ensure_index()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(path))
        id_path = path.with_suffix(path.suffix + ".ids")
        id_path.write_text("\n".join(self._id_map), encoding="utf-8")
        logger.info("FAISS index saved to %s (%d vectors)", path, index.ntotal)

    def load(self, path: str | Path) -> bool:
        """Load a persisted index and id map. Returns True if loaded."""
        path = Path(path)
        id_path = path.with_suffix(path.suffix + ".ids")
        if not path.exists() or not id_path.exists():
            logger.warning("FAISS index files not found: %s", path)
            return False
        try:
            self._index = faiss.read_index(str(path))
            self.dimension = int(self._index.d)
            self._id_map = id_path.read_text(encoding="utf-8").split("\n")
            if self._id_map == [""]:
                self._id_map = []
            logger.info(
                "FAISS index loaded from %s (%d vectors)", path, self._index.ntotal
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to load FAISS index: %s", exc)
            self._index = None
            self._id_map = []
            return False

    @property
    def is_empty(self) -> bool:
        return self._index is None or self._index.ntotal == 0

    @property
    def count(self) -> int:
        return int(self._index.ntotal) if self._index is not None else 0
