"""Workflow state management for SarkarSetu AI workflow engine.

Persists and loads workflow execution state to the database,
ensuring conversation continuity across multiple user messages.
Workflow state survives application restarts and can be
resumed after clarification responses.

All methods enforce user ownership - a user can only access
their own workflow executions.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_execution import WorkflowExecution, WorkflowStep

logger = logging.getLogger(__name__)


class WorkflowStateManager:
    """Manages persistence and retrieval of workflow state.

    Workflow execution state is persisted to the database so that:
    - Conversation continuity is maintained across multiple messages
    - Workflow state survives application restarts
    - Workflows can be resumed after clarification responses
    - Historical workflow executions are preserved for audit

    All methods enforce user ownership - a user can only access
    their own workflow executions.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_workflow_execution(
        self,
        user_id: UUID,
        conversation_id: UUID,
        service_type: str,
        workflow_id: UUID | None = None,
        business_profile_id: UUID | None = None,
        message: str = "",
        initial_state: str = "not_started",
    ) -> WorkflowExecution:
        """Create a new workflow execution record.

        Args:
            user_id: Authenticated user ID.
            conversation_id: Conversation ID.
            service_type: Service type identifier.
            workflow_id: Optional pre-generated workflow ID.
            business_profile_id: Optional associated business profile ID.
            message: Initial user message text.
            initial_state: Initial workflow state.

        Returns:
            The persisted WorkflowExecution model instance.
        """
        execution = WorkflowExecution(
            workflow_id=str(workflow_id or uuid4()),
            user_id=user_id,
            business_profile_id=business_profile_id,
            conversation_id=conversation_id,
            service_type=service_type,
            workflow_status=initial_state,
            current_step=None,
            input_snapshot={
                "workflow_id": str(workflow_id or uuid4()),
                "service_type": service_type,
                "message": message,
                "step_results": [],
                "current_step": 0,
                "completed_steps": [],
                "pending_steps": [],
                "collected_input": {},
                "evidence_references": [],
                "warnings": [],
            },
            result_data={
                "workflow_id": str(workflow_id or uuid4()),
                "service_type": service_type,
                "message": message,
                "step_results": [],
                "current_step": 0,
                "completed_steps": [],
                "pending_steps": [],
                "collected_input": {},
                "evidence_references": [],
                "warnings": [],
            },
            missing_information={},
            step_results=[],
            evidence_references=[],
            warnings=[],
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        logger.info(
            "Workflow execution created",
            extra={
                "workflow_id": execution.workflow_id,
                "user_id": str(user_id),
                "service_type": service_type,
            },
        )
        return execution

    async def get_workflow_execution(
        self,
        workflow_id: str,
        user_id: UUID,
    ) -> WorkflowExecution | None:
        """Retrieve a workflow execution by ID.

        Only returns executions owned by the requesting user.

        Args:
            workflow_id: Workflow execution ID.
            user_id: Authenticated user ID.

        Returns:
            The workflow execution model, or None if not found or
            not owned by the user.
        """
        result = await self.db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_workflow_executions(
        self,
        user_id: UUID,
        business_profile_id: UUID | None = None,
        service_type: str | None = None,
    ) -> list[WorkflowExecution]:
        """List workflow executions for a user.

        Only returns executions owned by the requesting user.

        Args:
            user_id: Authenticated user ID.
            business_profile_id: Optional business profile filter.
            service_type: Optional service type filter.

        Returns:
            List of workflow execution models.
        """
        query = select(WorkflowExecution).where(
            WorkflowExecution.user_id == user_id,
        )
        if business_profile_id is not None:
            query = query.where(
                WorkflowExecution.business_profile_id == business_profile_id
            )
        if service_type is not None:
            query = query.where(
                WorkflowExecution.service_type == service_type
            )
        result = await self.db.execute(
            query.order_by(WorkflowExecution.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_workflow_state(
        self,
        workflow_id: str,
        user_id: UUID,
        state: str | None = None,
        step_results: list[dict[str, Any]] | None = None,
        current_step: int | None = None,
        completed_steps: list[str] | None = None,
        pending_steps: list[str] | None = None,
        collected_input: dict[str, Any] | None = None,
        evidence_references: list[dict[str, Any]] | None = None,
        warnings: list[str] | None = None,
        result_data_updates: dict[str, Any] | None = None,
    ) -> WorkflowExecution | None:
        """Update workflow execution state.

        Only updates executions owned by the requesting user.

        Args:
            workflow_id: Workflow execution ID.
            user_id: Authenticated user ID.
            state: New workflow status.
            step_results: Updated step results.
            current_step: Current step index.
            completed_steps: List of completed step IDs.
            pending_steps: List of pending step IDs.
            collected_input: Updated collected input data.
            evidence_references: Updated evidence references.
            warnings: Updated warnings list.
            result_data_updates: Additional result data updates.

        Returns:
            The updated workflow execution model, or None if not found
            or not owned by the user.
        """
        execution = await self.get_workflow_execution(workflow_id, user_id)
        if execution is None:
            return None

        # Update workflow status
        if state is not None:
            execution.workflow_status = state

        # Update result_data with workflow-specific fields
        result_data = dict(execution.result_data or {})
        if step_results is not None:
            result_data["step_results"] = step_results
        if current_step is not None:
            result_data["current_step"] = current_step
        if completed_steps is not None:
            result_data["completed_steps"] = completed_steps
        if pending_steps is not None:
            result_data["pending_steps"] = pending_steps
        if collected_input is not None:
            result_data["collected_input"] = collected_input
        if evidence_references is not None:
            result_data["evidence_references"] = evidence_references
        if warnings is not None:
            result_data["warnings"] = warnings
        if result_data_updates is not None:
            result_data.update(result_data_updates)

        execution.result_data = result_data

        # Update missing_information if provided via result_data_updates
        if result_data_updates and "missing_information" in result_data_updates:
            execution.missing_information = result_data_updates[
                "missing_information"
            ]

        await self.db.commit()
        await self.db.refresh(execution)
        logger.info(
            "Workflow execution updated",
            extra={
                "workflow_id": workflow_id,
                "user_id": str(user_id),
                "state": execution.workflow_status,
            },
        )
        return execution

    async def cancel_workflow(
        self,
        workflow_id: str,
        user_id: UUID,
    ) -> WorkflowExecution | None:
        """Cancel a workflow execution.

        Only cancels executions owned by the requesting user.

        Args:
            workflow_id: Workflow execution ID.
            user_id: Authenticated user ID.

        Returns:
            The cancelled workflow execution model, or None if not found
            or not owned by the user.
        """
        execution = await self.get_workflow_execution(workflow_id, user_id)
        if execution is None:
            return None

        execution.workflow_status = "cancelled"
        result_data = dict(execution.result_data or {})
        result_data["cancelled_at"] = datetime.now(UTC).isoformat()
        execution.result_data = result_data

        await self.db.commit()
        await self.db.refresh(execution)
        logger.info(
            "Workflow execution cancelled",
            extra={
                "workflow_id": workflow_id,
                "user_id": str(user_id),
            },
        )
        return execution

    async def persist_step_result(
        self,
        workflow_id: str,
        user_id: UUID,
        step_result: dict[str, Any],
    ) -> WorkflowStep | None:
        """Persist a step result to the workflow execution.

        Args:
            workflow_id: Workflow execution ID.
            user_id: Authenticated user ID.
            step_result: Step result dictionary.

        Returns:
            The persisted WorkflowStep model, or None if not found
            or not owned by the user.
        """
        execution = await self.get_workflow_execution(workflow_id, user_id)
        if execution is None:
            return None

        step = WorkflowStep(
            workflow_execution_id=execution.id,
            step_id=step_result.get("step_id", str(uuid4())),
            step_name=step_result.get("step_name", ""),
            step_type=step_result.get("step_type", ""),
            step_status=step_result.get("status", ""),
            step_response=step_result.get("response"),
            structured_data=step_result.get("structured_data", {}),
            missing_information=step_result.get("missing_information", []),
            clarification_question=step_result.get("clarification_question"),
            evidence_references=step_result.get("evidence_references", []),
            next_step_id=step_result.get("next_step_id"),
            is_final=step_result.get("is_final", False),
        )
        self.db.add(step)
        await self.db.commit()
        await self.db.refresh(step)
        logger.info(
            "Workflow step persisted",
            extra={
                "workflow_id": workflow_id,
                "step_id": step.step_id,
                "step_status": step.step_status,
            },
        )
        return step
