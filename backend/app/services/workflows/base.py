"""Base workflow class for SarkarSetu AI workflow engine.

Provides a reusable base class for all specialized workflows.

Implements common context validation, structured response validation,
error handling, logging, execution timing, and step management.

All workflows must reuse the existing services (AIService,
ConversationService, ClarificationService, EligibilityEngine,
etc.) and must not duplicate existing infrastructure.
"""

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from app.services.ai.ai_service import AIService
from app.services.conversation.clarification_service import (
    ClarificationService,
)
from app.services.conversation.conversation_service import (
    ConversationService,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.retrieval import GovernmentKnowledgeProvider

from .context import WorkflowContext
from .workflow_result import WorkflowResult, WorkflowStepResult

logger = logging.getLogger(__name__)


class BaseWorkflow(ABC):
    """Abstract base class for all specialized workflows.

    Provides common infrastructure:
    - Context validation
    - Structured response validation
    - Error handling and safe exception responses
    - Execution timing and logging
    - Access to AIService, ConversationService, ClarificationService,
      EligibilityEngine, and knowledge provider
    - Step management and result building

    Workflows must implement the abstract `execute_steps` method
    which defines the ordered steps for their specific service type.
    """

    def __init__(
        self,
        name: str,
        service_type: str,
        ai_service: AIService,
        conversation_service: ConversationService,
        clarification_service: ClarificationService,
        eligibility_engine: EligibilityEngine,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
    ) -> None:
        self.name = name
        self.service_type = service_type
        self.ai_service = ai_service
        self.conversation_service = conversation_service
        self.clarification_service = clarification_service
        self.eligibility_engine = eligibility_engine
        self.retrieval_provider = retrieval_provider

    @abstractmethod
    async def _execute_steps(
        self,
        context: WorkflowContext,
    ) -> list[WorkflowStepResult]:
        """Execute the workflow's steps in order.

        Subclasses must implement this method to define the ordered
        sequence of steps for their specific service type.

        Args:
            context: Validated workflow context.

        Returns:
            List of step results in execution order.
        """
        ...

    async def execute(
        self,
        context: WorkflowContext,
    ) -> WorkflowResult:
        """Execute the workflow with full error handling and timing.

        Validates context, runs the workflow-specific steps, and wraps
        any exceptions in a safe WorkflowResult with FAILED status.

        Args:
            context: Validated workflow context.

        Returns:
            Typed workflow result, never raises exceptions.
        """
        # Validate context
        validation_errors = context.validate_context()
        if validation_errors:
            return WorkflowResult(
                workflow_id=str(context.workflow_id),
                service_type=self.service_type,
                status="failed",
                response=(
                    "I'm sorry, I couldn't process your request due to "
                    "missing information. Please try again."
                ),
                warnings=list(validation_errors),
            )

        try:
            step_results = await self._execute_steps(context)

            # Determine overall status from step results
            status = self._determine_status(step_results)
            response = self._build_response(step_results, status)
            structured_data = self._build_structured_data(step_results)
            warnings = self._collect_warnings(step_results)
            next_actions = self._collect_next_actions(step_results)
            evidence_references = self._collect_evidence_references(
                step_results
            )
            missing_information = self._collect_missing_information(
                step_results
            )
            clarification_question = self._collect_clarification_question(
                step_results
            )

            return WorkflowResult(
                workflow_id=str(context.workflow_id),
                service_type=self.service_type,
                status=status,
                response=response,
                step_results=step_results,
                structured_data=structured_data,
                missing_information=missing_information,
                clarification_question=clarification_question,
                warnings=warnings,
                evidence_references=evidence_references,
                next_actions=next_actions,
                completed_at=(
                    datetime.now(UTC)
                    if status
                    in ("completed", "failed", "cancelled")
                    else None
                ),
            )

        except Exception as exc:  # noqa: BLE001 - safe error response
            logger.exception(
                "Unexpected error in workflow %s",
                self.name,
                extra={"request_id": context.request_id, "error": str(exc)},
            )
            return WorkflowResult(
                workflow_id=str(context.workflow_id),
                service_type=self.service_type,
                status="failed",
                response=(
                    "I'm sorry, I encountered an unexpected error. "
                    "Please try again later."
                ),
                warnings=[str(exc)],
            )

    # ------------------------------------------------------------------
    # Helper methods for building results
    # ------------------------------------------------------------------

    def _determine_status(
        self,
        step_results: list[WorkflowStepResult],
    ) -> str:
        """Determine overall workflow status from step results.

        Args:
            step_results: List of step execution results.

        Returns:
            Overall workflow status string.
        """
        if not step_results:
            return "failed"

        # If any step failed, the workflow failed
        if any(s.status == "failed" for s in step_results):
            return "failed"

        # If any step needs information, we need more input
        if any(s.status == "needs_information" for s in step_results):
            return "needs_information"

        # If any step needs retrieval, we need to retrieve evidence
        if any(s.status == "needs_retrieval" for s in step_results):
            return "needs_retrieval"

        # If any step needs verification, we need eligibility assessment
        if any(s.status == "needs_verification" for s in step_results):
            return "needs_verification"

        # If any step is still pending
        if any(s.status == "pending" for s in step_results):
            return "in_progress"

        # If all steps are complete
        if all(s.status == "completed" for s in step_results):
            return "completed"

        return "in_progress"

    def _build_response(
        self,
        step_results: list[WorkflowStepResult],
        status: str,
    ) -> str:
        """Build user-facing response from step results.

        Args:
            step_results: List of step results.
            status: Overall workflow status.

        Returns:
            User-facing response text.
        """
        if not step_results:
            return (
                "I'm sorry, I couldn't process your request. "
                "Please try again."
            )

        # Use the last step's response as the main response
        last_step = step_results[-1]
        return last_step.response

    def _build_structured_data(
        self,
        step_results: list[WorkflowStepResult],
    ) -> dict[str, Any]:
        """Build structured data from step results.

        Args:
            step_results: List of step results.

        Returns:
            Structured data dictionary.
        """
        data: dict[str, Any] = {
            "workflow_id": "",
            "step_count": len(step_results),
            "completed_steps": sum(
                1 for s in step_results if s.status == "completed"
            ),
            "step_results": [
                {
                    "step_id": s.step_id,
                    "step_name": s.step_name,
                    "status": s.status,
                    "structured_data": s.structured_data,
                }
                for s in step_results
            ],
        }
        return data

    def _collect_warnings(
        self,
        step_results: list[WorkflowStepResult],
    ) -> list[str]:
        """Collect all warnings from step results.

        Args:
            step_results: List of step results.

        Returns:
            List of warning strings.
        """
        warnings: list[str] = []
        for result in step_results:
            warnings.extend(result.warnings)
        return warnings

    def _collect_next_actions(
        self,
        step_results: list[WorkflowStepResult],
    ) -> list[dict[str, Any]]:
        """Collect all action items from step results.

        Args:
            step_results: List of step results.

        Returns:
            List of action dictionaries.
        """
        actions: list[dict[str, Any]] = []
        for result in step_results:
            # Extract actions from structured_data if present
            if "actions" in result.structured_data:
                actions.extend(result.structured_data["actions"])
        return actions

    def _collect_evidence_references(
        self,
        step_results: list[WorkflowStepResult],
    ) -> list[dict[str, Any]]:
        """Collect all evidence references from step results.

        Args:
            step_results: List of step results.

        Returns:
            List of evidence reference dictionaries.
        """
        evidence: list[dict[str, Any]] = []
        for result in step_results:
            evidence.extend(result.evidence_references)
        return evidence

    def _collect_missing_information(
        self,
        step_results: list[WorkflowStepResult],
    ) -> list[str]:
        """Collect all missing information from step results.

        Args:
            step_results: List of step results.

        Returns:
            List of missing information strings.
        """
        missing: list[str] = []
        for result in step_results:
            missing.extend(result.missing_information)
        return missing

    def _collect_clarification_question(
        self,
        step_results: list[WorkflowStepResult],
    ) -> str | None:
        """Collect the clarification question from step results.

        Args:
            step_results: List of step results.

        Returns:
            Clarification question string, or None.
        """
        for result in step_results:
            if result.clarification_question:
                return result.clarification_question
        return None
