"""AI services package."""
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import (
    AIAuthenticationError,
    AIProviderError,
    AIRateLimitError,
    AIResponseValidationError,
    AIServiceUnavailableError,
    AITimeoutError,
)
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.local_knowledge import LocalKnowledgeBase, SchemeEntry, get_knowledge_base
from app.services.ai.provider_router import (
    PROVIDER_GEMINI,
    PROVIDER_LOCAL_FALLBACK,
    ProviderRouter,
)
from app.services.ai.providers import (
    AIProvider,
    ProviderResult,
    ProviderStatus,
)

__all__ = [
    "AIService",
    "GeminiClient",
    "AIServiceUnavailableError",
    "AIAuthenticationError",
    "AIRateLimitError",
    "AITimeoutError",
    "AIProviderError",
    "AIResponseValidationError",
    "AIProvider",
    "ProviderResult",
    "ProviderStatus",
    "ProviderRouter",
    "PROVIDER_GEMINI",
    "PROVIDER_LOCAL_FALLBACK",
    "LocalKnowledgeBase",
    "SchemeEntry",
    "get_knowledge_base",
]
