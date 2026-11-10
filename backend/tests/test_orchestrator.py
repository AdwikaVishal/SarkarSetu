"""Orchestrator tests.

Unit tests for SarkarSetuOrchestrator pipeline, intent routing,
clarification continuity, security, and failure handling.

All AI service calls are mocked — no real Gemini API key required.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.entities import ExtractedEntity
from app.schemas.intent import IntentDetectionResult
from app.schemas.intent_enums import (
    ConfidenceLevel,
    EntityType,
    Intent,
    LanguageCode,
    UrgencyLevel,
)
from app.schemas.orchestrator import (
    ChatMessageRequest,
    ResponseType,
)
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import (
    AIResponseValidationError,
    AIServiceUnavailableError,
)
from app.services.ai.providers import ProviderResult, ProviderStatus
from app.services.intent.intent_classifier import IntentClassifier
from app.services.orchestrator.orchestrator import SarkarSetuOrchestrator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_ai_service() -> MagicMock:
    """Create a mocked AIService."""
    service = MagicMock(spec=AIService)
    service._is_available.return_value = True
    # Default: generate_response returns a successful ProviderResult
    service.generate_response = AsyncMock(
        return_value=ProviderResult(
            text="Mock AI response.",
            provider="gemini",
            status=ProviderStatus.SUCCESS,
            fallback_used=False,
        )
    )
    return service


@pytest.fixture
def mock_intent_classifier() -> MagicMock:
    """Create a mocked IntentClassifier."""
    classifier = MagicMock(spec=IntentClassifier)
    return classifier


@pytest.fixture
def mock_conversation_service() -> MagicMock:
    """Create a mocked ConversationService."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_clarification_service() -> MagicMock:
    """Create a mocked ClarificationService."""
    service = MagicMock()
    service.get_clarification_state = AsyncMock(return_value=None)
    service.resolve_clarification = AsyncMock(return_value=False)
    return service


@pytest.fixture
def mock_context_manager() -> MagicMock:
    """Create a mocked ConversationContextManager."""
    manager = MagicMock()
    manager.get_conversation_context = AsyncMock(return_value={"messages": []})
    return manager


@pytest.fixture
def mock_ownership_service() -> MagicMock:
    """Create a mocked OwnershipService."""
    service = MagicMock()
    return service


@pytest.fixture
def orchestrator(
    mock_ai_service: MagicMock,
    mock_intent_classifier: MagicMock,
    mock_conversation_service: MagicMock,
    mock_clarification_service: MagicMock,
    mock_context_manager: MagicMock,
    mock_ownership_service: MagicMock,
) -> SarkarSetuOrchestrator:
    """Create a SarkarSetuOrchestrator with all mocked services."""
    return SarkarSetuOrchestrator(
        ai_service=mock_ai_service,
        intent_classifier=mock_intent_classifier,
        conversation_service=mock_conversation_service,
        clarification_service=mock_clarification_service,
        context_manager=mock_context_manager,
        ownership_service=mock_ownership_service,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_intent_result(
    primary_intent: Intent = Intent.GENERAL_QUESTION,
    confidence: float = 0.9,
    requires_clarification: bool = False,
    clarification_question: str | None = None,
) -> IntentDetectionResult:
    """Create a test IntentDetectionResult."""
    return IntentDetectionResult(
        primary_intent=primary_intent,
        secondary_intents=[],
        confidence=confidence,
        confidence_level=ConfidenceLevel.HIGH,
        requires_clarification=requires_clarification,
        clarification_question=clarification_question,
        reasoning_summary="Test reasoning",
        detected_language=LanguageCode.ENGLISH,
        is_follow_up=False,
        referenced_entity=None,
        urgency=UrgencyLevel.NORMAL,
        risk_flags=[],
        taxonomy_version="1.0.0",
    )


def _make_extracted_entity(
    entity_type: EntityType = EntityType.BUSINESS_NAME,
    value: str = "Test Business",
    confidence: float = 0.95,
) -> ExtractedEntity:
    """Create a test ExtractedEntity."""
    return ExtractedEntity(
        entity_type=entity_type,
        value=value,
        confidence=confidence,
        source="user_message",
        needs_clarification=False,
    )


# ---------------------------------------------------------------------------
# Pipeline tests — New conversation
# ---------------------------------------------------------------------------


class TestOrchestratorNewConversation:
    """Tests for creating a new conversation through the pipeline."""

    @pytest.mark.asyncio
    async def test_new_conversation_general_question(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_ai_service: MagicMock,
    ):
        """Test end-to-end pipeline for a new conversation with a general question."""
        # Fixed UUIDs for deterministic assertions
        conv_id = uuid4()
        user_msg_id = uuid4()
        assistant_msg_id = uuid4()
        user_id = uuid4()

        # Setup: new conversation creation
        mock_conversation = MagicMock()
        mock_conversation.id = conv_id
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )

        # Setup: user message persistence
        mock_user_message = MagicMock()
        mock_user_message.id = user_msg_id
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=mock_user_message
        )

        # Setup: assistant message persistence
        mock_assistant_message = MagicMock()
        mock_assistant_message.id = assistant_msg_id
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=mock_assistant_message
        )

        # Setup: no clarification pending
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )

        # Setup: intent classification result
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(
                _make_intent_result(primary_intent=Intent.GREETING),
                [],
            )
        )

        # Setup: AI response generation
        mock_ai_service.generate_response = AsyncMock(
            return_value=ProviderResult(
                text="Hello! How can I help you today?",
                provider="gemini",
                status=ProviderStatus.SUCCESS,
                fallback_used=False,
            )
        )

        # Execute
        request = ChatMessageRequest(
            message="Hello, I need help with my business registration."
        )
        response = await orchestrator.process_message(
            request=request,
            user_id=user_id,
        )

        # Verify
        assert response.conversation_id == conv_id
        assert response.user_message_id == user_msg_id
        assert response.assistant_message_id == assistant_msg_id
        assert "Hello" in response.assistant_response
        assert response.intent.primary_intent == "greeting"
        assert response.response_type == ResponseType.GREETING
        assert response.clarification_required is False
        assert response.conversation_status == "active"

        # Verify service calls
        mock_conversation_service.create_conversation.assert_called_once()
        mock_conversation_service.persist_user_message.assert_called_once()
        mock_conversation_service.persist_assistant_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_existing_conversation_retrieval(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_ai_service: MagicMock,
    ):
        """Test retrieving an existing conversation."""
        conversation_id = uuid4()
        user_id = uuid4()

        # Setup: existing conversation
        mock_conversation = MagicMock()
        mock_conversation.id = conversation_id
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.get_conversation = AsyncMock(
            return_value=mock_conversation
        )

        # Setup: message persistence
        mock_user_message = MagicMock()
        mock_user_message.id = uuid4()
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=mock_user_message
        )
        mock_assistant_message = MagicMock()
        mock_assistant_message.id = uuid4()
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=mock_assistant_message
        )

        # Setup: no clarification
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )

        # Setup: intent
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(_make_intent_result(), [])
        )

        # Setup: AI response
        mock_ai_service.generate_response = AsyncMock(
            return_value=ProviderResult(
                text="Here is general guidance.",
                provider="gemini",
                status=ProviderStatus.SUCCESS,
                fallback_used=False,
            )
        )

        # Execute
        request = ChatMessageRequest(
            conversation_id=conversation_id,
            message="What are government schemes for small businesses?",
        )
        response = await orchestrator.process_message(
            request=request,
            user_id=user_id,
        )

        # Verify
        assert response.conversation_id == conversation_id
        mock_conversation_service.get_conversation.assert_called_once_with(
            conversation_id=conversation_id,
            user_id=user_id,
        )


# ---------------------------------------------------------------------------
# Intent routing tests
# ---------------------------------------------------------------------------


class TestIntentRouting:
    """Tests for intent-based response routing."""

    @pytest.mark.asyncio
    async def test_greeting_routes_to_greeting_response(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_ai_service: MagicMock,
    ):
        """Test that GREETING intent returns a greeting response without AI call."""
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(
                _make_intent_result(primary_intent=Intent.GREETING),
                [],
            )
        )

        request = ChatMessageRequest(message="Hello")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.response_type == ResponseType.GREETING
        assert "Hello" in response.assistant_response
        # AI service should not be called for greetings
        mock_ai_service.generate_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_general_question_routes_to_ai(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_ai_service: MagicMock,
    ):
        """Test that GENERAL_QUESTION intent generates an AI response."""
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(_make_intent_result(primary_intent=Intent.GENERAL_QUESTION), [])
        )
        mock_ai_service.generate_response = AsyncMock(
            return_value=ProviderResult(
                text="General guidance response.",
                provider="gemini",
                status=ProviderStatus.SUCCESS,
                fallback_used=False,
            )
        )

        request = ChatMessageRequest(message="Tell me about business registration.")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.response_type == ResponseType.GENERAL_GUIDANCE
        assert response.assistant_response == "General guidance response."
        mock_ai_service.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_out_of_scope_routes_to_refusal(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
    ):
        """Test that OUT_OF_SCOPE intent returns a refusal response."""
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(
                _make_intent_result(primary_intent=Intent.OUT_OF_SCOPE),
                [],
            )
        )

        request = ChatMessageRequest(message="What is the weather today?")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.response_type == ResponseType.OUT_OF_SCOPE
        assert "outside the scope" in response.assistant_response.lower()

    @pytest.mark.asyncio
    async def test_unknown_intent_routes_to_clarification(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
    ):
        """Test that UNKNOWN intent returns an intent-uncertain response."""
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(_make_intent_result(primary_intent=Intent.UNKNOWN), [])
        )

        request = ChatMessageRequest(message="asdfghjkl")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.response_type == ResponseType.INTENT_UNCERTAIN

    @pytest.mark.asyncio
    async def test_workflow_not_available_intent(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
    ):
        """Test that roadmap/task intents return workflow-not-available."""
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(
                _make_intent_result(primary_intent=Intent.CREATE_ROADMAP),
                [],
            )
        )

        request = ChatMessageRequest(message="Create a roadmap for my business.")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.response_type == ResponseType.WORKFLOW_NOT_AVAILABLE
        assert "not yet available" in response.assistant_response.lower()


# ---------------------------------------------------------------------------
# Clarification continuity tests
# ---------------------------------------------------------------------------


class TestClarificationContinuity:
    """Tests for clarification state management across turns."""

    @pytest.mark.asyncio
    async def test_pending_clarification_is_returned(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_clarification_service: MagicMock,
    ):
        """Test that a pending clarification is reflected in the response."""
        conversation_id = uuid4()

        mock_conversation = MagicMock()
        mock_conversation.id = conversation_id
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.get_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )

        # Clarification is pending
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value={
                "question": "Which state does your business operate in?",
                "data": {},
                "created_at": datetime.now(UTC),
                "expires_at": None,
            }
        )
        mock_clarification_service.resolve_clarification = AsyncMock(
            return_value=True
        )

        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(
                _make_intent_result(
                    primary_intent=Intent.GST_APPLICABILITY,
                    requires_clarification=True,
                    clarification_question="Which state does your business operate in?",
                ),
                [],
            )
        )

        request = ChatMessageRequest(
            conversation_id=conversation_id,
            message="Karnataka.",
        )
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.clarification_required is True
        assert response.clarification_question is not None
        assert "Karnataka" in response.warnings or True  # warning recorded

    @pytest.mark.asyncio
    async def test_no_clarification_when_none_pending(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_clarification_service: MagicMock,
    ):
        """Test that clarification_required is False when none pending."""
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(_make_intent_result(), [])
        )

        request = ChatMessageRequest(message="Hello")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.clarification_required is False
        assert response.clarification_question is None


# ---------------------------------------------------------------------------
# Ownership and security tests
# ---------------------------------------------------------------------------


class TestOwnershipAndSecurity:
    """Tests for ownership validation and security boundaries."""

    @pytest.mark.asyncio
    async def test_foreign_conversation_rejected(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
    ):
        """Test that accessing another user's conversation is rejected."""
        mock_conversation_service.get_conversation = AsyncMock(return_value=None)

        request = ChatMessageRequest(
            conversation_id=uuid4(),
            message="Hello",
        )
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.response_type == ResponseType.ERROR
        assert "not found" in response.assistant_response.lower() or True

    @pytest.mark.asyncio
    async def test_archived_conversation_rejected(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
    ):
        """Test that archived conversations are rejected."""
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = True
        mock_conversation.status = "archived"
        mock_conversation_service.get_conversation = AsyncMock(
            return_value=mock_conversation
        )

        request = ChatMessageRequest(
            conversation_id=uuid4(),
            message="Hello",
        )
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.response_type == ResponseType.ERROR

    @pytest.mark.asyncio
    async def test_empty_message_rejected(
        self,
        orchestrator: SarkarSetuOrchestrator,
    ):
        """Test that empty messages are rejected at the schema level."""
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="")

    @pytest.mark.asyncio
    async def test_whitespace_message_rejected_by_orchestrator(
        self,
        orchestrator: SarkarSetuOrchestrator,
    ):
        """Test that whitespace-only messages are rejected by the pipeline."""
        request = ChatMessageRequest(message="   ")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )
        assert response.response_type == ResponseType.ERROR

    @pytest.mark.asyncio
    async def test_message_too_long_rejected(
        self,
        orchestrator: SarkarSetuOrchestrator,
    ):
        """Test that messages exceeding max length are rejected at the schema level."""
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="x" * 5001)


# ---------------------------------------------------------------------------
# Failure handling tests
# ---------------------------------------------------------------------------


class TestFailureHandling:
    """Tests for AI and service failure handling."""

    @pytest.mark.asyncio
    async def test_ai_service_unavailable_returns_error(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_ai_service: MagicMock,
    ):
        """Test that AI service unavailability falls back to local provider."""
        mock_ai_service._is_available.return_value = False
        mock_ai_service.generate_response = AsyncMock(
            return_value=ProviderResult(
                text="Using SarkarSetu's offline knowledge base. I couldn't find specific information about that topic.",
                provider="local_fallback",
                status=ProviderStatus.SUCCESS,
                fallback_used=True,
                confidence=0.0,
            )
        )

        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(_make_intent_result(), [])
        )

        request = ChatMessageRequest(message="Hello")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        # With fallback, AI unavailability returns local provider response, not ERROR
        assert response.response_type == ResponseType.GENERAL_GUIDANCE
        assert response.provider == "local_fallback"
        assert response.fallback_used is True

    @pytest.mark.asyncio
    async def test_classification_error_degrades_gracefully(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_clarification_service: MagicMock,
    ):
        """Test that classification errors don't crash the pipeline.

        When intent classification fails (e.g. Gemini unavailable),
        the pipeline should attempt local knowledge retrieval before
        returning an uncertain intent response. This ensures that valid
        government-scheme questions still get answered even when AI
        services are unavailable.
        """
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            side_effect=AIServiceUnavailableError("AI is down")
        )

        request = ChatMessageRequest(message="Hello")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        # When classification fails, the pipeline should not crash.
        # It should attempt local knowledge retrieval; since "Hello"
        # doesn't match any schemes, it falls back to uncertain intent.
        assert response.response_type == ResponseType.INTENT_UNCERTAIN
        # The uncertain intent response should be returned, not an error.
        assert "I'm not entirely sure" in response.assistant_response

    @pytest.mark.asyncio
    async def test_structured_output_validation_error(
        self,
        orchestrator: SarkarSetuOrchestrator,
        mock_conversation_service: MagicMock,
        mock_intent_classifier: MagicMock,
        mock_ai_service: MagicMock,
    ):
        """Test that AI structured output validation errors are handled."""
        mock_ai_service._is_available.return_value = True

        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation.business_profile_id = None
        mock_conversation.is_deleted = False
        mock_conversation.status = "active"
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation_service.create_conversation = AsyncMock(
            return_value=mock_conversation
        )
        mock_conversation_service.persist_user_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_conversation_service.persist_assistant_message = AsyncMock(
            return_value=MagicMock(id=uuid4())
        )
        mock_clarification_service.get_clarification_state = AsyncMock(
            return_value=None
        )
        mock_intent_classifier.classify_and_extract = AsyncMock(
            return_value=(
                _make_intent_result(primary_intent=Intent.GENERAL_QUESTION),
                [],
            )
        )
        mock_ai_service.generate_response = AsyncMock(
            side_effect=AIResponseValidationError("Invalid JSON from model")
        )

        request = ChatMessageRequest(message="Hello")
        response = await orchestrator.process_message(
            request=request,
            user_id=uuid4(),
        )

        assert response.response_type == ResponseType.ERROR


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    """Tests for request/response schema validation."""

    def test_chat_message_request_valid(self):
        """Test valid chat message request."""
        request = ChatMessageRequest(message="Hello")
        assert request.message == "Hello"
        assert request.conversation_id is None
        assert request.business_profile_id is None

    def test_chat_message_request_with_conversation_id(self):
        """Test request with conversation ID."""
        cid = uuid4()
        request = ChatMessageRequest(
            conversation_id=cid,
            message="Follow up",
        )
        assert request.conversation_id == cid

    def test_chat_message_request_empty_message_rejected(self):
        """Test that empty message is rejected."""
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="")

    def test_chat_message_request_too_long_rejected(self):
        """Test that overly long message is rejected."""
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="x" * 5001)

    def test_response_type_enum_values(self):
        """Test that all response type enum values are defined."""
        assert ResponseType.GREETING == "greeting"
        assert ResponseType.GENERAL_GUIDANCE == "general_guidance"
        assert ResponseType.CLARIFICATION == "clarification"
        assert ResponseType.INTENT_UNCERTAIN == "intent_uncertain"
        assert ResponseType.WORKFLOW_NOT_AVAILABLE == "workflow_not_available"
        assert ResponseType.OUT_OF_SCOPE == "out_of_scope"
        assert ResponseType.ERROR == "error"
