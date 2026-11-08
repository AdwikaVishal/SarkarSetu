"""Citation builder for government knowledge retrieval.

Builds structured citation objects from retrieved source documents,
ensuring all source metadata is preserved and presented consistently
to users and agents.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from app.schemas.agents import RetrievalSource

logger = logging.getLogger(__name__)


class CitationBuilder:
    """Builds citation objects from retrieved source documents.

    Ensures all source metadata is preserved and presented consistently
    without fabricating missing information.
    """

    def __init__(self) -> None:
        pass

    def build_sources(
        self,
        candidates: list[dict[str, Any]] | list[RetrievalSource],
    ) -> list[RetrievalSource]:
        """Build RetrievalSource objects from candidate documents.

        Accepts either raw dict documents or already-built RetrievalSource
        objects, normalizing them into RetrievalSource instances.

        Args:
            candidates: List of candidate document dicts or RetrievalSource
                objects.

        Returns:
            List of RetrievalSource objects with preserved metadata.
        """
        sources: list[RetrievalSource] = []

        for doc in candidates:
            source = self._build_single(doc)
            sources.append(source)

        return sources

    def _build_single(
        self,
        doc: dict[str, Any] | RetrievalSource,
    ) -> RetrievalSource:
        """Build a single RetrievalSource from a candidate document.

        Accepts either a raw dict or an existing RetrievalSource object.
        When given a RetrievalSource, returns it as-is (with validation
        metadata preserved if present).

        Args:
            doc: Candidate document dict or RetrievalSource object.

        Returns:
            RetrievalSource object with preserved metadata.
        """
        # If already a RetrievalSource, return as-is
        if isinstance(doc, RetrievalSource):
            return doc

        # Extract retrieval timestamp
        retrieval_timestamp = datetime.now(UTC)

        # Extract validation info
        validation_warnings = doc.get("_validation_warnings", [])
        validation_passed = doc.get("_validation_passed", True)

        # Build source with all available fields
        source = RetrievalSource(
            document_id=doc.get("document_id"),
            source_title=doc.get("source_title"),
            issuing_authority=doc.get("issuing_authority"),
            source_url=doc.get("source_url"),
            publication_date=doc.get("publication_date"),
            relevant_excerpt=doc.get("relevant_excerpt"),
            page_or_section=doc.get("page_or_section"),
            retrieval_score=doc.get("retrieval_score"),
            document_version=doc.get("document_version"),
        )

        # Store validation metadata in a way that can be accessed
        # by agents that need it
        source._validation_warnings = validation_warnings  # type: ignore[attr-defined]
        source._validation_passed = validation_passed  # type: ignore[attr-defined]
        source._retrieval_timestamp = retrieval_timestamp  # type: ignore[attr-defined]
        source._service_or_scheme = doc.get("service_or_scheme")  # type: ignore[attr-defined]
        source._jurisdiction = doc.get("jurisdiction")  # type: ignore[attr-defined]
        source._document_type = doc.get("document_type")  # type: ignore[attr-defined]
        source._effective_date = doc.get("effective_date")  # type: ignore[attr-defined]
        source._last_verified_date = doc.get("last_verified_date")  # type: ignore[attr-defined]

        return source


def build_citation_summary(source: RetrievalSource) -> str:
    """Build a human-readable citation summary from a RetrievalSource.

    Args:
        source: RetrievalSource object.

    Returns:
        Formatted citation string.
    """
    parts: list[str] = []

    if source.source_title:
        parts.append(source.source_title)
    if source.issuing_authority:
        parts.append(f"({source.issuing_authority})")
    if source.page_or_section:
        parts.append(f", {source.page_or_section}")
    if source.source_url:
        parts.append(f" - {source.source_url}")

    return " ".join(parts)


def build_citation_list(sources: list[RetrievalSource]) -> str:
    """Build a numbered citation list from RetrievalSource objects.

    Args:
        sources: List of RetrievalSource objects.

    Returns:
        Formatted citation list string.
    """
    if not sources:
        return "No sources cited."

    lines: list[str] = []
    for i, source in enumerate(sources, 1):
        citation = build_citation_summary(source)
        lines.append(f"{i}. {citation}")

    return "\n".join(lines)
