"""Retrieval logic for the government knowledge provider.

Implements query normalization, candidate retrieval, ranking, and
deduplication using a fixture-backed index for development purposes.

This module is clearly marked as development-only. Saatvika's RAG
implementation should replace the retriever with FAISS/semantic search.
"""

import logging
import re
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Fixture dataset of government documents for development testing.
# These are synthetic example documents and must NOT be treated as
# real government rules or citations. Saatvika's RAG implementation
# should replace this fixture data with real document retrieval.
_FIXTURE_DOCUMENTS: list[dict[str, Any]] = [
    {
        "document_id": "gov_in_udyam_2024_001",
        "source_title": "Udyam Registration Guidelines 2024",
        "issuing_authority": "Ministry of MSME, Government of India",
        "source_url": "https://udyamregistration.gov.in/udyam-registration-guidelines",
        "publication_date": "2024-01-15",
        "effective_date": "2024-04-01",
        "last_verified_date": "2024-06-01",
        "document_version": "2024.1",
        "document_type": "scheme_guideline",
        "relevant_excerpt": "Udyam Registration is available for micro, small and medium enterprises. "
        "Enterprises with investment in plant and machinery up to Rs. 2.5 crore and turnover up to "
        "Rs. 25 crore are classified as micro enterprises.",
        "service_or_scheme": "udyam_registration",
        "jurisdiction": "IND",
        "retrieval_score": 0.95,
    },
    {
        "document_id": "gov_in_gst_2024_002",
        "source_title": "GST Registration Threshold Limits",
        "issuing_authority": "Central Board of Indirect Taxes and Customs (CBIC)",
        "source_url": "https://gst.gov.in/gst-registration-threshold",
        "publication_date": "2024-03-01",
        "effective_date": "2024-04-01",
        "last_verified_date": "2024-06-15",
        "document_version": "2024.2",
        "document_type": "registration_requirement",
        "relevant_excerpt": "Businesses with aggregate turnover exceeding Rs. 20 lakh (Rs. 10 lakh for "
        "special category states) are required to register for GST. "
        "Inter-state suppliers must register regardless of turnover.",
        "service_or_scheme": "gst_registration",
        "jurisdiction": "IND",
        "retrieval_score": 0.92,
    },
    {
        "document_id": "gov_in_pmsbby_2024_003",
        "source_title": "Pradhan Mantri Shram Yogi Maan-Dhan (PM-SYM) Scheme",
        "issuing_authority": "Ministry of Labour and Employment, Government of India",
        "source_url": "https://pmsym.gov.in/scheme-details",
        "publication_date": "2024-02-01",
        "effective_date": "2024-03-01",
        "last_verified_date": "2024-05-01",
        "document_version": "2024.1",
        "document_type": "subsidy_scheme",
        "relevant_excerpt": "PM-SYM is a voluntary and contributory pension scheme for unorganised workers. "
        "Eligible workers are those in the age group of 18-40 years with monthly income "
        "not exceeding Rs. 15,000.",
        "service_or_scheme": "pmsym",
        "jurisdiction": "IND",
        "retrieval_score": 0.88,
    },
    {
        "document_id": "gov_in_msme_2024_004",
        "source_title": "MSME Scheme Benefits and Eligibility",
        "issuing_authority": "Ministry of MSME, Government of India",
        "source_url": "https://msme.gov.in/scheme-benefits",
        "publication_date": "2024-02-15",
        "effective_date": "2024-03-01",
        "last_verified_date": "2024-05-15",
        "document_version": "2024.1",
        "document_type": "scheme_guideline",
        "relevant_excerpt": "MSME schemes provide credit guarantee, subsidy, and infrastructure support "
        "to registered MSMEs. Eligibility depends on enterprise classification and "
        "sector-specific criteria.",
        "service_or_scheme": "msme_schemes",
        "jurisdiction": "IND",
        "retrieval_score": 0.90,
    },
    {
        "document_id": "gov_in_govt_emarket_2024_005",
        "source_title": "Government e-Marketplace (GeM) Registration",
        "issuing_authority": "Directorate General of Supplies and Disposals (DGS&D)",
        "source_url": "https://gem.gov.in/registration",
        "publication_date": "2024-01-10",
        "effective_date": "2024-02-01",
        "last_verified_date": "2024-04-01",
        "document_version": "2024.1",
        "document_type": "registration_requirement",
        "relevant_excerpt": "GeM registration is required for suppliers wanting to sell goods "
        "and services to government departments. Registration requires PAN, GSTIN, "
        "and bank account details.",
        "service_or_scheme": "gem_registration",
        "jurisdiction": "IND",
        "retrieval_score": 0.87,
    },
    {
        "document_id": "gov_in_startup_2024_006",
        "source_title": "Startup India Registration and Benefits",
        "issuing_authority": "Department for Promotion of Industry and Internal Trade (DPIIT)",
        "source_url": "https://startupindia.gov.in/registration",
        "publication_date": "2024-01-20",
        "effective_date": "2024-02-01",
        "last_verified_date": "2024-04-15",
        "document_version": "2024.1",
        "document_type": "registration_requirement",
        "relevant_excerpt": "Startup India recognition is available to entities incorporated as "
        "a private limited company, registered partnership firm, or limited liability "
        "partnership. Turnover should not exceed Rs. 100 crore in any financial year.",
        "service_or_scheme": "startup_india",
        "jurisdiction": "IND",
        "retrieval_score": 0.89,
    },
]


class Retriever:
    """Retrieval component for government knowledge.

    Provides query normalization, candidate retrieval, reranking, and
    deduplication. Uses a fixture-backed index for development.
    """

    def __init__(self) -> None:
        self._index = _FIXTURE_DOCUMENTS

    def normalize_query(self, query: str) -> str:
        """Normalize a user query for retrieval.

        Strips whitespace, normalizes case for matching, and removes
        extraneous punctuation while preserving meaningful terms.

        Args:
            query: Raw user query string.

        Returns:
            Normalized query string.
        """
        if not query:
            return ""

        # Basic normalization
        normalized = query.strip()
        normalized = re.sub(r"\s+", " ", normalized)  # Collapse whitespace
        return normalized

    def build_filters(
        self,
        query: str,
        explicit_filters: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Build retrieval filters from query context and explicit filters.

        Extracts scheme/service keywords from the query and combines
        them with explicit filter parameters.

        Args:
            query: Normalized user query.
            explicit_filters: Optional explicit filter parameters.

        Returns:
            Combined filter dictionary.
        """
        filters: dict[str, object] = {}
        if explicit_filters:
            filters.update(explicit_filters)

        query_lower = query.lower()

        # Extract scheme keywords from query
        scheme_keywords = [
            "udyam",
            "gst",
            "pmsym",
            "msme",
            "gem",
            "startup india",
            "startup",
        ]
        matched_schemes = [
            s for s in scheme_keywords if s in query_lower
        ]
        if matched_schemes:
            filters["scheme_or_scheme"] = matched_schemes

        return filters

    def retrieve_candidates(
        self,
        query: str,
        filters: dict[str, object] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Retrieve candidate documents from the fixture index.

        Performs keyword-based matching against fixture documents.

        Args:
            query: Normalized search query.
            filters: Optional filter parameters.
            limit: Maximum number of candidates to return.

        Returns:
            List of candidate document dictionaries with retrieval scores.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        candidates: list[dict[str, Any]] = []

        for doc in self._index:
            # Apply filters
            if filters:
                scheme_filters = filters.get("scheme_or_scheme")
                if scheme_filters and isinstance(scheme_filters, list):
                    doc_scheme = doc.get("service_or_scheme", "").lower()
                    # Match if any filter scheme is a substring of doc scheme,
                    # or vice versa (e.g., filter "gst" matches doc "gst_registration")
                    if not any(
                        sf in doc_scheme or doc_scheme in sf
                        for sf in scheme_filters
                        if isinstance(sf, str)
                    ):
                        continue

            # Calculate relevance score based on keyword overlap
            doc_text = (
                f"{doc.get('source_title', '')} "
                f"{doc.get('relevant_excerpt', '')} "
                f"{doc.get('service_or_scheme', '')}"
            ).lower()

            query_word_matches = sum(
                1 for w in query_words if w in doc_text
            )
            if query_word_matches == 0:
                continue

            base_score = query_word_matches / len(query_words)
            fixture_score = doc.get("retrieval_score", 0.5)
            # Combine query match with fixture score
            combined_score = (base_score * 0.6) + (fixture_score * 0.4)

            candidate = dict(doc)
            candidate["retrieval_score"] = round(combined_score, 4)
            candidates.append(candidate)

        # Sort by score descending
        candidates.sort(key=lambda d: d.get("retrieval_score", 0), reverse=True)

        return candidates[:limit]

    def rerank(
        self,
        candidates: list[dict[str, Any]],
        query: str,
    ) -> list[dict[str, Any]]:
        """Rerank candidate documents by relevance.

        Applies additional scoring based on document freshness,
        source authority, and query-context match.

        Args:
            candidates: List of candidate documents.
            query: Normalized query string.

        Returns:
            Reranked list of candidate documents.
        """
        for doc in candidates:
            score = doc.get("retrieval_score", 0.0)

            # Boost documents from authoritative government sources
            authority = doc.get("issuing_authority", "").lower()
            if any(
                kw in authority
                for kw in ["ministry", "government of india", "cbic", "dpiit"]
            ):
                score += 0.05

            # Boost documents with recent effective dates
            effective_date = doc.get("effective_date")
            if effective_date:
                try:
                    eff = datetime.fromisoformat(effective_date)
                    now = datetime.now(UTC)
                    days_old = (now - eff.replace(tzinfo=UTC)).days
                    if days_old < 365:
                        score += 0.02
                except (ValueError, TypeError):
                    pass

            doc["retrieval_score"] = round(min(score, 1.0), 4)

        candidates.sort(key=lambda d: d.get("retrieval_score", 0), reverse=True)
        return candidates

    def deduplicate(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Deduplicate overlapping document chunks.

        Removes documents with the same document_id, keeping the
        highest-scored version.

        Args:
            candidates: List of candidate documents.

        Returns:
            Deduplicated list of candidate documents.
        """
        seen_ids: set[str] = set()
        deduped: list[dict[str, Any]] = []

        for doc in candidates:
            doc_id = doc.get("document_id")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                deduped.append(doc)
            elif not doc_id:
                # Include documents without IDs
                deduped.append(doc)

        return deduped
