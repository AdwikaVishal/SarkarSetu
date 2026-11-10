"""Integration bridge between the RAG subsystem and Person 1's backend.

Implements the `GovernmentKnowledgeProvider` protocol defined in
`backend/app/services/retrieval.py` so the DocumentAgent, DiscoveryAgent,
and ComplianceAgent can consume official-source evidence from this RAG
layer without depending on its internals.

Usage in backend:

    from rag.integration.knowledge_provider import RagKnowledgeProvider
    provider = RagKnowledgeProvider()
    registry.register("DocumentAgent", DocumentAgent(..., retrieval_provider=provider, ...))
"""

from __future__ import annotations

import logging
from typing import Any

from rag.config.logging_config import get_logger
from rag.retrieval.engine import RetrievalEngine

logger = get_logger("integration")


class RagKnowledgeProvider:
    """Concrete GovernmentKnowledgeProvider backed by the RAG retrieval engine."""

    def __init__(self, engine: RetrievalEngine | None = None) -> None:
        self.engine = engine or RetrievalEngine()
        self._RetrievalSource: Any = None

    def _get_retrieval_source(self) -> Any:
        """Lazily import the backend RetrievalSource schema."""
        if self._RetrievalSource is not None:
            return self._RetrievalSource
        try:
            from app.schemas.agents import RetrievalSource  # noqa: PLC0415

            self._RetrievalSource = RetrievalSource
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Backend RetrievalSource schema unavailable: %s", exc
            )
            self._RetrievalSource = None
        return self._RetrievalSource

    async def retrieve(
        self,
        query: str,
        *,
        user_id: Any,
        conversation_id: Any,
        filters: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[Any]:
        """Retrieve relevant government sources for a query.

        Returns RetrievalSource objects when the backend schema is
        available, otherwise plain dicts. Never raises on retrieval
        failure so agents degrade gracefully.
        """
        del user_id, conversation_id  # RAG layer is stateless
        RetrievalSource = self._get_retrieval_source()

        try:
            result = self.engine.retrieve_guidance(
                query=query,
                business_context=filters or {},
                top_k=limit,
            )
        except Exception as exc:  # noqa: BLE001 - never break the agent
            logger.exception("RAG retrieval failed")
            return []

        if result.get("retrieval_status") == "insufficient_evidence":
            return []

        sources: list[Any] = []
        for item in result.get("results", []):
            page = item.get("page_number")
            data = {
                "document_id": item.get("chunk_id"),
                "source_title": item.get("document_title"),
                "issuing_authority": item.get("authority"),
                "source_url": item.get("source_url"),
                "publication_date": None,
                "relevant_excerpt": item.get("text"),
                "page_or_section": str(page) if page is not None else None,
                "retrieval_score": item.get("similarity_score"),
                "document_version": None,
            }
            if RetrievalSource is not None:
                try:
                    sources.append(RetrievalSource(**data))  # type: ignore
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to build RetrievalSource: %s", exc)
                    sources.append(data)
            else:
                sources.append(data)
        return sources
