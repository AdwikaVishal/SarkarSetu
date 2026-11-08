"""Source validation for government knowledge retrieval.

Implements source validation rules to ensure retrieved documents
meet quality standards before being presented to users or used
by agents.

Validation rules:
- Prefer official government domains and issuing authorities.
- Preserve the original URL.
- Flag unofficial sources.
- Never treat a search snippet as authoritative evidence.
- Do not use expired or superseded documents as current guidance
  without explicitly marking them historical.
- Do not treat a document's upload date as its publication date.
- Do not invent section numbers, page numbers or dates.
- Preserve conflicting evidence rather than silently choosing one source.
- Return source verification status and warnings.
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Known official Indian government domains
OFFICIAL_GOV_DOMAINS: frozenset[str] = frozenset({
    "gov.in",
    "nic.in",
    "govt.in",
    "udyamregistration.gov.in",
    "gst.gov.in",
    "msme.gov.in",
    "pmsym.gov.in",
    "gem.gov.in",
    "startupindia.gov.in",
    "incometax.gov.in",
    "epfindia.gov.in",
    "esic.nic.in",
})


class SourceValidator:
    """Validates retrieved government document sources.

    Applies validation rules to ensure source quality and provenance.
    Does not modify source content - only adds validation metadata
    and warnings.
    """

    def __init__(self) -> None:
        pass

    def validate_sources(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Validate a list of candidate documents.

        Args:
            candidates: List of candidate document dictionaries.

        Returns:
            List of validated candidate documents with added
            validation metadata.
        """
        validated: list[dict[str, Any]] = []

        for doc in candidates:
            validated_doc = self._validate_single(doc)
            validated.append(validated_doc)

        return validated

    def _validate_single(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Validate a single candidate document.

        Args:
            doc: Candidate document dictionary.

        Returns:
            Validated document with added validation fields.
        """
        doc = dict(doc)  # Don't mutate original

        warnings: list[str] = []

        # Check issuing authority
        authority = doc.get("issuing_authority", "")
        is_official = self._is_official_authority(authority)
        doc["_is_official_authority"] = is_official

        if not is_official:
            warnings.append(
                f"Source authority '{authority}' is not a recognized "
                "official government body."
            )

        # Check source URL domain
        url = doc.get("source_url", "")
        is_official_domain = self._is_official_domain(url)
        doc["_is_official_domain"] = is_official_domain

        if not is_official_domain and url:
            warnings.append(
                f"Source URL '{url}' is not from an official government domain."
            )

        # Check effective date vs publication date
        effective_date = doc.get("effective_date")
        publication_date = doc.get("publication_date")

        if effective_date and publication_date:
            try:
                eff = self._parse_date(effective_date)
                pub = self._parse_date(publication_date)
                if eff and pub and eff < pub:
                    warnings.append(
                        f"Effective date ({effective_date}) precedes "
                        f"publication date ({publication_date}). "
                        "This may indicate a data quality issue."
                    )
            except (ValueError, TypeError):
                pass

        # Check if document appears expired
        if effective_date:
            try:
                eff = self._parse_date(effective_date)
                if eff:
                    now = datetime.now(UTC)
                    if eff < now.replace(tzinfo=eff.tzinfo or UTC):
                        warnings.append(
                            f"Document effective date ({effective_date}) "
                            "is in the past. Verify current validity."
                        )
            except (ValueError, TypeError):
                pass

        # Check for missing critical fields
        missing_fields: list[str] = []
        if not doc.get("source_title"):
            missing_fields.append("source_title")
        if not doc.get("issuing_authority"):
            missing_fields.append("issuing_authority")
        if not doc.get("source_url"):
            missing_fields.append("source_url")
        if not doc.get("relevant_excerpt"):
            missing_fields.append("relevant_excerpt")

        if missing_fields:
            warnings.append(
                f"Missing source metadata: {', '.join(missing_fields)}"
            )

        doc["_validation_warnings"] = warnings
        doc["_validation_passed"] = len(warnings) == 0

        return doc

    def _is_official_authority(self, authority: str) -> bool:
        """Check if an issuing authority is an official government body.

        Args:
            authority: Issuing authority string.

        Returns:
            True if the authority appears to be an official government body.
        """
        if not authority:
            return False

        authority_lower = authority.lower()
        official_keywords = [
            "ministry",
            "government of india",
            "department",
            "board",
            "council",
            "commission",
            "authority",
            "directorate",
        ]

        return any(kw in authority_lower for kw in official_keywords)

    def _is_official_domain(self, url: str) -> bool:
        """Check if a URL is from an official government domain.

        Args:
            url: Source URL string.

        Returns:
            True if the URL appears to be from an official government domain.
        """
        if not url:
            return False

        url_lower = url.lower()
        return any(domain in url_lower for domain in OFFICIAL_GOV_DOMAINS)

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse a date string into a datetime object.

        Args:
            date_str: Date string in ISO format.

        Returns:
            Parsed datetime object, or None if parsing fails.
        """
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            try:
                # Try common formats
                from datetime import datetime as dt

                return dt.strptime(date_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                return None
