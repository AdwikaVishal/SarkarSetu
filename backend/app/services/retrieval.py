"""Government knowledge retrieval protocol.

Defines the interface that Saatvika's RAG/document retrieval layer
must implement. Agents depend on this protocol, not on any concrete
implementation.

If no stable retrieval interface exists, agents use the
UnavailableGovernmentKnowledgeProvider which gracefully reports
that retrieval is not available.
"""

import logging
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.schemas.agents import RetrievalSource

logger = logging.getLogger(__name__)


@runtime_checkable
class GovernmentKnowledgeProvider(Protocol):
    """Protocol for government document and scheme retrieval.

    Saatvika's RAG layer should implement this protocol. Agents
    call `retrieve` to obtain official-source evidence before
    making any claims about government schemes, rules, or
    requirements.
    """

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
            List of RetrievalSource objects with source references.
            Empty list if no results found or provider unavailable.

        Raises:
            Should not raise for normal unavailability; return empty
            list instead. May raise for configuration errors.
        """
        ...


class UnavailableGovernmentKnowledgeProvider:
    """Fallback implementation when no retrieval provider is connected.

    Agents using this provider will receive empty results and should
    return NEEDS_RETRIEVAL status with a clear message that
    official-source verification is required.
    """

    async def retrieve(
        self,
        query: str,
        *,
        user_id: UUID,
        conversation_id: UUID,
        filters: dict[str, object] | None = None,
        limit: int = 5,
    ) -> list[RetrievalSource]:
        """Return empty results — no retrieval provider connected."""
        logger.warning(
            "GovernmentKnowledgeProvider not available",
            extra={
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "query": query[:200],
            },
        )
        return []


def get_unavailable_provider() -> UnavailableGovernmentKnowledgeProvider:
    """Factory function to create an unavailable provider instance."""
    return UnavailableGovernmentKnowledgeProvider()
