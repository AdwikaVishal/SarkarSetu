"""Result ranking helpers.

Applies metadata filtering and similarity-score thresholds to raw FAISS
results, then returns a ranked list.
"""

from __future__ import annotations

from typing import Any

from rag.config.logging_config import get_logger

logger = get_logger("ranking")


def rank_results(
    results: list[dict[str, Any]],
    *,
    min_score: float | None = None,
    filters: dict[str, Any] | None = None,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Rank and filter retrieval results.

    Args:
        results: Raw result records with similarity_score.
        min_score: Minimum similarity score to keep.
        filters: Optional metadata field filters (key -> value).
        top_k: Maximum number of results to return.

    Returns:
        Ranked, filtered result list.
    """
    filtered = results
    if min_score is not None:
        filtered = [
            r for r in filtered
            if (r.get("similarity_score") or 0.0) >= min_score
        ]
    if filters:
        filtered = [
            r for r in filtered
            if all(r.get(k) == v for k, v in filters.items())
        ]
    # Already sorted desc by FAISS; preserve order
    if top_k is not None:
        filtered = filtered[:top_k]
    return filtered
