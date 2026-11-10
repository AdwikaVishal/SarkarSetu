"""Source versioning and change detection.

Tracks source freshness using SHA-256 content hashes. When the same
document is collected again, the new hash is compared with the stored
hash to detect content changes. Age alone never marks a source outdated.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from rag.config.logging_config import get_logger
from rag.config.settings import settings
from rag.sources.source_metadata import SourceMetadata, SourceRegistry

logger = get_logger("source_versioning")


class SourceChangeReport(BaseModel):
    """Result of checking a source for changes."""

    source_id: str = Field(..., description="Source identifier")
    source_url: str = Field(..., description="Source URL")
    previous_hash: str | None = Field(
        default=None, description="Previously stored content hash"
    )
    new_hash: str = Field(..., description="Hash of the newly collected content")
    changed: bool = Field(
        default=False, description="Whether content changed since last ingestion"
    )
    first_seen: bool = Field(
        default=False, description="Whether this is a new source"
    )
    checked_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO timestamp of the check",
    )
    action: str = Field(
        default="none",
        description="Suggested action: none / reingest / reprocess_chunks",
    )
    notes: str | None = Field(default=None, description="Additional notes")


class SourceFreshnessReport(BaseModel):
    """Aggregate freshness report across all tracked sources."""

    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    total_sources: int = Field(default=0)
    unchanged: int = Field(default=0)
    changed: int = Field(default=0)
    new: int = Field(default=0)
    never_ingested: int = Field(default=0)
    sources: list[SourceChangeReport] = Field(default_factory=list)


class SourceVersioning:
    """Detects content changes in government sources using SHA-256 hashes."""

    def __init__(self, registry: SourceRegistry | None = None) -> None:
        self.registry = registry or SourceRegistry()

    def check_changes(
        self,
        source_id: str,
        new_file_path: str | Path,
    ) -> SourceChangeReport:
        """Compare a newly collected file against the stored source hash.

        Args:
            source_id: The source identifier to check.
            new_file_path: Path to the newly collected document.

        Returns:
            SourceChangeReport indicating whether content changed.
        """
        new_path = Path(new_file_path)
        existing = self.registry.get(source_id)

        if not new_path.exists():
            return SourceChangeReport(
                source_id=source_id,
                source_url=existing.source_url if existing else "",
                new_hash="",
                changed=False,
                first_seen=existing is None,
                action="error",
                notes=f"File not found: {new_path}",
            )

        new_bytes = new_path.read_bytes()
        new_hash = self._hash_bytes(new_bytes)

        if existing is None:
            return SourceChangeReport(
                source_id=source_id,
                source_url="",
                new_hash=new_hash,
                changed=False,
                first_seen=True,
                action="ingest",
                notes="New source; no previous hash to compare",
            )

        previous_hash = existing.content_hash
        changed = previous_hash is not None and previous_hash != new_hash

        return SourceChangeReport(
            source_id=source_id,
            source_url=existing.source_url,
            previous_hash=previous_hash,
            new_hash=new_hash,
            changed=changed,
            first_seen=False,
            action="reingest" if changed else "none",
            notes=(
                "Content changed since last ingestion"
                if changed
                else "Content unchanged since last ingestion"
            ),
        )

    def freshness_report(self) -> SourceFreshnessReport:
        """Build a freshness report for all registered sources."""
        sources = self.registry.list_sources()
        report = SourceFreshnessReport(total_sources=len(sources))
        for source in sources:
            entry = SourceChangeReport(
                source_id=source.source_id,
                source_url=source.source_url,
                previous_hash=source.content_hash,
                new_hash=source.content_hash or "",
                changed=False,
                first_seen=source.content_hash is None,
                action="ingest" if source.content_hash is None else "none",
                notes=(
                    "Never ingested"
                    if source.content_hash is None
                    else "Hash recorded"
                ),
            )
            if source.content_hash is None:
                report.never_ingested += 1
            else:
                report.unchanged += 1
            report.sources.append(entry)
        return report

    @staticmethod
    def _hash_bytes(data: bytes) -> str:
        import hashlib

        return hashlib.sha256(data).hexdigest()

    def record_ingestion(
        self,
        source_id: str,
        source_url: str,
        content_hash: str,
        file_path: str | Path,
        **metadata: Any,
    ) -> None:
        """Record (or update) a source after successful ingestion."""
        existing = self.registry.get(source_id)
        base = {
            "source_id": source_id,
            "title": metadata.get("title", ""),
            "authority": metadata.get("authority", ""),
            "source_url": source_url,
            "document_type": metadata.get("document_type", "pdf"),
            "topic": metadata.get("topic", ""),
            "content_hash": content_hash,
            "file_path": str(file_path),
            "verification_status": metadata.get(
                "verification_status", "pending"
            ),
            "version": metadata.get("version"),
            "published_at": metadata.get("published_at"),
            "page_count": metadata.get("page_count"),
            "extraction_method": metadata.get("extraction_method"),
            "notes": metadata.get("notes"),
        }
        if existing:
            # Preserve original retrieved_at; update hash and file info
            base["retrieved_at"] = existing.retrieved_at
            source = SourceMetadata(**base)
        else:
            source = SourceMetadata(**base)
        self.registry.add(source)


# ---------------------------------------------------------------------------
# Module-level convenience function matching the Person 1 integration contract.
# ---------------------------------------------------------------------------

_default_versioning: SourceVersioning | None = None


def _get_default_versioning() -> SourceVersioning:
    global _default_versioning
    if _default_versioning is None:
        _default_versioning = SourceVersioning()
    return _default_versioning


def check_source_changes(
    source_id: str,
    new_file_path: str,
) -> dict:
    """Check whether a source document has changed since last ingestion.

    Standalone convenience wrapper:

        from rag.sources.source_versioning import check_source_changes

    Args:
        source_id: The source identifier to check.
        new_file_path: Path to the newly collected document.

    Returns:
        A dict describing whether content changed and the suggested action.
    """
    versioning = _get_default_versioning()
    report = versioning.check_changes(source_id, new_file_path)
    return report.model_dump(mode="json")

