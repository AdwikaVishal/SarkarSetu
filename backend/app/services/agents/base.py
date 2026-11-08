"""Base agent for SarkarSetu AI specialized agents.

Provides a reusable base class with common context validation,
structured response validation, error handling, logging, execution
timing, AI service access, prompt management, and evidence handling.

All agents must reuse the existing AIService and must not
instantiate separate Gemini clients or directly access secrets.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.schemas.agents import (
    AgentContext,
    AgentResult,
    AgentStatus,
    RetrievalSource,
)
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import AIError, AIServiceUnavailableError
from app.services.eligibility import (
    EligibilityAssessmentRequest,
    EligibilityAssessmentResult,
    EligibilityEvaluator,
    EligibilityEvaluatorUnavailable,
)
from app.services.retrieval import (
    GovernmentKnowledgeProvider,
    UnavailableGovernmentKnowledgeProvider,
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all specialized agents.

    Provides common infrastructure:
    - Context validation
    - Structured output validation via AIService
    - Error handling and safe exception responses
    - Execution timing and logging
    - Access to AIService, retrieval provider, and eligibility evaluator
    - Evidence handling
    """

    def __init__(
        self,
        name: str,
        ai_service: AIService,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
        eligibility_evaluator: EligibilityEvaluator | None = None,
    ) -> None:
        self.name = name
        self.ai_service = ai_service
        self.retrieval_provider = retrieval_provider or (
            UnavailableGovernmentKnowledgeProvider()
        )
        self.eligibility_evaluator = eligibility_evaluator or (
            EligibilityEvaluatorUnavailable()
        )

    @abstractmethod
    async def _execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's specific logic.

        Subclasses must implement this method. It receives a
        validated AgentContext and returns a typed AgentResult.

        Args:
            context: Validated agent context.

        Returns:
            Typed agent result.
        """
        ...

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent with full error handling and timing.

        Validates context, runs the agent-specific logic, and wraps
        any exceptions in a safe AgentResult with FAILED status.

        Args:
            context: Agent context to execute against.

        Returns:
            Typed agent result, never raises exceptions.
        """
        start_time = time.perf_counter()

        # Validate context
        validation_errors = context.validate_context()
        if validation_errors:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                response="I'm sorry, I couldn't process your request due to missing information. Please try again.",
                warnings=validation_errors,
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        try:
            result = await self._execute(context)
            result.execution_duration_ms = (
                time.perf_counter() - start_time
            ) * 1000
            return result
        except AIServiceUnavailableError as exc:
            logger.warning(
                "AI service unavailable in agent %s",
                self.name,
                extra={"request_id": context.request_id, "error": str(exc)},
            )
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                response="I'm sorry, the AI service is not available right now. Please try again later.",
                warnings=[str(exc)],
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
            )
        except AIError as exc:
            logger.warning(
                "AI error in agent %s",
                self.name,
                extra={"request_id": context.request_id, "error": exc.message},
            )
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                response="I'm sorry, I encountered an error processing your request. Please try again.",
                warnings=[exc.message],
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
            )
        except Exception as exc:  # noqa: BLE001 - safe error response
            logger.exception(
                "Unexpected error in agent %s",
                self.name,
                extra={"request_id": context.request_id, "error": str(exc)},
            )
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                response="I'm sorry, I encountered an unexpected error. Please try again later.",
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
            )

    async def generate_structured_response(
        self,
        prompt: str,
        response_model: type[Any],
        *,
        temperature: float = 0.3,
        max_output_tokens: int = 1024,
        system_instruction: str | None = None,
    ) -> Any:
        """Generate structured output using the existing AIService.

        Delegates to AIService.generate_structured_output with
        consistent error handling.

        Args:
            prompt: The prompt text.
            response_model: Pydantic model class for validation.
            temperature: Sampling temperature.
            max_output_tokens: Maximum output tokens.
            system_instruction: Optional system instruction.

        Returns:
            Validated model instance.

        Raises:
            AIServiceUnavailableError: If AI service is not configured.
            AIError: For other AI errors.
        """
        return await self.ai_service.generate_structured_output(
            prompt=prompt,
            response_model=response_model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
        )

    async def retrieve_evidence(
        self,
        query: str,
        context: AgentContext,
        *,
        filters: dict[str, object] | None = None,
        limit: int = 5,
    ) -> list[RetrievalSource]:
        """Retrieve government document evidence using the retrieval provider.

        Args:
            query: Search query.
            context: Agent context for user/conversation IDs.
            filters: Optional retrieval filters.
            limit: Maximum number of results.

        Returns:
            List of RetrievalSource objects. Empty list if provider
            is unavailable or no results found.
        """
        return await self.retrieval_provider.retrieve(
            query=query,
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            filters=filters,
            limit=limit,
        )

    async def evaluate_eligibility(
        self,
        scheme_name: str | None,
        registration_type: str | None,
        business_attributes: dict[str, Any],
        missing_information: list[str],
        context: dict[str, Any] | None = None,
        user_id: UUID | None = None,
    ) -> EligibilityAssessmentResult:
        """Evaluate eligibility using the deterministic evaluator.

        Delegates to EligibilityEvaluator.evaluate with consistent
        error handling.

        Args:
            scheme_name: Name of the scheme being assessed.
            registration_type: Type of registration being assessed.
            business_attributes: Known business attributes.
            missing_information: Information still needed from user.
            context: Additional context from conversation.
            user_id: Authenticated user ID (from context if not provided).

        Returns:
            Typed eligibility assessment result.
        """
        ctx = context or {}
        request = EligibilityAssessmentRequest(
            user_id=user_id or UUID(int=0),
            business_profile_id=None,
            scheme_name=scheme_name,
            registration_type=registration_type,
            business_attributes=business_attributes,
            missing_information=missing_information,
            context=ctx,
        )
        return await self.eligibility_evaluator.evaluate(request)

    def build_safe_error_response(
        self,
        message: str,
        status: AgentStatus = AgentStatus.FAILED,
        warnings: list[str] | None = None,
    ) -> AgentResult:
        """Build a safe error AgentResult without leaking internals.

        Args:
            message: User-safe error message.
            status: Agent status (default FAILED).
            warnings: Optional warnings.

        Returns:
            Safe error AgentResult.
        """
        return AgentResult(
            agent_name=self.name,
            status=status,
            response=message,
            warnings=warnings or [],
        )
