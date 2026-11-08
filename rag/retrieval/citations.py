"""Citation generation.

Builds traceable citation records from retrieved chunks. Never
fabricates URLs or page numbers; only cites chunks that were actually
retrieved.
"""

from __future__ import annotations

from typing import Any

from rag.config.logging_config import get_logger

logger = get_logger("citations")


class Citation:
    """A single citation referencing a retrieved source passage."""

    def __init__(self, **fields: Any) -> None:
        self.citation_id: str = fields.get("citation_id", "")
        self.source_id: str | None = fields.get("source_id")
        self.document_title: str | None = fields.get("document_title")
        self.authority: str | None = fields.get("authority")
        self.page_number: int | None = fields.get("page_number")
        self.section: str | None = fields.get("section")
        self.source_url: str | None = fields.get("source_url")
        self.retrieved_at: str | None = fields.get("retrieved_at")
        self.verification_status: str | None = fields.get(
            "verification_status", "pending"
        )
        self.similarity_score: float | None = fields.get("similarity_score")
        self.excerpt: str | None = fields.get("excerpt")

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "source_id": self.source_id,
            "document_title": self.document_title,
            "authority": self.authority,
            "page_number": self.page_number,
            "section": self.section,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at,
            "verification_status": self.verification_status,
            "similarity_score": self.similarity_score,
            "excerpt": self.excerpt,
        }


def build_citations(
    results: list[dict[str, Any]],
    *,
    id_prefix: str = "CIT",
) -> list[dict[str, Any]]:
    """Build citation records from retrieved results.

    Args:
        results: Retrieved chunk records (must include source metadata).
        id_prefix: Prefix for generated citation ids.

    Returns:
        List of citation dicts. Only cites chunks actually retrieved.
    """
    citations: list[dict[str, Any]] = []
    for index, result in enumerate(results, 1):
        citation_id = f"{id_prefix}_{index:03d}"
        citation = Citation(
            citation_id=citation_id,
            source_id=result.get("source_id"),
            document_title=result.get("document_title"),
            authority=result.get("authority"),
            page_number=result.get("page_number"),
            section=result.get("section"),
            source_url=result.get("source_url"),
            retrieved_at=result.get("retrieved_at"),
            verification_status=result.get("verification_status"),
            similarity_score=result.get("similarity_score"),
            excerpt=result.get("text"),
        )
        citations.append(citation.to_dict())
    return citations
