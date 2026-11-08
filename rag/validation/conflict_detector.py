"""Conflict detector.

Flags conflicting source passages among retrieved results by detecting
contradictory numeric claims (e.g. different thresholds) on the same
topic from different sources.
"""

from __future__ import annotations

import re
from typing import Any

from rag.config.logging_config import get_logger

logger = get_logger("conflict_detector")


class ConflictDetector:
    """Detects conflicts between retrieved source passages."""

    _THRESHOLD_PATTERN = re.compile(
        r"(?i)(threshold|limit|exemption|turnover|cap|ceiling)[^\d]{0,40}"
        r"(₹|rs|inr|rupees?|lakh|crore)?\s*(\d[\d,]*(?:\.\d+)?)"
    )

    def detect(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect conflicts among results.

        Returns a list of conflict descriptions.
        """
        conflicts: list[dict[str, Any]] = []
        # Group numeric threshold claims by topic keyword
        claims: dict[str, list[dict[str, Any]]] = {}
        for result in results:
            text = result.get("text") or ""
            for match in self._THRESHOLD_PATTERN.finditer(text):
                topic = match.group(1).lower()
                value = match.group(3)
                claims.setdefault(topic, []).append(
                    {
                        "source_id": result.get("source_id"),
                        "document_title": result.get("document_title"),
                        "value": value,
                        "page_number": result.get("page_number"),
                        "excerpt": text[:200],
                    }
                )

        for topic, entries in claims.items():
            values = {e["value"] for e in entries}
            if len(values) > 1:
                conflicts.append(
                    {
                        "topic": topic,
                        "conflicting_values": sorted(values),
                        "sources": entries,
                        "note": (
                            "Different sources report different threshold values; "
                            "verify on official government websites."
                        ),
                    }
                )
        return conflicts
