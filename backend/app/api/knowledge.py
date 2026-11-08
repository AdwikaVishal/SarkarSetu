"""Knowledge retrieval API router.

Provides authenticated endpoints for government knowledge retrieval:

- POST /api/v1/knowledge/search - Search government knowledge base
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.orchestrator import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    RetrievalSourceResponse,
)
from app.services.knowledge.provider import FixtureKnowledgeProvider

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


async def get_knowledge_provider() -> FixtureKnowledgeProvider:
    """Dependency to get FixtureKnowledgeProvider instance."""
    from app.core.config import settings

    return FixtureKnowledgeProvider(enabled=settings.knowledge_retrieval_enabled)


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search government knowledge base",
    description=(
        "Search the government knowledge base for relevant documents, "
        "schemes, and regulations. Returns structured citations with "
        "source provenance."
    ),
)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    provider: FixtureKnowledgeProvider = Depends(get_knowledge_provider),
    current_user: User = Depends(get_current_active_user),
) -> KnowledgeSearchResponse:
    """Search the government knowledge base.

    Requires authentication. The user_id is taken from the JWT token,
    never from client input.

    Returns structured citations with source provenance for each result.
    """
    try:
        sources = await provider.retrieve(
            query=request.query,
            user_id=current_user.id,
            conversation_id=request.conversation_id or UUID(int=0),
            filters=request.filters,
            limit=request.limit or 5,
        )

        # Convert to response schema
        source_responses = [
            RetrievalSourceResponse(
                document_id=s.document_id,
                source_title=s.source_title,
                issuing_authority=s.issuing_authority,
                source_url=s.source_url,
                publication_date=s.publication_date,
                relevant_excerpt=s.relevant_excerpt,
                page_or_section=s.page_or_section,
                retrieval_score=s.retrieval_score,
                document_version=s.document_version,
            )
            for s in sources
        ]

        return KnowledgeSearchResponse(
            query=request.query,
            results=source_responses,
            total_count=len(source_responses),
            provider_enabled=provider.enabled,
        )

    except Exception as exc:  # noqa: BLE001 - safe error response
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Knowledge search error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while searching the knowledge base.",
        ) from exc
