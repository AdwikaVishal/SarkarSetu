"""Tests for the provider router and AI providers."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ai.exceptions import (
    AIAuthenticationError,
    AIServiceUnavailableError,
    AITimeoutError,
)
from app.services.ai.providers import (
    GeminiProvider,
    LocalFallbackProvider,
    ProviderResult,
    ProviderStatus,
)
from app.services.ai.provider_router import ProviderRouter


class TestGeminiProvider:
    """Tests for GeminiProvider."""

    def setup_method(self):
        self.mock_ai_service = MagicMock()
        self.mock_ai_service._is_available.return_value = True
        self.provider = GeminiProvider(self.mock_ai_service)

    def test_is_available_when_configured(self):
        """Test is_available returns True when Gemini is configured."""
        self.mock_ai_service._is_available.return_value = True
        assert self.provider.is_available() is True

    def test_is_available_when_not_configured(self):
        """Test is_available returns False when Gemini is not configured."""
        self.mock_ai_service._is_available.return_value = False
        assert self.provider.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test successful response generation."""
        self.mock_ai_service.generate_text = AsyncMock(return_value="Hello world")
        result = await self.provider.generate_response("Hello")
        assert result.status == ProviderStatus.SUCCESS
        assert result.text == "Hello world"
        assert result.provider == "gemini"
        assert result.fallback_used is False

    @pytest.mark.asyncio
    async def test_generate_response_not_available(self):
        """Test response when Gemini is not available."""
        self.mock_ai_service._is_available.return_value = False
        result = await self.provider.generate_response("Hello")
        assert result.status == ProviderStatus.ERROR
        assert result.text == ""
        assert "not configured" in result.error.lower()

    @pytest.mark.asyncio
    async def test_generate_response_auth_error_no_retry(self):
        """Test that authentication errors are not retried."""
        self.mock_ai_service.generate_text = AsyncMock(
            side_effect=AIAuthenticationError("Invalid API key")
        )
        result = await self.provider.generate_response("Hello")
        assert result.status == ProviderStatus.ERROR
        assert "Invalid API key" in result.error
        # Should only be called once (no retry)
        assert self.mock_ai_service.generate_text.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_retry(self):
        """Test that rate limit errors are retried."""
        call_count = 0

        async def flaky_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise AITimeoutError("Request timed out")
            return "Success after retries"

        self.mock_ai_service.generate_text = flaky_generate
        result = await self.provider.generate_response("Hello")
        assert result.status == ProviderStatus.SUCCESS
        assert result.text == "Success after retries"
        assert call_count == 3


class TestLocalFallbackProvider:
    """Tests for LocalFallbackProvider."""

    def setup_method(self):
        from app.services.ai.local_knowledge import get_knowledge_base
        self.kb = get_knowledge_base()
        self.provider = LocalFallbackProvider(self.kb)

    def test_is_available_always_true(self):
        """Test that local fallback is always available."""
        assert self.provider.is_available() is True

    @pytest.mark.asyncio
    async def test_generate_response_known_scheme(self):
        """Test response for a known scheme."""
        result = await self.provider.generate_response("udyam registration")
        assert result.status == ProviderStatus.SUCCESS
        assert result.fallback_used is True
        assert result.provider == "local_fallback"
        assert "Udyam Registration" in result.text
        assert "udyamregistration.gov.in" in result.text
        assert result.requires_verification is True

    @pytest.mark.asyncio
    async def test_generate_response_unknown_topic(self):
        """Test response for an unknown topic."""
        result = await self.provider.generate_response("xyzzy quantum computing")
        assert result.status == ProviderStatus.SUCCESS
        assert result.fallback_used is True
        assert "couldn't find specific information" in result.text.lower()

    @pytest.mark.asyncio
    async def test_generate_response_gst(self):
        """Test response for GST registration."""
        result = await self.provider.generate_response("gst registration")
        assert result.status == ProviderStatus.SUCCESS
        assert "GST Registration" in result.text
        assert "gst.gov.in" in result.text

    @pytest.mark.asyncio
    async def test_response_has_sources(self):
        """Test that response includes source information."""
        result = await self.provider.generate_response("pmegp")
        assert len(result.sources) > 0
        assert result.sources[0]["source_title"] is not None
        assert result.sources[0]["source_url"] is not None


class TestProviderRouter:
    """Tests for ProviderRouter."""

    def setup_method(self):
        self.mock_ai_service = MagicMock()
        self.mock_ai_service._is_available.return_value = True
        self.router = ProviderRouter(self.mock_ai_service)

    def test_gemini_provider_property(self):
        """Test gemini_provider property."""
        assert isinstance(self.router.gemini_provider, GeminiProvider)

    def test_local_provider_property(self):
        """Test local_provider property."""
        from app.services.ai.providers import LocalFallbackProvider
        assert isinstance(self.router.local_provider, LocalFallbackProvider)

    def test_get_provider_status(self):
        """Test provider status reporting."""
        status = self.router.get_provider_status()
        assert "gemini" in status
        assert "local_fallback" in status
        assert status["local_fallback"]["available"] is True

    @pytest.mark.asyncio
    async def test_generate_response_uses_gemini_when_available(self):
        """Test that Gemini is used when available."""
        self.mock_ai_service.generate_text = AsyncMock(return_value="Gemini response")
        result = await self.router.generate_response("Hello")
        assert result.provider == "gemini"
        assert result.fallback_used is False
        assert result.status == ProviderStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_generate_response_falls_back_when_gemini_unavailable(self):
        """Test fallback to local when Gemini is unavailable."""
        self.mock_ai_service._is_available.return_value = False
        result = await self.router.generate_response("udyam registration")
        assert result.provider == "local_fallback"
        assert result.fallback_used is True
        assert result.status == ProviderStatus.SUCCESS
        assert "Udyam Registration" in result.text

    @pytest.mark.asyncio
    async def test_generate_response_auth_error_falls_back(self):
        """Test fallback when Gemini auth error occurs."""
        self.mock_ai_service.generate_text = AsyncMock(
            side_effect=AIAuthenticationError("Invalid API key")
        )
        result = await self.router.generate_response("udyam registration")
        # Auth error is permanent, so fallback should be used
        assert result.provider == "local_fallback"
        assert result.fallback_used is True
        assert result.status == ProviderStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_generate_response_both_fail(self):
        """Test that local fallback always returns a response even with empty KB."""
        self.mock_ai_service._is_available.return_value = False
        result = await self.router.generate_response("unknown topic xyzzy")
        # Local fallback always returns SUCCESS (even with "no match" message)
        assert result.provider == "local_fallback"
        assert result.fallback_used is True
        assert result.status == ProviderStatus.SUCCESS
        assert "couldn't find specific information" in result.text.lower()
