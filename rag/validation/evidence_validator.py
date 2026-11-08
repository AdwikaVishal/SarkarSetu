"""Evidence validation.

Identifies claims with no supporting retrieved passage, missing
citations, unverified sources, and low-confidence retrieval results.
Does not treat LLM output as verification of government rules.
"""

from __future__ import annotations

from typing import Any

from rag.config.logging_config import get_logger

logger = get_logger("evidence_validator")


class EvidenceValidator:
    """Validates that retrieval results provide sufficient evidence."""

    def validate(
        self,
        query: str,
        results: list[dict[str, Any]],
        business_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Assess whether results provide sufficient evidence for query.

        Returns a dict with:
        - sufficient: bool
        - insufficient: bool
        - missing_citations: list[str]
        - unverified_sources: list[str]
        - low_confidence: list[str]
        - message: str | None
        """
        business_context = business_context or {}
        missing_citations: list[str] = []
        unverified_sources: list[str] = []
        low_confidence: list[str] = []

        if not results:
            return {
                "sufficient": False,
                "insufficient": True,
                "missing_citations": [],
                "unverified_sources": [],
                "low_confidence": [],
                "message": (
                    "Insufficient verified information is available to "
                    "answer this question."
                ),
            }

        for result in results:
            source_id = result.get("source_id") or "unknown"
            status = result.get("verification_status", "pending")
            score = result.get("similarity_score") or 0.0
            excerpt = result.get("text")

            if not excerpt:
                missing_citations.append(source_id)

            if status in ("pending", "unverified"):
                unverified_sources.append(source_id)

            if score < 0.4:
                low_confidence.append(source_id)

        sufficient = bool(results) and not missing_citations and not low_confidence

        return {
            "sufficient": sufficient,
            "insufficient": not sufficient,
            "missing_citations": missing_citations,
            "unverified_sources": unverified_sources,
            "low_confidence": low_confidence,
            "message": (
                "Some retrieved sources are unverified or low-confidence."
                if not sufficient
                else None
            ),
        }
