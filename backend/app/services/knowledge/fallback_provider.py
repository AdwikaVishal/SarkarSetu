"""Fallback government knowledge provider.

Wraps the UnavailableGovernmentKnowledgeProvider to provide a
consistent interface when no retrieval provider is configured.

This provider should be used when Saatvika's RAG implementation
is not yet available. It clearly reports that retrieval is not
available rather than returning fabricated results.
"""

import logging
from uuid import UUID

from app.schemas.agents import RetrievalSource
from app.services.retrieval import UnavailableGovernmentKnowledgeProvider

logger = logging.getLogger(__name__)


class FallbackKnowledgeProvider:
    """Fallback provider that delegates to UnavailableGovernmentKnowledgeProvider.

    This provider is used when no real retrieval provider is configured.
    It always returns empty results and logs a warning, ensuring that
    agents correctly handle the unavailability of retrieval.
    """

    def __init__(self) -> None:
        self._provider = UnavailableGovernmentKnowledgeProvider()
        self.enabled = False

    async def retrieve(
        self,
        query: str,
        *,
        user_id: UUID,
        conversation_id: UUID,
        filters: dict[str, object] | None = None,
        limit: int = 5,
    ) -> list[RetrievalSource]:
        """Return empty results - no retrieval provider connected.

        Args:
            query: Search query describing what information is needed.
            user_id: Authenticated user ID for audit logging.
            conversation_id: Conversation ID for context.
            filters: Optional filters (scheme name, department, state, etc.).
            limit: Maximum number of results to return.

        Returns:
            Empty list - no retrieval results available.
        """
        logger.warning(
            "FallbackKnowledgeProvider returning empty results - "
            "no retrieval provider configured",
            extra={
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "query": query[:200],
            },
        )
        return []


def get_fallback_provider() -> FallbackKnowledgeProvider:
    """Factory function to create a FallbackKnowledgeProvider instance.

    Returns:
        A configured FallbackKnowledgeProvider instance.
    """
    return FallbackKnowledgeProvider()
