"""Gemini async client wrapper.

Wraps the Google Gen AI SDK with retry logic, timeout handling,
and exception translation into application-level exceptions.
"""
import asyncio
import logging
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings
from app.services.ai.exceptions import (
    AIAuthenticationError,
    AIError,
    AIProviderError,
    AIRateLimitError,
    AIServiceUnavailableError,
    AITimeoutError,
)

logger = logging.getLogger(__name__)


class GeminiClient:
    """Async wrapper around the Google Gen AI SDK.

    Provides a single shared client instance with retry logic,
    timeout handling, and consistent exception translation.
    """

    def __init__(self) -> None:
        api_key = settings.gemini_api_key
        if not api_key:
            raise AIServiceUnavailableError(
                "GEMINI_API_KEY is not configured"
            )

        self._client = genai.Client(api_key=api_key)
        self._model = settings.gemini_model
        self._max_retries = settings.gemini_max_retries
        self._timeout = settings.gemini_timeout_seconds

    async def generate_content(
        self,
        contents: str | list[Any],
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        system_instruction: str | None = None,
        response_mime_type: str = "text/plain",
    ) -> Any:
        """Generate content using the Gemini model.

        Args:
            contents: Text content or list of content parts.
            temperature: Sampling temperature (0.0 to 2.0).
            max_output_tokens: Maximum output tokens.
            system_instruction: System instruction to prepend.
            response_mime_type: MIME type of expected response
                ("text/plain" or "application/json").

        Returns:
            The raw generation result from the SDK.

        Raises:
            AIAuthenticationError: Invalid API key.
            AIRateLimitError: Rate limit exceeded.
            AITimeoutError: Request timed out.
            AIProviderError: Other provider errors.
        """
        config = self._build_generate_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            response_mime_type=response_mime_type,
        )

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self._client.aio.models.generate_content(
                        model=self._model,
                        contents=contents,
                        config=config,
                    ),
                    timeout=self._timeout,
                )
            except TimeoutError as exc:
                last_error = AITimeoutError(
                    f"Gemini request timed out after {self._timeout}s"
                )
                if attempt == self._max_retries:
                    raise last_error from exc
                await asyncio.sleep(self._backoff_delay(attempt))
            except Exception as exc:
                last_error = self._translate_error(exc)
                if not self._is_retryable(exc) or attempt == self._max_retries:
                    raise last_error from exc
                await asyncio.sleep(self._backoff_delay(attempt))

        # Should never reach here, but satisfy type checker
        raise last_error or AIProviderError("Unknown Gemini error")

    def _build_generate_config(
        self,
        temperature: float | None,
        max_output_tokens: int | None,
        system_instruction: str | None,
        response_mime_type: str,
    ) -> types.GenerateContentConfig:
        """Build the GenerateContentConfig for the SDK."""
        config_kwargs: dict[str, Any] = {
            "response_mime_type": response_mime_type,
        }

        if temperature is not None:
            config_kwargs["temperature"] = temperature
        if max_output_tokens is not None:
            config_kwargs["max_output_tokens"] = max_output_tokens
        if system_instruction is not None:
            config_kwargs["system_instruction"] = system_instruction

        return types.GenerateContentConfig(**config_kwargs)

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        import random

        delay: float = float(min(2 ** attempt, 30))
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        """Determine if an error is retryable.

        Retryable: rate limits, timeouts, temporary provider errors.
        Non-retryable: invalid API key, invalid requests, bad config.
        """
        error_type = type(error).__name__
        error_message = str(error).lower()

        # Non-retryable: authentication/config errors
        if any(
            term in error_message
            for term in [
                "api key",
                "authentication",
                "unauthorized",
                "invalid argument",
                "bad request",
                "model not found",
            ]
        ):
            return False

        # Retryable: rate limits, service unavailable, timeouts
        if any(
            term in error_type or term in error_message
            for term in [
                "rate limit",
                "quota",
                "unavailable",
                "timeout",
                "internal error",
                "503",
                "504",
                "429",
            ]
        ):
            return True

        return False

    @staticmethod
    def _translate_error(error: Exception) -> AIError:
        """Translate SDK exceptions into application-level exceptions."""
        error_type = type(error).__name__
        error_message = str(error)

        # Authentication errors
        if any(
            term in error_message.lower()
            for term in ["api key", "authentication", "unauthorized"]
        ):
            return AIAuthenticationError(
                f"Gemini authentication failed: {error_message}"
            )

        # Rate limit errors
        if "rate limit" in error_type.lower() or "429" in error_message:
            return AIRateLimitError(
                f"Gemini rate limit exceeded: {error_message}"
            )

        # Timeout errors
        if "timeout" in error_type.lower() or "deadline" in error_message.lower():
            return AITimeoutError(
                f"Gemini request timed out: {error_message}"
            )

        # Generic provider errors
        return AIProviderError(
            f"Gemini provider error: {error_message}"
        )
