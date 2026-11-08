"""Chunk metadata store (JSONL).

Persists chunk metadata separately from vectors, retaining the mapping
from chunk_id to source document, page, section, and source URL.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from rag.config.logging_config import get_logger
from rag.config.settings import settings

logger = get_logger("metadata_store")


class ChunkMetadataStore:
    """Append-only JSONL store of chunk metadata records."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.metadata_store_path
        self._lock = threading.Lock()
        self._cache: dict[str, dict[str, Any]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    chunk_id = record.get("chunk_id")
                    if chunk_id:
                        self._cache[chunk_id] = record
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed metadata line")

    def write_records(self, records: list[dict[str, Any]]) -> None:
        """Write (append) chunk metadata records to the store."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self.path.open("a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False))
                fh.write("\n")
                chunk_id = record.get("chunk_id")
                if chunk_id:
                    self._cache[chunk_id] = record

    def get(self, chunk_id: str) -> dict[str, Any] | None:
        self._ensure_loaded()
        return self._cache.get(chunk_id)

    def get_many(self, chunk_ids: list[str]) -> list[dict[str, Any] | None]:
        self._ensure_loaded()
        return [self._cache.get(cid) for cid in chunk_ids]

    def all(self) -> list[dict[str, Any]]:
        self._ensure_loaded()
        return list(self._cache.values())

    def count(self) -> int:
        self._ensure_loaded()
        return len(self._cache)

    def clear(self) -> None:
        """Clear the store (used when rebuilding the index)."""
        self._cache = {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")
