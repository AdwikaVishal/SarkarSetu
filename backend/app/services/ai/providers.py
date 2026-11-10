"""AI provider abstraction for multi-provider architecture.

Defines a common protocol that all AI providers implement, enabling
the system to route requests through Gemini (primary) with a local
knowledge-based fallback provider.

Providers never leak API keys, credentials, or stack traces to
frontend responses.
"""

import asyncio
import logging
import random
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from app.services.ai.exceptions import (
    AIAuthenticationError,
    AIError,
    AIProviderError,
    AIServiceUnavailableError,
    AITimeoutError,
    AIRateLimitError,
)

logger = logging.getLogger(__name__)

# --- Provider identifiers ---

PROVIDER_GEMINI = "gemini"
PROVIDER_LOCAL_FALLBACK = "local_fallback"

# --- Retry configuration ---

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_MAX_DELAY = 30.0  # seconds

# --- Error classification ---

PERMANENT_ERROR_TERMS = [
    "api key",
    "authentication",
    "unauthorized",
    "invalid argument",
    "bad request",
    "model not found",
    "forbidden",
]

RETRYABLE_ERROR_TERMS = [
    "rate limit",
    "quota",
    "unavailable",
    "timeout",
    "internal error",
    "503",
    "504",
    "429",
    "deadline",
]


class ProviderStatus(str, Enum):
    """Status of a provider response."""

    SUCCESS = "success"
    FALLBACK = "fallback"
    ERROR = "error"


@dataclass
class ProviderResult:
    """Normalized result from any AI provider.

    All providers return this shape so the orchestrator can handle
    responses uniformly regardless of which provider generated them.
    """

    text: str
    provider: str
    status: ProviderStatus = ProviderStatus.SUCCESS
    confidence: float | None = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    fallback_used: bool = False
    requires_verification: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI response providers.

    Any provider that implements `generate_response` can be plugged
    into the provider router. Providers must not raise exceptions for
    normal unavailability - they should return a ProviderResult with
    an error status instead.
    """

    async def generate_response(
        self,
        message: str,
        *,
        conversation_history: list[dict[str, str]] | None = None,
        business_context: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> ProviderResult:
        """Generate a response for the given message.

        Args:
            message: The user's message text.
            conversation_history: Optional recent conversation turns.
            business_context: Optional business profile context.
            system_instruction: Optional system-level instruction.
            temperature: Sampling temperature.
            max_output_tokens: Maximum output tokens.

        Returns:
            A normalized ProviderResult.
        """
        ...

    def is_available(self) -> bool:
        """Return True if this provider can currently serve requests."""
        ...

    @property
    def name(self) -> str:
        """Return the provider identifier string."""
        ...


def _is_retryable(error: Exception) -> bool:
    """Determine if an error is safe to retry.

    Retryable: rate limits, service unavailable, timeouts, transient
    network errors.
    Non-retryable: invalid API key, authentication errors, bad requests,
    forbidden, model not found.
    """
    error_type = type(error).__name__
    error_message = str(error).lower()

    # Non-retryable: authentication/config errors
    if any(term in error_message for term in PERMANENT_ERROR_TERMS):
        return False

    # Retryable: rate limits, service unavailable, timeouts
    if any(term in error_type.lower() or term in error_message for term in RETRYABLE_ERROR_TERMS):
        return True

    return False


def _backoff_delay(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = float(min(2 ** attempt, RETRY_MAX_DELAY))
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


class GeminiProvider:
    """Gemini AI provider - the primary response generator.

    Wraps the existing GeminiClient/AIService and translates its
    output into the normalized ProviderResult format. Implements
    bounded exponential backoff with jitter for transient errors
    and does not retry permanent errors (invalid key, auth failure).
    """

    def __init__(self, ai_service: Any) -> None:
        self._ai_service = ai_service
        self._name = PROVIDER_GEMINI

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        """Return True if Gemini is configured and enabled."""
        try:
            return self._ai_service._is_available()  # noqa: SLF001 - intentional
        except Exception:
            return False

    async def generate_response(
        self,
        message: str,
        *,
        conversation_history: list[dict[str, str]] | None = None,
        business_context: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> ProviderResult:
        """Generate a response using Gemini.

        Retries transient errors with bounded exponential backoff.
        Does not retry permanent errors (invalid key, auth failure).
        """
        if not self.is_available():
            return ProviderResult(
                text="",
                provider=self._name,
                status=ProviderStatus.ERROR,
                error="Gemini service is not configured or disabled.",
                fallback_used=False,
            )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Build the full prompt with context
                full_prompt = self._build_prompt(
                    message=message,
                    conversation_history=conversation_history,
                    business_context=business_context,
                )

                text = await self._ai_service.generate_text(
                    prompt=full_prompt,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    system_instruction=system_instruction,
                )

                return ProviderResult(
                    text=text or "",
                    provider=self._name,
                    status=ProviderStatus.SUCCESS,
                    confidence=None,
                    fallback_used=False,
                    requires_verification=True,
                    metadata={"model": getattr(self._ai_service, "_model", "gemini")},
                )

            except AIServiceUnavailableError as exc:
                # Permanent: not configured or disabled - don't retry
                return ProviderResult(
                    text="",
                    provider=self._name,
                    status=ProviderStatus.ERROR,
                    error=str(exc),
                    fallback_used=False,
                )
            except AIAuthenticationError as exc:
                # Permanent: invalid key - don't retry
                return ProviderResult(
                    text="",
                    provider=self._name,
                    status=ProviderStatus.ERROR,
                    error=str(exc),
                    fallback_used=False,
                )
            except (AITimeoutError, AIRateLimitError, AIProviderError) as exc:
                last_error = exc
                if not _is_retryable(exc) or attempt == MAX_RETRIES:
                    return ProviderResult(
                        text="",
                        provider=self._name,
                        status=ProviderStatus.ERROR,
                        error=str(exc),
                        fallback_used=False,
                    )
                await asyncio.sleep(_backoff_delay(attempt))
            except Exception as exc:  # noqa: BLE001 - safe error handling
                last_error = exc
                if attempt == MAX_RETRIES:
                    return ProviderResult(
                        text="",
                        provider=self._name,
                        status=ProviderStatus.ERROR,
                        error=str(exc),
                        fallback_used=False,
                    )
                await asyncio.sleep(_backoff_delay(attempt))

        # Should never reach here, but satisfy type checker
        return ProviderResult(
            text="",
            provider=self._name,
            status=ProviderStatus.ERROR,
            error=str(last_error or AIProviderError("Unknown Gemini error")),
            fallback_used=False,
        )

    def _build_prompt(
        self,
        message: str,
        conversation_history: list[dict[str, str]] | None = None,
        business_context: str | None = None,
    ) -> str:
        """Build the full prompt for Gemini with context."""
        parts: list[str] = [f"User message: {message}"]

        if conversation_history:
            parts.append("\nConversation history:")
            for turn in conversation_history[-10:]:
                role = str(turn.get("role", "user"))
                content = str(turn.get("content", ""))
                parts.append(f"  {role}: {content}")

        if business_context:
            parts.append(f"\nBusiness context: {business_context}")

        parts.append(
            "\n\nGenerate a helpful, accurate response for an Indian entrepreneur "
            "navigating government services. Do not invent government rules, "
            "schemes, deadlines, fees, or official approvals. Clearly distinguish "
            "verified information from general guidance. Do not claim registration "
            "is complete or that the user is approved for any scheme."
        )

        return "\n".join(parts)


class LocalFallbackProvider:
    """Local knowledge-based fallback provider.

    Uses a deterministic, keyword-based knowledge base of Indian MSME
    and business-related government schemes to generate responses when
    Gemini is unavailable. Does not require any external API or paid
    service.

    Never invents scheme information - returns an honest "no match"
    response when no relevant knowledge entry is found.
    """

    def __init__(self, knowledge_base: Any) -> None:
        self._knowledge_base = knowledge_base
        self._name = PROVIDER_LOCAL_FALLBACK

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        """The local fallback is always available."""
        return True

    async def generate_response(
        self,
        message: str,
        *,
        conversation_history: list[dict[str, str]] | None = None,
        business_context: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> ProviderResult:
        """Generate a response using the local knowledge base.

        Matches the user's message against known schemes using keyword
        and phrase matching. Returns structured, readable answers with
        official source links and a clear fallback indicator.
        """
        try:
            result = await self._knowledge_base.retrieve(message)

            if not result or not result.get("matched_schemes"):
                # No relevant knowledge entry found
                return ProviderResult(
                    text=self._build_no_match_response(message),
                    provider=self._name,
                    status=ProviderStatus.SUCCESS,
                    confidence=0.0,
                    fallback_used=True,
                    requires_verification=True,
                    warnings=[
                        "No matching scheme information found in the local knowledge base."
                    ],
                    metadata={"match_type": "none"},
                )

            text = self._build_knowledge_response(result)
            sources = [
                {
                    "source_title": s.get("name"),
                    "issuing_authority": s.get("issuing_authority"),
                    "source_url": s.get("official_url"),
                    "relevant_excerpt": s.get("description"),
                    "retrieval_score": s.get("confidence"),
                }
                for s in result.get("matched_schemes", [])
            ]

            return ProviderResult(
                text=text,
                provider=self._name,
                status=ProviderStatus.SUCCESS,
                confidence=result.get("confidence", 0.0),
                sources=sources,
                fallback_used=True,
                requires_verification=True,
                warnings=[
                    "Using SarkarSetu's offline knowledge base. "
                    "Some information may not reflect the latest government updates."
                ],
                metadata={"match_type": result.get("match_type", "keyword")},
            )

        except Exception as exc:  # noqa: BLE001 - safe error handling
            logger.exception("Local fallback provider failed")
            return ProviderResult(
                text=self._build_error_response(),
                provider=self._name,
                status=ProviderStatus.ERROR,
                error=str(exc),
                fallback_used=True,
                requires_verification=True,
            )

    def _build_knowledge_response(self, result: dict[str, Any]) -> str:
        """Build a structured, readable response from knowledge base results."""
        lines: list[str] = []

        matched = result.get("matched_schemes", [])
        match_type = result.get("match_type", "keyword")

        if match_type == "exact":
            lines.append(f"## {matched[0].get('name', 'Scheme Information')}")
        else:
            lines.append("## Relevant Government Schemes")

        lines.append("")
        lines.append(
            "*Using SarkarSetu's offline knowledge base. "
            "Some information may not reflect the latest government updates.*"
        )
        lines.append("")

        for scheme in matched[:3]:
            lines.append(f"### {scheme.get('name', 'Unknown Scheme')}")
            lines.append("")

            if scheme.get("description"):
                lines.append(f"**Description:** {scheme['description']}")
                lines.append("")

            if scheme.get("eligibility"):
                lines.append(f"**Eligibility:** {scheme['eligibility']}")
                lines.append("")

            if scheme.get("benefits"):
                lines.append(f"**Benefits:** {scheme['benefits']}")
                lines.append("")

            if scheme.get("required_documents"):
                docs = scheme["required_documents"]
                if isinstance(docs, list):
                    lines.append("**Required Documents:**")
                    for doc in docs:
                        lines.append(f"  - {doc}")
                else:
                    lines.append(f"**Required Documents:** {docs}")
                lines.append("")

            if scheme.get("application_procedure"):
                lines.append(f"**Application Procedure:** {scheme['application_procedure']}")
                lines.append("")

            if scheme.get("official_url"):
                lines.append(f"**Official URL:** {scheme['official_url']}")
                lines.append("")

            if scheme.get("official_source"):
                lines.append(f"**Source:** {scheme['official_source']}")
                lines.append("")

            lines.append("---")
            lines.append("")

        lines.append(
            "This information is for general guidance only and does not "
            "constitute official eligibility confirmation or government "
            "approval. Please verify details on the official government "
            "website before applying."
        )

        return "\n".join(lines)

    def _build_no_match_response(self, message: str) -> str:
        """Build an honest response when no knowledge entry matches."""
        return (
            "I couldn't find specific information about that topic in my "
            "local knowledge base. I can help you with:\n\n"
            "• Udyam Registration\n"
            "• PMEGP (Prime Minister's Employment Generation Programme)\n"
            "• MUDRA loans\n"
            "• Stand-Up India\n"
            "• Startup India\n"
            "• CGTMSE\n"
            "• GST registration\n"
            "• MSME classification\n"
            "• Government subsidies for small businesses\n"
            "• Basic business compliance and documentation\n\n"
            "Could you rephrase your question or ask about one of these topics?"
        )

    def _build_error_response(self) -> str:
        """Build a safe error response without leaking internals."""
        return (
            "I'm sorry, I couldn't generate a response at this time. "
            "Please try again later or consult official government websites "
            "directly for scheme information."
        )


__all__ = [
    "AIProvider",
    "ProviderResult",
    "ProviderStatus",
    "GeminiProvider",
    "LocalFallbackProvider",
    "PROVIDER_GEMINI",
    "PROVIDER_LOCAL_FALLBACK",
    "_is_retryable",
    "_backoff_delay",
]
