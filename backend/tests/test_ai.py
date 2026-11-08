"""AI service and API tests."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import (
    AIResponseValidationError,
    AIServiceUnavailableError,
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
# AI Service tests (mocked)
# ---------------------------------------------------------------------------


class TestAIService:
    """Tests for AIService with mocked client."""

    def test_service_creates_client_when_enabled(self):
        """Test that AIService creates a GeminiClient when configured."""
        with patch(
            "app.services.ai.ai_service.GeminiClient"
        ) as mock_client:
            mock_client.return_value = MagicMock()
            with patch(
                "app.services.ai.ai_service.settings"
            ) as mock_settings:
                mock_settings.gemini_enabled = True
                service = AIService()
                assert service._client is not None
                mock_client.assert_called_once()

    def test_service_no_client_when_disabled(self):
        """Test that AIService sets _client to None when disabled."""
        with patch(
            "app.services.ai.ai_service.GeminiClient",
            side_effect=AIServiceUnavailableError("No API key"),
        ):
            with patch(
                "app.services.ai.ai_service.settings"
            ) as mock_settings:
                mock_settings.gemini_enabled = True
                service = AIService()
                assert service._client is None

    @pytest.mark.asyncio
    async def test_generate_text_success(self):
        """Test successful text generation."""
        with patch(
            "app.services.ai.ai_service.GeminiClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.generate_content = AsyncMock(
                return_value=MagicMock(text="Generated response text")
            )
            mock_client_class.return_value = mock_client

            with patch(
                "app.services.ai.ai_service.settings"
            ) as mock_settings:
                mock_settings.gemini_enabled = True
                service = AIService()
                service._client = mock_client
                result = await service.generate_text(prompt="Hello, world!")
                assert result == "Generated response text"
                mock_client.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_text_service_unavailable(self):
        """Test generate_text when AI is disabled."""
        service = AIService()
        service._client = None

        with pytest.raises(AIServiceUnavailableError):
            await service.generate_text(prompt="Hello")

    @pytest.mark.asyncio
    async def test_generate_structured_output_success(self):
        """Test successful structured output generation."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            score: float

        with patch(
            "app.services.ai.ai_service.GeminiClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.generate_content = AsyncMock(
                return_value=MagicMock(text='{"name": "test", "score": 0.95}')
            )
            mock_client_class.return_value = mock_client

            with patch(
                "app.services.ai.ai_service.settings"
            ) as mock_settings:
                mock_settings.gemini_enabled = True
                service = AIService()
                service._client = mock_client
                result = await service.generate_structured_output(
                    prompt="Generate a test object",
                    response_model=TestModel,
                )
                assert result.name == "test"
                assert result.score == 0.95

    @pytest.mark.asyncio
    async def test_generate_structured_output_invalid_json(self):
        """Test structured output with invalid JSON."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str

        with patch(
            "app.services.ai.ai_service.GeminiClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.generate_content = AsyncMock(
                return_value=MagicMock(text="not valid json")
            )
            mock_client_class.return_value = mock_client

            with patch(
                "app.services.ai.ai_service.settings"
            ) as mock_settings:
                mock_settings.gemini_enabled = True
                service = AIService()
                service._client = mock_client
                with pytest.raises(AIResponseValidationError):
                    await service.generate_structured_output(
                        prompt="Generate JSON",
                        response_model=TestModel,
                    )

    @pytest.mark.asyncio
    async def test_health_check_disabled(self):
        """Test health check when AI is disabled."""
        service = AIService()
        service._client = None

        health = await service.health_check()
        assert health["enabled"] is False
        assert health["available"] is False


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestAIAPIEndpoints:
    """Tests for AI API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_text_endpoint(self, client, db_session):
        """Test POST /api/v1/ai/generate endpoint."""
        # Register user first
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "aiuser@example.com",
                "full_name": "AI User",
                "password": "StrongPassword123!",
            },
        )
        assert reg_response.status_code == 201
        token = reg_response.json()["access_token"]

        # Mock the AI service
        from app.api.ai import get_ai_service
        from app.main import app as main_app

        mock_service = MagicMock()
        mock_service.generate_text = AsyncMock(
            return_value="Generated text response"
        )
        main_app.dependency_overrides[get_ai_service] = lambda: mock_service

        try:
            response = await client.post(
                "/api/v1/ai/generate",
                json={
                    "prompt": "Tell me about Udyam registration",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["text"] == "Generated text response"
            assert data["model"] == "gemini-2.5-flash"
        finally:
            main_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_generate_text_unauthenticated(self, client):
        """Test generate endpoint without authentication."""
        response = await client.post(
            "/api/v1/ai/generate",
            json={"prompt": "Hello"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_ai_health_endpoint(self, client):
        """Test GET /api/v1/ai/health endpoint."""
        response = await client.get("/api/v1/ai/health")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "model" in data
        assert "available" in data

    @pytest.mark.asyncio
    async def test_generate_text_disabled_ai(self, client, db_session):
        """Test generate endpoint when AI is disabled."""
        # Register user
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "aiuser2@example.com",
                "full_name": "AI User 2",
                "password": "StrongPassword123!",
            },
        )
        token = reg_response.json()["access_token"]

        # Mock the AI service with disabled state
        from app.main import app as main_app
        from app.services.ai.ai_service import AIService

        mock_service = MagicMock()
        mock_service.generate_text = AsyncMock(
            side_effect=AIServiceUnavailableError(
                "AI service is not configured"
            )
        )
        main_app.dependency_overrides[AIService] = lambda: mock_service

        try:
            response = await client.post(
                "/api/v1/ai/generate",
                json={"prompt": "Hello"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 503
        finally:
            main_app.dependency_overrides.clear()
