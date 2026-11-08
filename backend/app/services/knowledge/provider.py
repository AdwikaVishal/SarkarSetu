"""Government knowledge provider implementation.

Provides a concrete implementation of the GovernmentKnowledgeProvider protocol
using a fixture-backed development dataset. This provider is clearly marked
as development-only and must not be used in production without replacement
by Saatvika's RAG implementation.

The provider supports dependency injection so it can be replaced without
changing agent code.
"""

import logging
from uuid import UUID

from app.schemas.agents import RetrievalSource
from app.services.knowledge.citation_builder import CitationBuilder
from app.services.knowledge.retriever import Retriever
from app.services.knowledge.source_validator import SourceValidator

logger = logging.getLogger(__name__)


class FixtureKnowledgeProvider:
    """Fixture-backed government knowledge provider (development only).

    This provider uses a static fixture dataset for development and testing.
    It is NOT suitable for production use. Saatvika's RAG implementation
    should replace this provider before production deployment.

    The provider implements the GovernmentKnowledgeProvider protocol and
    can be swapped out without changing agent code.
    """

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.retriever = Retriever()
        self.validator = SourceValidator()
        self.citation_builder = CitationBuilder()

    async def retrieve(
        self,
        query: str,
        *,
        user_id: UUID,
        conversation_id: UUID,
        filters: dict[str, object] | None = None,
        limit: int = 5,
    ) -> list[RetrievalSource]:
        """Retrieve relevant government documents for a query.

        Args:
            query: Search query describing what information is needed.
            user_id: Authenticated user ID for audit logging.
            conversation_id: Conversation ID for context.
            filters: Optional filters (scheme name, department, state, etc.).
            limit: Maximum number of results to return.

        Returns:
            List of RetrievalSource objects. Empty list if provider is
            disabled or no results found.

        Raises:
            ValueError: If the provider is not configured (provider_enabled=False).
        """
        if not self.enabled:
            logger.warning(
                "FixtureKnowledgeProvider is disabled",
                extra={
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "query": query[:200],
                },
            )
            return []

        try:
            # Step 1: Normalize query
            normalized_query = self.retriever.normalize_query(query)

            # Step 2: Extract filters from query context
            effective_filters = self.retriever.build_filters(
                query=normalized_query,
                explicit_filters=filters or {},
            )

            # Step 3: Retrieve candidates from fixture index
            candidates = self.retriever.retrieve_candidates(
                query=normalized_query,
                filters=effective_filters,
                limit=limit * 2,  # Retrieve more for filtering/reranking
            )

            # Step 4: Validate source metadata and provenance
            validated = self.validator.validate_sources(candidates)

            # Step 5: Rerank results
            ranked = self.retriever.rerank(validated, normalized_query)

            # Step 6: Deduplicate overlapping chunks
            deduplicated = self.retriever.deduplicate(ranked)

            # Step 7: Limit results
            limited = deduplicated[:limit]

            # Step 8: Build citations
            sources = self.citation_builder.build_sources(limited)

            logger.info(
                "Knowledge retrieval completed",
                extra={
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "query": query[:200],
                    "candidates_returned": len(sources),
                },
            )
            return sources

        except Exception as exc:  # noqa: BLE001 - safe error handling
            logger.exception(
                "Knowledge retrieval failed",
                extra={
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "query": query[:200],
                    "error": str(exc),
                },
            )
            return []


def get_fixture_provider(enabled: bool = True) -> FixtureKnowledgeProvider:
    """Factory function to create a FixtureKnowledgeProvider instance.

    Args:
        enabled: Whether the provider is active. When disabled, returns
            empty results without querying the fixture index.

    Returns:
        A configured FixtureKnowledgeProvider instance.
    """
    return FixtureKnowledgeProvider(enabled=enabled)
