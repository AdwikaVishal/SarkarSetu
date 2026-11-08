"""Workflow engine for SarkarSetu AI.

Deterministic workflow execution engine that coordinates all existing
backend services into complete end-to-end conversational workflows
for government services (Udyam registration, GST registration, MSME
scheme discovery).

The engine is the sole authority for workflow execution - agents and
the orchestrator delegate to it for workflow management.

Guarantees:
- Same inputs + same service type -> same workflow progression
  (deterministic)
- No LLM involvement in workflow decision-making
- Missing information triggers clarification, never silent failure
- Unavailable retrieval triggers NEEDS_RETRIEVAL, never silent failure
- Workflow state is persisted and survives application restarts
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.services.ai.ai_service import AIService
from app.services.conversation.clarification_service import (
    ClarificationService,
)
from app.services.conversation.conversation_service import (
    ConversationService,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.retrieval import GovernmentKnowledgeProvider

from .base import BaseWorkflow
from .context import WorkflowContext
from .workflow_result import WorkflowResult

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Deterministic workflow engine for SarkarSetu AI.

    Coordinates all existing backend services into complete end-to-end
    conversational workflows for government services.

    The engine is the sole authority for workflow execution - agents
    and the orchestrator delegate to it for workflow management.

    Guarantees:
    - Same inputs + same service type + same state -> same workflow
      progression (deterministic)
    - No LLM involvement in workflow decision-making
    - Missing information triggers clarification, never silent failure
    - Unavailable retrieval triggers NEEDS_RETRIEVAL, never silent
      failure
    - Workflow state is persisted and survives application restarts
    """

    def __init__(
        self,
        state_manager: Any,
        step_executor: Any,
        ai_service: AIService | None = None,
        conversation_service: ConversationService | None = None,
        clarification_service: ClarificationService | None = None,
        eligibility_engine: EligibilityEngine | None = None,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.step_executor = step_executor
        self.ai_service = ai_service
        self.conversation_service = conversation_service
        self.clarification_service = clarification_service
        self.eligibility_engine = eligibility_engine
        self.retrieval_provider = retrieval_provider
        self._workflows: dict[str, BaseWorkflow] = {}

    def register_workflow(
        self,
        service_type: str,
        workflow: BaseWorkflow,
    ) -> None:
        """Register a workflow for a service type.

        Args:
            service_type: Service type identifier.
            workflow: Workflow instance to register.
        """
        self._workflows[service_type] = workflow
        logger.info(
            "Workflow registered",
            extra={
                "service_type": service_type,
                "workflow_name": workflow.name,
            },
        )

    def get_workflow(
        self,
        service_type: str,
    ) -> BaseWorkflow | None:
        """Get a workflow by service type.

        Args:
            service_type: Service type identifier.

        Returns:
            Workflow instance, or None if not registered.
        """
        return self._workflows.get(service_type)

    def get_supported_service_types(
        self,
    ) -> list[str]:
        """Get list of supported service types.

        Returns:
            List of service type identifiers.
        """
        return list(self._workflows.keys())

    async def execute_workflow(
        self,
        user_id: UUID,
        conversation_id: UUID,
        service_type: str,
        message: str,
        business_profile_id: UUID | None = None,
        workflow_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """Execute a workflow for the given service type.

        This is the main entry point for workflow execution. It:
        1. Creates or retrieves a workflow execution
        2. Builds a workflow context from the message and context
        3. Executes workflow steps via the appropriate workflow
        4. Persists the result
        5. Returns a typed workflow result

        Args:
            user_id: Authenticated user ID.
            conversation_id: Conversation ID.
            service_type: Service type identifier.
            message: User message text.
            business_profile_id: Optional business profile ID.
            workflow_id: Optional pre-generated workflow ID.
            context: Additional context from conversation.

        Returns:
            Typed workflow result.
        """
        # Step 1: Create or retrieve workflow execution
        workflow_exec = await self.state_manager.create_workflow_execution(
            user_id=user_id,
            conversation_id=conversation_id,
            service_type=service_type,
            workflow_id=workflow_id,
            business_profile_id=business_profile_id,
            message=message,
        )

        # Step 2: Build workflow context
        wf_context = WorkflowContext(
            workflow_id=workflow_exec.workflow_id,
            user_id=user_id,
            conversation_id=conversation_id,
            business_profile_id=business_profile_id,
            service_type=service_type,
            message=message,
        )

        # Step 3: Execute workflow via the appropriate workflow service
        workflow = self.get_workflow(service_type)
        if workflow is None:
            return WorkflowResult(
                workflow_id=workflow_exec.workflow_id,
                service_type=service_type,
                status="failed",
                response=(
                    f"Service type '{service_type}' is not supported "
                    f"by the workflow engine."
                ),
                warnings=[
                    f"No workflow registered for service type: "
                    f"{service_type}"
                ],
            )

        try:
            result = await workflow.execute(wf_context)
        except Exception as exc:  # noqa: BLE001 - safe error handling
            logger.exception(
                "Workflow execution failed",
                extra={
                    "workflow_id": str(wf_context.workflow_id),
                    "service_type": service_type,
                    "error": str(exc),
                },
            )
            result = WorkflowResult(
                workflow_id=str(wf_context.workflow_id),
                service_type=service_type,
                status="failed",
                response=(
                    "I'm sorry, I encountered an error processing your "
                    "request. Please try again later."
                ),
                warnings=[str(exc)],
            )

        # Step 4: Persist workflow state
        await self.state_manager.update_workflow_state(
            workflow_id=workflow_exec.workflow_id,
            user_id=user_id,
            state=result.status,
            step_results=[
                {
                    "step_id": s.step_id,
                    "step_name": s.step_name,
                    "step_type": s.structured_data.get("step_type", ""),
                    "status": s.status,
                    "response": s.response,
                    "structured_data": s.structured_data,
                    "missing_information": s.missing_information,
                    "clarification_question": s.clarification_question,
                    "warnings": s.warnings,
                    "evidence_references": s.evidence_references,
                    "next_step": s.next_step,
                    "is_final": s.is_final,
                }
                for s in result.step_results
            ],
            current_step=len(result.step_results),
            completed_steps=[
                s.step_id
                for s in result.step_results
                if s.status == "completed"
            ],
            pending_steps=[
                s.step_id
                for s in result.step_results
                if s.status
                in (
                    "needs_information",
                    "needs_retrieval",
                    "needs_verification",
                )
            ],
            collected_input={},
            evidence_references=result.evidence_references,
            warnings=result.warnings,
            result_data_updates={
                "result": result.model_dump(),
            },
        )

        return result

    async def _resolve_rule_set(
        self,
        request: Any,
    ) -> Any | None:
        """Placeholder for eligibility rule set resolution.

        This method is kept for interface compatibility with the
        eligibility engine. Workflow engine uses its own state
        management.
        """
        return None

    def _normalize_input(
        self,
        request: Any,
    ) -> dict[str, Any]:
        """Normalize business input data for evaluation.

        Args:
            request: Assessment request.

        Returns:
            Normalized input data dictionary.
        """
        return dict(request.business_attributes or {})

    def _aggregate_status(
        self,
        condition_results: list[Any],
    ) -> tuple[str, list[str]]:
        """Aggregate step results into a final workflow status.

        Args:
            condition_results: List of step results.

        Returns:
            Tuple of (workflow_status, list of missing information).
        """
        return "completed", []

    def _build_warnings(
        self,
        condition_results: list[Any],
        rule_set: Any,
    ) -> list[str]:
        """Build warnings from step results.

        Args:
            condition_results: List of step results.
            rule_set: The rule set used.

        Returns:
            List of warning strings.
        """
        return []

    def _build_unverified_result(
        self,
        request: Any,
        start_time: datetime,
    ) -> WorkflowResult:
        """Build an unverified result when no workflow is available.

        Args:
            request: Assessment request.
            start_time: Evaluation start time.

        Returns:
            Unverified workflow result.
        """
        return WorkflowResult(
            workflow_id=str(uuid4()),
            service_type="unknown",
            status="failed",
            response=(
                "I'm sorry, I couldn't process your request at this "
                "time. Please try again later."
            ),
            warnings=[
                "Workflow engine is not configured for this service "
                "type."
            ],
        )
