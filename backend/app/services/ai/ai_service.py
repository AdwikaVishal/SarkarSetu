"""AI service layer.

Provides high-level AI operations:
- generate_text: Generate text from a prompt.
- generate_structured_output: Generate structured output validated against a Pydantic model.
- generate_json: Generate JSON output parsed into a dict.
- generate_response: Generate a response using the multi-provider router (Gemini with local fallback).
- health_check: Check AI service availability.

All methods are async and delegate to the appropriate provider.
"""

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.services.ai.exceptions import (
    AIResponseValidationError,
    AIServiceUnavailableError,
)
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.local_knowledge import get_knowledge_base
from app.services.ai.provider_router import ProviderRouter

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AIService:
    """Service for AI operations."""

    def __init__(self) -> None:
        try:
            self._client: GeminiClient | None = GeminiClient()
        except AIServiceUnavailableError:
            self._client = None
        self._provider_router: ProviderRouter | None = None

    @property
    def provider_router(self) -> ProviderRouter:
        """Return the provider router, initializing it lazily."""
        if self._provider_router is None:
            self._provider_router = ProviderRouter(
                ai_service=self,
                knowledge_base=get_knowledge_base(),
            )
        return self._provider_router

    def _is_available(self) -> bool:
        """Check if AI service is configured and available."""
        return self._client is not None and settings.gemini_enabled

    def _require_available(self) -> None:
        """Raise if AI service is not available."""
        if self._client is None or not settings.gemini_enabled:
            raise AIServiceUnavailableError(
                "AI service is not configured or disabled. "
                "Set GEMINI_API_KEY and GEMINI_ENABLED=true to enable."
            )

    async def generate_text(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        system_instruction: str | None = None,
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The user prompt text.
            temperature: Sampling temperature.
            max_output_tokens: Maximum output tokens.
            system_instruction: System instruction to prepend.

        Returns:
            The generated text.

        Raises:
            AIServiceUnavailableError: If AI is not configured.
            AIError: For other AI errors.
        """
        self._require_available()
        assert self._client is not None

        logger.info(
            "AI text generation requested",
            extra={
                "model": settings.gemini_model,
                "operation": "generate_text",
                "prompt_length": len(prompt),
            },
        )

        result = await self._client.generate_content(
            contents=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            response_mime_type="text/plain",
        )

        text = result.text or ""
        logger.info(
            "AI text generation completed",
            extra={
                "model": settings.gemini_model,
                "operation": "generate_text",
                "response_length": len(text),
            },
        )
        return text

    async def generate_json(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        system_instruction: str | None = None,
    ) -> dict[str, Any]:
        """Generate JSON output and parse it into a dict.

        Args:
            prompt: The user prompt text.
            temperature: Sampling temperature.
            max_output_tokens: Maximum output tokens.
            system_instruction: System instruction to prepend.

        Returns:
            Parsed JSON as a dict.

        Raises:
            AIServiceUnavailableError: If AI is not configured.
            AIResponseValidationError: If response is not valid JSON.
            AIError: For other AI errors.
        """
        self._require_available()
        assert self._client is not None

        logger.info(
            "AI JSON generation requested",
            extra={
                "model": settings.gemini_model,
                "operation": "generate_json",
                "prompt_length": len(prompt),
            },
        )

        result = await self._client.generate_content(
            contents=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            response_mime_type="application/json",
        )

        text = result.text or ""
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "AI JSON generation failed - invalid JSON",
                extra={
                    "model": settings.gemini_model,
                    "operation": "generate_json",
                    "response_preview": text[:200],
                },
            )
            raise AIResponseValidationError(
                f"Model returned invalid JSON: {exc}"
            ) from exc

        if not isinstance(parsed, dict):
            raise AIResponseValidationError(
                "Model returned JSON that is not an object"
            )

        logger.info(
            "AI JSON generation completed",
            extra={
                "model": settings.gemini_model,
                "operation": "generate_json",
                "keys": list(parsed.keys()) if isinstance(parsed, dict) else None,
            },
        )
        return parsed

    async def generate_structured_output(
        self,
        prompt: str,
        response_model: type[T],
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        system_instruction: str | None = None,
    ) -> T:
        """Generate structured output validated against a Pydantic model.

        Args:
            prompt: The user prompt text.
            response_model: Pydantic model class to validate against.
            temperature: Sampling temperature.
            max_output_tokens: Maximum output tokens.
            system_instruction: System instruction to prepend.

        Returns:
            Parsed and validated model instance.

        Raises:
            AIServiceUnavailableError: If AI is not configured.
            AIResponseValidationError: If response fails validation.
            AIError: For other AI errors.
        """
        self._require_available()
        assert self._client is not None

        logger.info(
            "AI structured generation requested",
            extra={
                "model": settings.gemini_model,
                "operation": "generate_structured_output",
                "response_model": response_model.__name__,
                "prompt_length": len(prompt),
            },
        )

        # Build a JSON schema instruction for the model
        schema_json = response_model.model_json_schema()
        schema_instruction = (
            f"\n\nRespond with a valid JSON object matching this schema:\n"
            f"{json.dumps(schema_json, indent=2)}\n"
            f"Return ONLY the JSON object, no markdown fences, no extra text."
        )
        full_prompt = f"{prompt}\n{schema_instruction}"

        result = await self._client.generate_content(
            contents=full_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            response_mime_type="application/json",
        )

        text = result.text or ""
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "AI structured generation failed - invalid JSON",
                extra={
                    "model": settings.gemini_model,
                    "operation": "generate_structured_output",
                    "response_model": response_model.__name__,
                    "response_preview": text[:200],
                },
            )
            raise AIResponseValidationError(
                f"Model returned invalid JSON: {exc}"
            ) from exc

        try:
            validated = response_model.model_validate(parsed)
        except ValidationError as exc:
            logger.warning(
                "AI structured generation failed - validation error",
                extra={
                    "model": settings.gemini_model,
                    "operation": "generate_structured_output",
                    "response_model": response_model.__name__,
                    "errors": exc.errors(),
                },
            )
            raise AIResponseValidationError(
                f"Model response failed validation: {exc}"
            ) from exc

        logger.info(
            "AI structured generation completed",
            extra={
                "model": settings.gemini_model,
                "operation": "generate_structured_output",
                "response_model": response_model.__name__,
            },
        )
        return validated

    async def generate_response(
        self,
        message: str,
        *,
        conversation_history: list[dict[str, str]] | None = None,
        business_context: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ):
        """Generate a response using the multi-provider router.

        Attempts Gemini first with retry logic for transient errors.
        If Gemini fails or is unavailable, falls back to the local
        knowledge-based provider. Never raises exceptions for normal
        unavailability - returns a ProviderResult with error status.

        Args:
            message: The user's message text.
            conversation_history: Optional recent conversation turns.
            business_context: Optional business profile context.
            system_instruction: Optional system-level instruction.
            temperature: Sampling temperature.
            max_output_tokens: Maximum output tokens.

        Returns:
            A ProviderResult with normalized response data including
            provider name, fallback status, and metadata.
        """
        return await self.provider_router.generate_response(
            message=message,
            conversation_history=conversation_history,
            business_context=business_context,
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    def get_provider_status(self) -> dict[str, Any]:
        """Return availability status of all providers."""
        return self.provider_router.get_provider_status()

    async def health_check(self) -> dict[str, object]:
        """Check AI service availability without generating content.

        Returns:
            Dict with service status information including provider
            availability details.
        """
        available = self._is_available()
        provider_status = self.get_provider_status()
        return {
            "enabled": settings.gemini_enabled,
            "model": settings.gemini_model if available else None,
            "available": available,
            "providers": provider_status,
        }
