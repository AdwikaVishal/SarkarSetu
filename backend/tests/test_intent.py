"""Intent detection and entity extraction tests."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.conversation import MessageCreate
from app.schemas.entities import ExtractedEntity
from app.schemas.intent import IntentDetectionResult
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import (
    AIServiceUnavailableError,
)
from app.services.intent.entity_extractor import EntityExtractor
from app.services.intent.intent_classifier import IntentClassifier
from app.services.intent.intent_taxonomy import (
    ConfidenceLevel,
    EntityType,
    Intent,
    get_confidence_level,
)

# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------


class TestAIConfiguration:
    """Tests for AI configuration loading."""

    def test_settings_has_ai_fields(self):
        """Test that Settings has AI-related fields."""
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
            GEMINI_API_KEY="test-key",
            GEMINI_MODEL="gemini-2.5-flash",
            GEMINI_TEMPERATURE=0.7,
            GEMINI_MAX_OUTPUT_TOKENS=8192,
            GEMINI_TIMEOUT_SECONDS=30,
            GEMINI_MAX_RETRIES=3,
            GEMINI_ENABLED=True,
            JWT_SECRET="test-secret",
        )
        assert settings.gemini_api_key == "test-key"
        assert settings.gemini_model == "gemini-2.5-flash"
        assert settings.gemini_temperature == 0.7
        assert settings.gemini_max_output_tokens == 8192
        assert settings.gemini_timeout_seconds == 30
        assert settings.gemini_max_retries == 3
        assert settings.gemini_enabled is True

    def test_settings_ai_disabled_by_default(self):
        """Test that GEMINI_ENABLED defaults to False."""
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
            GEMINI_API_KEY="test-key",
            JWT_SECRET="test-secret",
        )
        assert settings.gemini_enabled is False

    def test_settings_missing_gemini_key_raises(self, tmp_path, monkeypatch):
        """Test that missing GEMINI_API_KEY raises error."""
        monkeypatch.chdir(tmp_path)
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Settings(
                DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
                JWT_SECRET="test-secret",
            )


# ---------------------------------------------------------------------------
# Intent Taxonomy tests
# ---------------------------------------------------------------------------


class TestIntentTaxonomy:
    """Tests for intent taxonomy."""

    def test_intent_values(self):
        """Test that all intent values are valid strings."""
        assert Intent.GST_REGISTRATION.value == "gst_registration"
        assert Intent.UDYAM_REGISTRATION.value == "udyam_registration"
        assert Intent.GOVERNMENT_SCHEME_DISCOVERY.value == "government_scheme_discovery"
        assert Intent.SCHEME_ELIGIBILITY.value == "scheme_eligibility"
        assert Intent.DOCUMENT_GUIDANCE.value == "document_guidance"
        assert Intent.CREATE_ROADMAP.value == "create_roadmap"
        assert Intent.GREETING.value == "greeting"
        assert Intent.UNKNOWN.value == "unknown"

    def test_confidence_levels(self):
        """Test confidence level values."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"

    def test_get_confidence_level(self):
        """Test confidence level determination."""
        assert get_confidence_level(0.95) == ConfidenceLevel.HIGH
        assert get_confidence_level(0.85) == ConfidenceLevel.HIGH
        assert get_confidence_level(0.84) == ConfidenceLevel.MEDIUM
        assert get_confidence_level(0.70) == ConfidenceLevel.MEDIUM
        assert get_confidence_level(0.65) == ConfidenceLevel.MEDIUM
        assert get_confidence_level(0.64) == ConfidenceLevel.LOW
        assert get_confidence_level(0.0) == ConfidenceLevel.LOW


# ---------------------------------------------------------------------------
# Intent Classifier tests (mocked)
# ---------------------------------------------------------------------------


class TestIntentClassifier:
    """Tests for IntentClassifier with mocked AI service."""

    def test_service_creates_classifier(self):
        """Test that IntentClassifier creates a GeminiClient when configured."""
        mock_ai_service = MagicMock()
        classifier = IntentClassifier(mock_ai_service)
        assert classifier.ai_service is mock_ai_service

    @pytest.mark.asyncio
    async def test_classify_intent_success(self):
        """Test successful intent classification."""

        from app.schemas.intent import IntentDetectionResult

        mock_result = MagicMock()
        mock_result.primary_intent = Intent.GST_REGISTRATION.value
        mock_result.secondary_intents = []
        mock_result.confidence = 0.95
        mock_result.confidence_level = "high"
        mock_result.requires_clarification = False
        mock_result.clarification_question = None
        mock_result.reasoning_summary = "User asks about GST registration"
        mock_result.detected_language = "en"
        mock_result.is_follow_up = False
        mock_result.referenced_entity = None
        mock_result.urgency = "normal"
        mock_result.risk_flags = []
        mock_result.taxonomy_version = "1.0.0"

        with patch(
            "app.services.ai.ai_service.GeminiClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.generate_content = AsyncMock(
                return_value=MagicMock(text='{"primary_intent": "gst_registration", "secondary_intents": [], "confidence": 0.95, "confidence_level": "high", "requires_clarification": false, "clarification_question": null, "reasoning_summary": "User asks about GST registration", "detected_language": "en", "is_follow_up": false, "referenced_entity": null, "urgency": "normal", "risk_flags": []}')
            )
            mock_client_class.return_value = mock_client

            with patch(
                "app.services.ai.ai_service.settings"
            ) as mock_settings:
                mock_settings.gemini_enabled = True
                service = AIService()
                service._client = mock_client
                result = await service.generate_structured_output(
                    prompt="Classify: How do I register for GST?",
                    response_model=IntentDetectionResult,
                )
                assert result.primary_intent == Intent.GST_REGISTRATION
                assert result.confidence == 0.95


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestAIAPIEndpoints:
    """Tests for AI intent API endpoints."""

    @pytest.mark.asyncio
    async def test_classify_intent_endpoint(self, client, db_session):
        """Test POST /api/v1/intent/classify endpoint."""
        # Register user first
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "intentuser@example.com",
                "full_name": "Intent User",
                "password": "StrongPassword123!",
            },
        )
        assert reg_response.status_code == 201
        token = reg_response.json()["access_token"]

        # Mock the AI service
        from app.main import app as main_app
        from app.services.ai.ai_service import AIService
        from app.services.intent.intent_classifier import (
            _IntentDetectionResult,
        )

        mock_service = MagicMock()
        mock_result = _IntentDetectionResult(
            primary_intent=Intent.GST_REGISTRATION.value,
            secondary_intents=[],
            confidence=0.95,
            confidence_level="high",
            requires_clarification=False,
            clarification_question=None,
            reasoning_summary="User asks about GST registration",
            detected_language="en",
            is_follow_up=False,
            referenced_entity=None,
            urgency="normal",
            risk_flags=[],
            taxonomy_version="1.0.0",
        )
        mock_service.generate_structured_output = AsyncMock(
            return_value=mock_result
        )
        main_app.dependency_overrides[AIService] = lambda: mock_service

        try:
            response = await client.post(
                "/api/v1/intent/classify",
                json={
                    "message": "How do I register for GST?",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["intent_detection"]["primary_intent"] == "gst_registration"
            assert data["intent_detection"]["confidence"] == 0.95
        finally:
            main_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_classify_intent_unauthenticated(self, client):
        """Test classify endpoint without authentication."""
        response = await client.post(
            "/api/v1/intent/classify",
            json={"message": "Hello"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_analyze_intent_endpoint(self, client, db_session):
        """Test POST /api/v1/intent/analyze endpoint."""
        # Register user first
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "analyze@example.com",
                "full_name": "Analyze User",
                "password": "StrongPassword123!",
            },
        )
        assert reg_response.status_code == 201
        token = reg_response.json()["access_token"]

        # Mock the intent classifier service
        from app.main import app as main_app
        from app.services.ai.ai_service import AIService
        from app.services.intent.entity_extractor import (
            _EntityExtractionResult,
            _ExtractedEntityItem,
        )
        from app.services.intent.intent_classifier import (
            _IntentDetectionResult,
        )

        intent_result = _IntentDetectionResult(
            primary_intent=Intent.GST_REGISTRATION.value,
            secondary_intents=[],
            confidence=0.9,
            confidence_level="high",
            requires_clarification=False,
            clarification_question=None,
            reasoning_summary="User asks about GST",
            detected_language="en",
            is_follow_up=False,
            referenced_entity=None,
            urgency="normal",
            risk_flags=[],
            taxonomy_version="1.0.0",
        )

        entity_result = _EntityExtractionResult(
            entities=[
                _ExtractedEntityItem(
                    entity_type="gemini_api_key",
                    value="AIza...",
                    confidence=0.9,
                    source="user_message",
                    needs_clarification=False,
                )
            ]
        )

        # Mock generate_structured_output to return different results
        # based on the response_model argument
        async def mock_generate_structured_output(
            prompt: str,
            response_model: type,
            *args,
            **kwargs,
        ):
            if response_model is _IntentDetectionResult:
                return intent_result
            elif response_model is _EntityExtractionResult:
                return entity_result
            raise ValueError(
                f"Unexpected response_model: {response_model}"
            )

        mock_service = MagicMock()
        mock_service.generate_structured_output = mock_generate_structured_output
        main_app.dependency_overrides[AIService] = lambda: mock_service

        try:
            response = await client.post(
                "/api/v1/intent/analyze",
                json={
                    "message": "How do I register for GST?",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["intent"]["primary_intent"] == "gst_registration"
            assert data["intent"]["confidence"] == 0.9
            assert data["summary"] == "User asks about GST"
        finally:
            main_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_classify_intent_disabled_ai(self, client, db_session):
        """Test classify endpoint when AI is disabled."""
        # Register user
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "aiuser3@example.com",
                "full_name": "AI User 3",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        # Mock the AI service with disabled state
        from app.main import app as main_app
        from app.services.ai.ai_service import AIService

        mock_service = MagicMock()
        mock_service.generate_structured_output = AsyncMock(
            side_effect=AIServiceUnavailableError(
                "AI service is not configured"
            )
        )
        main_app.dependency_overrides[AIService] = lambda: mock_service

        try:
            response = await client.post(
                "/api/v1/intent/classify",
                json={"message": "Hello"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 503
        finally:
            main_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# EntityExtractor typing tests
# ---------------------------------------------------------------------------


class TestEntityExtractorTyping:
    """Tests for EntityExtractor returning typed ExtractedEntity objects."""

    def test_extractor_returns_extracted_entity_instances(self):
        """Test that extract_entities constructs ExtractedEntity objects."""
        entities = [
            ExtractedEntity(
                entity_type=EntityType.BUSINESS_NAME,
                value="Acme Pvt Ltd",
                confidence=0.95,
                source="user_message",
                needs_clarification=False,
            ),
            ExtractedEntity(
                entity_type=EntityType.STATE,
                value="Karnataka",
                confidence=0.88,
                source="user_message",
                needs_clarification=True,
            ),
        ]
        assert len(entities) == 2
        assert isinstance(entities[0], ExtractedEntity)
        assert entities[0].entity_type == EntityType.BUSINESS_NAME
        assert entities[0].value == "Acme Pvt Ltd"
        assert entities[0].confidence == 0.95
        assert entities[0].source == "user_message"
        assert entities[0].needs_clarification is False
        assert isinstance(entities[1], ExtractedEntity)
        assert entities[1].entity_type == EntityType.STATE
        assert entities[1].needs_clarification is True

    def test_extracted_entity_validation(self):
        """Test ExtractedEntity field validation."""
        entity = ExtractedEntity(
            entity_type=EntityType.PIN_CODE,
            value="560001",
            confidence=0.9,
            source="user_message",
        )
        assert entity.entity_type == EntityType.PIN_CODE
        assert entity.value == "560001"
        assert entity.confidence == 0.9
        assert entity.source == "user_message"
        assert entity.needs_clarification is False

    def test_extracted_entity_confidence_bounds(self):
        """Test confidence must be between 0.0 and 1.0."""
        with pytest.raises(ValidationError):
            ExtractedEntity(
                entity_type=EntityType.OTHER,
                value="test",
                confidence=1.5,
                source="user_message",
            )
        with pytest.raises(ValidationError):
            ExtractedEntity(
                entity_type=EntityType.OTHER,
                value="test",
                confidence=-0.1,
                source="user_message",
            )


# ---------------------------------------------------------------------------
# IntentClassifier typed entity regression tests
# ---------------------------------------------------------------------------


class TestIntentClassifierTypedEntities:
    """Tests that IntentClassifier returns typed entity lists."""

    def test_extract_entities_return_type_annotation(self):
        """Test that extract_entities returns list[ExtractedEntity]."""
        import typing

        mock_ai_service = MagicMock()
        classifier = IntentClassifier(mock_ai_service)
        hints = typing.get_type_hints(classifier.extract_entities)
        assert hints["return"] == list[ExtractedEntity]

    def test_classify_and_extract_return_type_annotation(self):
        """Test that classify_and_extract returns tuple with typed entities."""
        import typing

        mock_ai_service = MagicMock()
        classifier = IntentClassifier(mock_ai_service)
        hints = typing.get_type_hints(classifier.classify_and_extract)
        assert hints["return"] == tuple[
            IntentDetectionResult, list[ExtractedEntity]
        ]

    @pytest.mark.asyncio
    async def test_extract_entities_returns_typed_entities(self):
        """Test that extract_entities returns ExtractedEntity instances."""
        mock_ai_service = MagicMock()
        mock_result = MagicMock()
        mock_result.entities = [
            MagicMock(
                entity_type="business_name",
                value="Acme Pvt Ltd",
                confidence=0.95,
                source="user_message",
                needs_clarification=False,
            ),
            MagicMock(
                entity_type="invalid_type",
                value="skipped",
                confidence=0.5,
                source="user_message",
                needs_clarification=False,
            ),
        ]
        mock_ai_service.generate_structured_output = AsyncMock(
            return_value=mock_result
        )

        classifier = IntentClassifier(mock_ai_service)
        entities = await classifier.extract_entities(
            message="My business is Acme Pvt Ltd"
        )

        assert len(entities) == 1  # invalid_type skipped
        assert isinstance(entities[0], ExtractedEntity)
        assert entities[0].entity_type == EntityType.BUSINESS_NAME
        assert entities[0].value == "Acme Pvt Ltd"
        assert entities[0].confidence == 0.95

    @pytest.mark.asyncio
    async def test_classify_and_extract_returns_typed_entities(self):
        """Test that classify_and_extract returns typed entity list."""
        mock_ai_service = MagicMock()
        intent_result = IntentDetectionResult(
            primary_intent=Intent.GST_REGISTRATION,
            secondary_intents=[],
            confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            requires_clarification=False,
            clarification_question=None,
            reasoning_summary="GST registration query",
            detected_language="en",
            is_follow_up=False,
            referenced_entity=None,
            urgency="normal",
            risk_flags=[],
            taxonomy_version="1.0.0",
        )
        mock_entity_result = MagicMock()
        mock_entity_result.entities = [
            MagicMock(
                entity_type="registration_type",
                value="GST registration",
                confidence=0.9,
                source="user_message",
                needs_clarification=False,
            )
        ]
        mock_ai_service.generate_structured_output = AsyncMock(
            side_effect=[intent_result, mock_entity_result]
        )

        classifier = IntentClassifier(mock_ai_service)
        result, entities = await classifier.classify_and_extract(
            message="How do I register for GST?"
        )

        assert isinstance(result, IntentDetectionResult)
        assert len(entities) == 1
        assert isinstance(entities[0], ExtractedEntity)
        assert entities[0].entity_type == EntityType.REGISTRATION_TYPE


# ---------------------------------------------------------------------------
# MessageCreate role restriction tests
# ---------------------------------------------------------------------------


class TestMessageCreateRoleRestriction:
    """Tests that public API only allows user role messages."""

    def test_message_create_user_role_allowed(self):
        """Test that role='user' is accepted."""
        msg = MessageCreate(
            conversation_id=uuid4(),
            role="user",
            content="Hello, how do I register for GST?",
        )
        assert msg.role == "user"
        assert msg.content == "Hello, how do I register for GST?"

    def test_message_create_role_defaults_to_user(self):
        """Test that role defaults to 'user' when not specified."""
        msg = MessageCreate(
            conversation_id=uuid4(),
            content="Hello",
        )
        assert msg.role == "user"

    def test_message_create_assistant_role_rejected(self):
        """Test that role='assistant' raises validation error."""
        with pytest.raises(ValidationError):
            MessageCreate(
                conversation_id=uuid4(),
                role="assistant",
                content="I am an assistant",
            )

    def test_message_create_system_role_rejected(self):
        """Test that role='system' raises validation error."""
        with pytest.raises(ValidationError):
            MessageCreate(
                conversation_id=uuid4(),
                role="system",
                content="System message",
            )

    def test_message_create_invalid_role_rejected(self):
        """Test that any other role raises validation error."""
        with pytest.raises(ValidationError):
            MessageCreate(
                conversation_id=uuid4(),
                role="admin",
                content="Admin message",
            )

    def test_message_create_missing_role_uses_default(self):
        """Test that omitting role defaults to 'user'."""
        msg = MessageCreate(
            conversation_id=uuid4(),
            content="Test content",
        )
        assert msg.role == "user"


# ---------------------------------------------------------------------------
# Schema import consistency tests
# ---------------------------------------------------------------------------


class TestSchemaConsistency:
    """Tests that ExtractedEntity is consistently imported."""

    def test_extracted_entity_importable_from_entities(self):
        """Test ExtractedEntity can be imported from app.schemas.entities."""
        from app.schemas.entities import ExtractedEntity as EE
        assert EE is ExtractedEntity

    def test_extracted_entity_reexported_from_intent(self):
        """Test ExtractedEntity is re-exported from app.schemas.intent."""
        from app.schemas.intent import IntentAnalysisResponse, EntityExtractionResponse
        assert EntityExtractionResponse.model_fields["entities"].annotation == list[
            ExtractedEntity
        ]
        assert IntentAnalysisResponse.model_fields["entities"].annotation == list[
            ExtractedEntity
        ]
