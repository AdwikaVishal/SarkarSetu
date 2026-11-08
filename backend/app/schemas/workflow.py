"""Workflow schemas for SarkarSetu AI workflow engine.

Defines Pydantic models for workflow execution requests and responses,
workflow service types, and workflow-related data models.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow execution status enum."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    NEEDS_INFORMATION = "needs_information"
    NEEDS_RETRIEVAL = "needs_retrieval"
    NEEDS_VERIFICATION = "needs_verification"
    ELIGIBILITY_PENDING = "eligibility_pending"
    ELIGIBILITY_COMPLETE = "eligibility_complete"
    ACTIONS_AVAILABLE = "actions_available"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Workflow step status enum."""

    PENDING = "pending"
    COMPLETED = "completed"
    NEEDS_INFORMATION = "needs_information"
    NEEDS_RETRIEVAL = "needs_retrieval"
    NEEDS_VERIFICATION = "needs_verification"
    FAILED = "failed"


class WorkflowStepResult(BaseModel):
    """Result of executing a single workflow step."""

    step_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique step result ID.",
    )
    step_name: str = Field(
        ...,
        description="Name/identifier of the step.",
    )
    status: StepStatus = Field(
        ...,
        description="Step execution status.",
    )
    response: str = Field(
        ...,
        description="User-facing response text from this step.",
    )
    structured_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data produced by this step.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of information needed from the user.",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Clarification question to ask the user, if required.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings collected during step processing.",
    )
    evidence_references: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source references for any claims made.",
    )
    next_step_id: str | None = Field(
        default=None,
        description="ID of the next step to execute, if any.",
    )
    is_final: bool = Field(
        default=False,
        description="Whether this is the final step of the workflow.",
    )


class WorkflowResult(BaseModel):
    """Typed result of workflow execution.

    Contains all information needed to build a user-facing response
    without leaking internal implementation details.
    """

    workflow_id: str = Field(
        ...,
        description="Unique workflow execution ID.",
    )
    service_type: str = Field(
        ...,
        description="Service type identifier.",
    )
    status: str = Field(
        ...,
        description="Overall workflow status.",
    )
    response: str = Field(
        ...,
        description="User-facing response text summarizing the "
        "workflow result.",
    )
    step_results: list[WorkflowStepResult] = Field(
        default_factory=list,
        description="Results from each executed workflow step.",
    )
    structured_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data produced by the workflow.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of information needed from the user.",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Clarification question to ask the user, if required.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings collected during processing.",
    )
    evidence_references: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source references for any claims made.",
    )
    next_actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Actionable next steps for the user.",
    )
    eligibility_assessment_id: str | None = Field(
        default=None,
        description="ID of the eligibility assessment, if applicable.",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when the workflow was completed, if applicable.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the result was created.",
    )


class WorkflowExecutionRequest(BaseModel):
    """Request schema for starting a workflow execution."""

    conversation_id: UUID = Field(
        ...,
        description="Conversation ID associated with this workflow.",
    )
    service_type: str = Field(
        ...,
        description="Service type identifier (e.g., 'udyam_registration', "
        "'gst_registration', 'msme_schemes').",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message text describing the request.",
    )
    business_profile_id: UUID | None = Field(
        default=None,
        description="Optional associated business profile ID.",
    )


class WorkflowExecutionResponse(BaseModel):
    """Response schema for workflow execution."""

    workflow_id: str = Field(
        ...,
        description="Unique workflow execution ID.",
    )
    service_type: str = Field(
        ...,
        description="Service type identifier.",
    )
    status: str = Field(
        ...,
        description="Overall workflow status.",
    )
    response: str = Field(
        ...,
        description="User-facing response text.",
    )
    step_results: list[WorkflowStepResult] = Field(
        default_factory=list,
        description="Results from each executed workflow step.",
    )
    structured_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data produced by the workflow.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of information needed from the user.",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Clarification question to ask the user, if required.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings collected during processing.",
    )
    evidence_references: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source references for any claims made.",
    )
    next_actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Actionable next steps for the user.",
    )
    eligibility_assessment_id: str | None = Field(
        default=None,
        description="ID of the eligibility assessment, if applicable.",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when the workflow was completed, if applicable.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the workflow was created.",
    )


class WorkflowServiceTypeInfo(BaseModel):
    """Information about a supported workflow service type."""

    service_type: str = Field(
        ...,
        description="Service type identifier.",
    )
    display_name: str = Field(
        ...,
        description="Human-readable display name.",
    )
    description: str = Field(
        default="",
        description="Description of the workflow service.",
    )


class WorkflowServiceTypeResponse(BaseModel):
    """Response schema for listing supported workflow service types."""

    service_types: list[WorkflowServiceTypeInfo] = Field(
        default_factory=list,
        description="List of supported service types.",
    )


class ClarificationResponse(BaseModel):
    """Request schema for responding to a clarification question."""

    response: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User's response to the clarification question.",
    )


class ResumeWorkflowRequest(BaseModel):
    """Request schema for resuming a paused workflow."""

    message: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional message to include with the resume request.",
    )


class WorkflowHistoryResponse(BaseModel):
    """Response schema for listing workflow executions."""

    workflows: list[WorkflowExecutionResponse] = Field(
        default_factory=list,
        description="List of workflow executions.",
    )
    total_count: int = Field(
        default=0,
        description="Total number of workflow executions.",
    )
