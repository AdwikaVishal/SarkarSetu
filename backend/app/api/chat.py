"""Chat API router.

Provides the end-to-end conversational endpoint:
- POST /api/v1/chat/message - Process a user message through the orchestrator
- GET /api/v1/chat/conversations/{conversation_id}/status - Get conversation status
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ai import get_ai_service
from app.api.dependencies import get_current_active_user
from app.core.config import settings
from app.database.connection import get_db
from app.models.user import User
from app.schemas.orchestrator import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationStatusResponse,
)
from app.services.agents.agent_registry import AgentRegistry
from app.services.ai.ai_service import AIService
from app.services.conversation.clarification_service import ClarificationService
from app.services.conversation.context_manager import (
    ConversationContextManager,
)
from app.services.conversation.conversation_service import ConversationService
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.eligibility_engine.rule_evaluator import RuleEvaluator
from app.services.eligibility_engine.rule_registry import RuleRegistry
from app.services.intent.intent_classifier import IntentClassifier
from app.services.knowledge.provider import get_fixture_provider
from app.services.orchestrator.orchestrator import SarkarSetuOrchestrator
from app.services.ownership import OwnershipService

# Person 2 RAG subsystem integration (optional hard dependency).
# Falls back to the fixture provider when rag/ is not on the path or its
# dependencies are missing, so the backend keeps starting in dev.
try:  # noqa: E401
    from rag.integration.knowledge_provider import RagKnowledgeProvider

    _RAG_PROVIDER_AVAILABLE = True
except Exception:  # pragma: no cover - backend runs without rag/ deps
    RagKnowledgeProvider = None  # type: ignore[assignment,misc]
    _RAG_PROVIDER_AVAILABLE = False

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    """Dependency to get ConversationService instance."""
    return ConversationService(db)


async def get_clarification_service(
    db: AsyncSession = Depends(get_db),
) -> ClarificationService:
    """Dependency to get ClarificationService instance."""
    return ClarificationService(db)


async def get_context_manager(
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationContextManager:
    """Dependency to get ConversationContextManager instance."""
    return ConversationContextManager(db=conversation_service.db)


async def get_ownership_service(
    db: AsyncSession = Depends(get_db),
) -> OwnershipService:
    """Dependency to get OwnershipService instance."""
    return OwnershipService(db)


async def get_intent_classifier(
    ai_service: AIService = Depends(get_ai_service),
) -> IntentClassifier:
    """Dependency to get IntentClassifier instance."""
    return IntentClassifier(ai_service)


async def get_agent_registry(
    ai_service: AIService = Depends(get_ai_service),
    db: AsyncSession = Depends(get_db),
) -> AgentRegistry:
    """Dependency to get AgentRegistry instance with eligibility engine
    and knowledge retrieval provider."""
    registry = RuleRegistry(db)
    engine = EligibilityEngine(
        registry=registry,
        evaluator=RuleEvaluator(),
    )
    # Wire up the knowledge retrieval provider.
    # Prefer Person 2's RAG-backed GovernmentKnowledgeProvider; fall back to
    # the fixture provider when the RAG subsystem is unavailable.
    if _RAG_PROVIDER_AVAILABLE and RagKnowledgeProvider is not None:
        knowledge_provider = RagKnowledgeProvider()
    else:
        knowledge_provider = get_fixture_provider(
            enabled=settings.knowledge_retrieval_enabled
        )
    return AgentRegistry(
        ai_service=ai_service,
        retrieval_provider=knowledge_provider,
        eligibility_evaluator=engine,
    )


async def get_orchestrator(
    ai_service: AIService = Depends(get_ai_service),
    intent_classifier: IntentClassifier = Depends(get_intent_classifier),
    conversation_service: ConversationService = Depends(get_conversation_service),
    clarification_service: ClarificationService = Depends(get_clarification_service),
    context_manager: ConversationContextManager = Depends(get_context_manager),
    ownership_service: OwnershipService = Depends(get_ownership_service),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
) -> SarkarSetuOrchestrator:
    """Dependency to get SarkarSetuOrchestrator instance."""
    return SarkarSetuOrchestrator(
        ai_service=ai_service,
        intent_classifier=intent_classifier,
        conversation_service=conversation_service,
        clarification_service=clarification_service,
        context_manager=context_manager,
        ownership_service=ownership_service,
        agent_registry=agent_registry,
    )


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description=(
        "Process a user message through the full orchestration pipeline: "
        "validate, load/create conversation, persist user message, "
        "retrieve context, handle clarification, classify intent, "
        "generate assistant response, and persist assistant message."
    ),
)
async def send_message(
    request: ChatMessageRequest,
    orchestrator: SarkarSetuOrchestrator = Depends(get_orchestrator),
    current_user: User = Depends(get_current_active_user),
) -> ChatMessageResponse:
    """Send a message through the SarkarSetu AI orchestrator.

    Requires authentication. The user_id is taken from the JWT token,
    never from client input.
    """
    try:
        response = await orchestrator.process_message(
            request=request,
            user_id=current_user.id,
        )
    except Exception as exc:  # noqa: BLE001 - safe error response below
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Chat endpoint error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your message.",
        ) from exc

    return response


@router.get(
    "/conversations/{conversation_id}/status",
    response_model=ConversationStatusResponse,
    summary="Get conversation status",
    description=(
        "Retrieve the status of a conversation, including whether a "
        "clarification is pending and the associated business profile."
    ),
)
async def get_conversation_status(
    conversation_id: UUID,
    orchestrator: SarkarSetuOrchestrator = Depends(get_orchestrator),
    current_user: User = Depends(get_current_active_user),
) -> ConversationStatusResponse:
    """Get conversation status and clarification state.

    Requires authentication and conversation ownership.
    """
    conversation_status = await orchestrator.get_conversation_status(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    if conversation_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or not owned by user",
        )
    return conversation_status
