"""AI API router.

Provides AI generation endpoints:
- POST /api/v1/ai/generate - Generate text
- POST /api/v1/ai/json - Generate JSON
- POST /api/v1/ai/structured - Generate structured output
- GET  /api/v1/ai/health - Health check
- POST /api/v1/ai/test - Development test endpoint (dev only)
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.schemas.ai import (
    AIHealthResponse,
    AIJSONRequest,
    AIJSONResponse,
    AIRequest,
    AIResponse,
    AIStructuredRequest,
    AIStructuredResponse,
    AITestRequest,
    AITestResponse,
)
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import AIError, AIServiceUnavailableError

router = APIRouter(prefix="/ai", tags=["ai"])


async def get_ai_service(
    ai_service: AIService = Depends(AIService),
) -> AIService:
    """Dependency to get AIService instance."""
    return ai_service


@router.post(
    "/generate",
    response_model=AIResponse,
    summary="Generate text",
    description="Generate text from a prompt using Gemini.",
)
async def generate_text(
    request: AIRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_active_user),
) -> AIResponse:
    """Generate text from a prompt.

    Requires authentication. AI must be enabled via GEMINI_ENABLED=true
    and GEMINI_API_KEY must be configured.
    """
    try:
        text = await ai_service.generate_text(
            prompt=request.prompt,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
            system_instruction=request.system_instruction,
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

    return AIResponse(
        text=text,
        model=settings.gemini_model,
    )


@router.post(
    "/json",
    response_model=AIJSONResponse,
    summary="Generate JSON",
    description="Generate JSON output from a prompt using Gemini.",
)
async def generate_json(
    request: AIJSONRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_active_user),
) -> AIJSONResponse:
    """Generate JSON output from a prompt.

    Requires authentication. AI must be enabled.
    """
    try:
        data = await ai_service.generate_json(
            prompt=request.prompt,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
            system_instruction=request.system_instruction,
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

    return AIJSONResponse(
        data=data,
        model=settings.gemini_model,
    )


@router.post(
    "/structured",
    response_model=AIStructuredResponse,
    summary="Generate structured output",
    description="Generate structured output validated against a JSON schema.",
)
async def generate_structured(
    request: AIStructuredRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_active_user),
) -> AIStructuredResponse:
    """Generate structured output validated against a JSON schema.

    Requires authentication. AI must be enabled.
    """
    try:
        data = await ai_service.generate_json(
            prompt=(
                f"{request.prompt}\n\n"
                f"Respond with a valid JSON object matching this schema:\n"
                f"{request.response_schema}\n"
                f"Return ONLY the JSON object, no markdown fences."
            ),
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
            system_instruction=request.system_instruction,
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

    return AIStructuredResponse(
        data=data,
        model=settings.gemini_model,
    )


@router.get(
    "/health",
    response_model=AIHealthResponse,
    summary="AI health check",
    description="Check AI service availability.",
)
async def ai_health(
    ai_service: AIService = Depends(get_ai_service),
) -> AIHealthResponse:
    """Check AI service availability.

    No authentication required. Reports whether AI is configured and enabled.
    """
    health = await ai_service.health_check()
    return AIHealthResponse(
        enabled=bool(health["enabled"]),
        model=health["model"],  # type: ignore[arg-type]
        available=bool(health["available"]),
    )


@router.post(
    "/test",
    response_model=AITestResponse,
    summary="Test AI generation (development only)",
    description=(
        "Test AI generation with a short prompt. "
        "Only available in development when AI_TEST_ENABLED=true."
    ),
)
async def test_generation(
    request: AITestRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_active_user),
) -> AITestResponse:
    """Test AI generation (development only).

    Requires authentication and GEMINI_ENABLED=true.
    Input is limited to 2000 characters.
    """
    if not settings.is_development:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test endpoint only available in development",
        )

    try:
        text = await ai_service.generate_text(
            prompt=request.prompt,
            temperature=request.temperature,
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

    return AITestResponse(
        text=text,
        model=settings.gemini_model,
    )
