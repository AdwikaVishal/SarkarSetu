"""Intent detection API router.

Provides intent classification and entity extraction endpoints:
- POST /api/v1/intent/classify - Classify intent
- POST /api/v1/intent/extract - Extract entities
- POST /api/v1/intent/analyze - Combined analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ai import get_ai_service
from app.api.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.business import BusinessProfile
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.intent import (
    EntityExtractionRequest,
    EntityExtractionResponse,
    IntentAnalysisRequest,
    IntentAnalysisResponse,
    IntentClassificationRequest,
    IntentClassificationResponse,
)
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import AIError, AIServiceUnavailableError
from app.services.intent.intent_classifier import IntentClassifier
from app.services.intent.intent_taxonomy import LanguageCode

router = APIRouter(prefix="/intent", tags=["intent"])


async def get_intent_classifier(
    ai_service: AIService = Depends(get_ai_service),
) -> IntentClassifier:
    """Dependency to get IntentClassifier instance."""
    return IntentClassifier(ai_service)


async def _get_user_business_profile(
    db: AsyncSession,
    user_id: str,
    business_profile_id: str,
) -> None:
    """Verify business profile belongs to user and is not archived.

    Args:
        db: Database session.
        user_id: ID of the authenticated user.
        business_profile_id: ID of the business profile.

    Raises:
        HTTPException: 404 if profile not found, not owned by user, or archived.
    """
    result = await db.execute(
        select(BusinessProfile).where(
            BusinessProfile.id == business_profile_id,
            BusinessProfile.user_id == user_id,
            BusinessProfile.is_deleted == False,  # noqa: E712
        )
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found",
        )


async def _get_user_conversation(
    db: AsyncSession,
    user_id: str,
    conversation_id: str,
) -> None:
    """Verify conversation belongs to user and its business profile
    (if any) also belongs to the user and is not archived.

    Args:
        db: Database session.
        user_id: ID of the authenticated user.
        conversation_id: ID of the conversation.

    Raises:
        HTTPException: 404 if conversation not found or not owned by user.
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.business_profile_id is not None:
        result = await db.execute(
            select(BusinessProfile).where(
                BusinessProfile.id == conversation.business_profile_id,
                BusinessProfile.user_id == user_id,
                BusinessProfile.is_deleted == False,  # noqa: E712
            )
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found or not owned by user",
            )


@router.post(
    "/classify",
    response_model=IntentClassificationResponse,
    summary="Classify intent",
    description="Classify user message intent using AI.",
)
async def classify_intent(
    request: IntentClassificationRequest,
    classifier: IntentClassifier = Depends(get_intent_classifier),
    current_user: User = Depends(get_current_active_user),
) -> IntentClassificationResponse:
    """Classify user message intent.

    Requires authentication. AI must be enabled via GEMINI_ENABLED=true
    and GEMINI_API_KEY must be configured.
    """
    try:
        result = await classifier.classify_intent(
            message=request.message,
            user_id=str(current_user.id),
            conversation_history=[],
            business_context=None,
        )
    except AIServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return IntentClassificationResponse(intent_detection=result)


@router.post(
    "/extract",
    response_model=EntityExtractionResponse,
    summary="Extract entities",
    description="Extract entities from a user message using AI.",
)
async def extract_entities(
    request: EntityExtractionRequest,
    classifier: IntentClassifier = Depends(get_intent_classifier),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EntityExtractionResponse:
    """Extract entities from a user message.

    Requires authentication. AI must be enabled.
    """
    # Verify business_profile ownership if provided
    if request.business_profile_id:
        await _get_user_business_profile(
            db, str(current_user.id), request.business_profile_id
        )

    # Verify conversation ownership if provided
    if request.conversation_id:
        await _get_user_conversation(
            db, str(current_user.id), request.conversation_id
        )

    try:
        entities = await classifier.extract_entities(
            message=request.message,
            business_context=None,
            conversation_history=[],
        )
    except AIServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return EntityExtractionResponse(
        entities=entities,
        detected_language=LanguageCode("en"),
    )


@router.post(
    "/analyze",
    response_model=IntentAnalysisResponse,
    summary="Intent and entity analysis",
    description="Combined intent classification and entity extraction.",
)
async def analyze_intent(
    request: IntentAnalysisRequest,
    classifier: IntentClassifier = Depends(get_intent_classifier),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IntentAnalysisResponse:
    """Perform combined intent classification and entity extraction.

    Requires authentication. AI must be enabled.
    """
    # Verify business_profile ownership if provided
    if request.business_profile_id:
        await _get_user_business_profile(
            db, str(current_user.id), request.business_profile_id
        )

    # Verify conversation ownership if provided
    if request.conversation_id:
        await _get_user_conversation(
            db, str(current_user.id), request.conversation_id
        )

    try:
        intent_result, entities = await classifier.classify_and_extract(
            message=request.message,
        )
    except AIServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return IntentAnalysisResponse(
        intent=intent_result,
        entities=entities,
        requires_clarification=intent_result.requires_clarification,
        clarification_question=intent_result.clarification_question,
        summary=intent_result.reasoning_summary,
    )
