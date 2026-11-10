"""Semantic retrieval engine.

Accepts natural-language queries, generates query embeddings, searches
FAISS, and returns ranked results with full source metadata, page
numbers, official source links, and verification flags.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from rag.config.logging_config import get_logger
from rag.config.settings import settings
from rag.embeddings.embedder import Embedder, EmbeddingError
from rag.retrieval.citations import build_citations, Citation
from rag.retrieval.ranking import rank_results
from rag.storage.faiss_index import FaissIndex
from rag.storage.metadata_store import ChunkMetadataStore
from rag.validation.evidence_validator import EvidenceValidator
from rag.validation.conflict_detector import ConflictDetector

logger = get_logger("retrieval")


class RetrievalResult:
    """Structured output of a retrieval query."""

    def __init__(
        self,
        *,
        query: str,
        results: list[dict[str, Any]],
        citations: list[dict[str, Any]],
        source_versions: list[dict[str, Any]],
        retrieval_status: str,
        message: str | None = None,
    ) -> None:
        self.query = query
        self.results = results
        self.citations = citations
        self.source_versions = source_versions
        self.retrieval_status = retrieval_status
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "results": self.results,
            "citations": self.citations,
            "source_versions": self.source_versions,
            "retrieval_status": self.retrieval_status,
            "message": self.message,
        }


class RetrievalEngine:
    """Semantic retrieval over the FAISS index of government sources."""

    def __init__(
        self,
        *,
        index: FaissIndex | None = None,
        metadata_store: ChunkMetadataStore | None = None,
        embedder: Embedder | None = None,
        top_k: int | None = None,
    ) -> None:
        self.index = index or FaissIndex()
        self.metadata_store = metadata_store or ChunkMetadataStore()
        self.embedder = embedder or Embedder()
        self.top_k = top_k or settings.default_top_k
        self.validator = EvidenceValidator()
        self.conflict_detector = ConflictDetector()

    def retrieve_guidance(
        self,
        query: str,
        business_context: dict[str, Any] | None = None,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        """Retrieve relevant government guidance for a query.

        Args:
            query: Natural-language user query.
            business_context: Optional business profile context for
                metadata filtering (e.g. state, scheme).
            top_k: Maximum number of results to return.

        Returns:
            Dict matching the retrieve_guidance output contract.
        """
        business_context = business_context or {}
        k = top_k or self.top_k

        if not query or not query.strip():
            return RetrievalResult(
                query=query,
                results=[],
                citations=[],
                source_versions=[],
                retrieval_status="insufficient_evidence",
                message="Empty query; no retrieval performed.",
            ).to_dict()

        # Ensure index loaded
        if self.index.is_empty:
            loaded = self.index.load(settings.faiss_index_path)
            if not loaded:
                return RetrievalResult(
                    query=query,
                    results=[],
                    citations=[],
                    source_versions=[],
                    retrieval_status="insufficient_evidence",
                    message="No knowledge base index available. Ingest government sources first.",
                ).to_dict()

        # Generate query embedding
        try:
            query_embedding = self.embedder.generate_query_embedding(query)
        except EmbeddingError as exc:
            logger.exception("Query embedding failed")
            return RetrievalResult(
                query=query,
                results=[],
                citations=[],
                source_versions=[],
                retrieval_status="error",
                message=f"Embedding generation failed: {exc}",
            ).to_dict()

        # Search FAISS
        raw_results = self.index.search(query_embedding, top_k=k)

        if not raw_results:
            return RetrievalResult(
                query=query,
                results=[],
                citations=[],
                source_versions=[],
                retrieval_status="insufficient_evidence",
                message="No relevant passages found in the knowledge base.",
            ).to_dict()

        # Fetch metadata for each result
        chunk_ids = [cid for cid, _ in raw_results]
        records = self.metadata_store.get_many(chunk_ids)

        results: list[dict[str, Any]] = []
        citations: list[dict[str, Any]] = []
        source_versions: list[dict[str, Any]] = []
        seen_sources: set[str] = set()

        for (chunk_id, score), record in zip(raw_results, records):
            if record is None:
                logger.warning("No metadata for chunk %s", chunk_id)
                continue
            result = self._build_result_record(record, score)
            results.append(result)

            citation = self._build_citation(record, score)
            citations.append(citation)

            source_id = record.get("source_id", "")
            if source_id and source_id not in seen_sources:
                seen_sources.add(source_id)
                source_versions.append(
                    {
                        "source_id": source_id,
                        "document_title": record.get("document_title"),
                        "authority": record.get("authority"),
                        "source_url": record.get("source_url"),
                        "version": record.get("version"),
                        "verification_status": record.get(
                            "verification_status", "pending"
                        ),
                        "retrieved_at": record.get("retrieved_at"),
                    }
                )

        # Evidence validation
        validation = self.validator.validate(query, results, business_context)
        conflicts = self.conflict_detector.detect(results)

        retrieval_status = "success"
        messages: list[str] = []
        if validation.get("insufficient"):
            retrieval_status = "insufficient_evidence"
            messages.append(validation.get("message", "Insufficient verified information is available to answer this question."))
        if conflicts:
            retrieval_status = "conflicting_evidence"
            messages.append(
                f"Conflicting source passages detected: {len(conflicts)} conflict(s)"
            )
        if not results:
            retrieval_status = "insufficient_evidence"
            messages.append("No relevant passages found in the knowledge base.")

        message = " ".join(messages) if messages else None

        return RetrievalResult(
            query=query,
            results=results,
            citations=citations,
            source_versions=source_versions,
            retrieval_status=retrieval_status,
            message=message,
        ).to_dict()

    @staticmethod
    def _build_result_record(record: dict[str, Any], score: float) -> dict[str, Any]:
        return {
            "chunk_id": record.get("chunk_id"),
            "text": record.get("text"),
            "source_id": record.get("source_id"),
            "document_title": record.get("document_title"),
            "authority": record.get("authority"),
            "page_number": record.get("page_number"),
            "section": record.get("section"),
            "source_url": record.get("source_url"),
            "similarity_score": round(score, 4),
            "verification_status": record.get("verification_status", "pending"),
            "retrieved_at": record.get("retrieved_at"),
            "extraction_method": record.get("extraction_method"),
        }

    @staticmethod
    def _build_citation(record: dict[str, Any], score: float) -> dict[str, Any]:
        return {
            "source_id": record.get("source_id"),
            "document_title": record.get("document_title"),
            "authority": record.get("authority"),
            "page_number": record.get("page_number"),
            "section": record.get("section"),
            "source_url": record.get("source_url"),
            "retrieved_at": record.get("retrieved_at"),
            "verification_status": record.get("verification_status", "pending"),
            "similarity_score": round(score, 4),
            "excerpt": record.get("text"),
        }


# ---------------------------------------------------------------------------
# Module-level convenience functions matching the Person 1 integration contract.
# `from rag.retrieval.engine import retrieve_guidance` works directly.
# ---------------------------------------------------------------------------

_default_engine: RetrievalEngine | None = None


def _get_default_engine() -> RetrievalEngine:
    global _default_engine
    if _default_engine is None:
        _default_engine = RetrievalEngine()
    return _default_engine


def retrieve_guidance(
    query: str,
    business_context: dict[str, Any] | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    """Retrieve relevant government guidance for a query.

    Standalone convenience wrapper around :meth:`RetrievalEngine.retrieve_guidance`
    so the function can be imported directly:

        from rag.retrieval.engine import retrieve_guidance

    Args:
        query: Natural-language user query.
        business_context: Optional business profile context.
        top_k: Maximum number of results to return.

    Returns:
        Dict matching the retrieve_guidance output contract.
    """
    return _get_default_engine().retrieve_guidance(
        query=query, business_context=business_context, top_k=top_k
    )
