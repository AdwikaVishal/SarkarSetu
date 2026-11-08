"""Workflow result types for SarkarSetu AI workflow engine.

Typed results returned by workflow execution, containing all
information needed to build user-facing responses without leaking
internal implementation details.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


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
    status: str = Field(
        ...,
        description="Step execution status (e.g., 'completed', 'needs_information', 'needs_retrieval', 'needs_verification', 'failed').",
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
        description="Non-fatal warnings collected during step execution.",
    )
    evidence_references: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source references for any claims made.",
    )
    next_step: str | None = Field(
        default=None,
        description="ID of the next step to execute, if any.",
    )
    is_final: bool = Field(
        default=False,
        description="Whether this is the final step of the workflow.",
    )
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the step was executed.",
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
        description="Service type identifier (e.g., 'udyam_registration', 'gst_registration', 'msme_schemes').",
    )
    status: str = Field(
        ...,
        description="Overall workflow status (e.g., 'completed', 'needs_information', 'needs_retrieval', 'needs_verification', 'eligibility_pending', 'eligibility_complete', 'actions_available', 'failed', 'cancelled').",
    )
    response: str = Field(
        ...,
        description="User-facing response text summarizing the workflow result.",
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
        description="ID of the eligibility assessment, if one was performed.",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when the workflow was completed, if applicable.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the result was created.",
    )
