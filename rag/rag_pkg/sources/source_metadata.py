"""Source metadata model and registry for government documents.

Every collected government source is assigned a unique source_id and
stored with full provenance metadata. No dates or versions are
fabricated: unknown values remain None.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from rag.config.logging_config import get_logger
from rag.config.settings import settings

logger = get_logger("source_metadata")


class SourceMetadata(BaseModel):
    """Metadata for a single government source document."""

    source_id: str = Field(..., description="Unique source identifier (e.g. UDYAM_001)")
    title: str = Field(..., description="Document title")
    authority: str = Field(..., description="Issuing government authority")
    source_url: str = Field(..., description="Official source URL")
    document_type: str = Field(default="pdf", description="Document type (pdf/html/etc.)")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO timestamp when the source was retrieved",
    )
    published_at: str | None = Field(
        default=None, description="Publication/update date when available"
    )
    version: str | None = Field(
        default=None, description="Document version when available"
    )
    verification_status: str = Field(
        default="pending",
        description="pending/verified/unverified/outdated",
    )
    topic: str = Field(default="", description="Topic category (udyam_registration, gst, ...)")
    content_hash: str | None = Field(
        default=None, description="SHA-256 hash of the document content"
    )
    file_path: str | None = Field(
        default=None, description="Local path to the collected document"
    )
    page_count: int | None = Field(
        default=None, description="Number of pages in the document"
    )
    extraction_method: str | None = Field(
        default=None, description="pdf_text / ocr / mixed"
    )
    notes: str | None = Field(
        default=None, description="Collector notes / limitations"
    )

    def to_record(self) -> dict[str, Any]:
        """Serialize to a flat record for JSONL storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "SourceMetadata":
        return cls.model_validate(record)


def compute_content_hash(data: bytes) -> str:
    """Compute SHA-256 hash of raw document bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of extracted text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SourceRegistry:
    """Persistent registry of government sources.

    Stores sources as JSONL records. Provides lookup by source_id and
    by source_url, change detection via content hash, and registry
    persistence.
    """

    def __init__(self, registry_path: Path | None = None) -> None:
        self.registry_path = registry_path or settings.source_registry_path
        self._sources: dict[str, SourceMetadata] = {}
        self._by_url: dict[str, str] = {}  # url -> source_id
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.registry_path.exists():
            return
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with self.registry_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    source = SourceMetadata.from_record(record)
                    self._sources[source.source_id] = source
                    if source.source_url:
                        self._by_url[source.source_url] = source.source_id
                except (json.JSONDecodeError, ValueError) as exc:
                    logger.warning("Skipping malformed registry line: %s", exc)

    def add(self, source: SourceMetadata) -> None:
        """Add or update a source in the registry."""
        self._ensure_loaded()
        self._sources[source.source_id] = source
        if source.source_url:
            self._by_url[source.source_url] = source.source_id
        self._persist()

    def get(self, source_id: str) -> SourceMetadata | None:
        self._ensure_loaded()
        return self._sources.get(source_id)

    def get_by_url(self, source_url: str) -> SourceMetadata | None:
        self._ensure_loaded()
        source_id = self._by_url.get(source_url)
        if source_id is None:
            return None
        return self._sources.get(source_id)

    def list_sources(self) -> list[SourceMetadata]:
        self._ensure_loaded()
        return list(self._sources.values())

    def _persist(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with self.registry_path.open("w", encoding="utf-8") as fh:
            for source in self._sources.values():
                fh.write(json.dumps(source.to_record(), ensure_ascii=False))
                fh.write("\n")

    def contains(self, source_id: str) -> bool:
        self._ensure_loaded()
        return source_id in self._sources

    def count(self) -> int:
        self._ensure_loaded()
        return len(self._sources)
