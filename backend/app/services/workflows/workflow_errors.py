"""Workflow error types for SarkarSetu AI workflow engine.

Defines error categories and error types used throughout the workflow
engine to provide structured, actionable error information without
leaking internal implementation details.
"""

from enum import Enum
from typing import Any


class WorkflowErrorCategory(str, Enum):
    """Categories of workflow errors.

    Categorizes errors to enable appropriate handling and user messaging.
    """

    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    INVALID_TRANSITION = "invalid_transition"
    MISSING_INFORMATION = "missing_information"
    RETRIEVAL_FAILED = "retrieval_failed"
    ELIGIBILITY_FAILED = "eligibility_failed"
    INTERNAL_ERROR = "internal_error"
    WORKFLOW_NOT_FOUND = "workflow_not_found"
    WORKFLOW_ARCHIVED = "workflow_archived"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_CANCELLED = "workflow_cancelled"


class WorkflowError(Exception):
    """Structured workflow error.

    Carries a structured error code, human-readable message, and optional
    context for recovery suggestions. Never leaks internal implementation
    details.
    """

    def __init__(
        self,
        code: str,
        message: str,
        category: WorkflowErrorCategory = WorkflowErrorCategory.INTERNAL_ERROR,
        context: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.category = category
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "context": self.context,
        }


class WorkflowValidationError(WorkflowError):
    """Raised when workflow input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        context: dict[str, object] | None = None,
    ) -> None:
        merged_context: dict[str, object] = dict(context) if context else {}
        if field:
            merged_context["field"] = field
        super().__init__(
            code="validation_error",
            message=message,
            category=WorkflowErrorCategory.VALIDATION_ERROR,
            context=merged_context,
        )


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow execution is not found."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            code="workflow_not_found",
            message=f"Workflow {workflow_id} not found.",
            category=WorkflowErrorCategory.WORKFLOW_NOT_FOUND,
            context={"workflow_id": workflow_id},
        )


class WorkflowUnauthorizedError(WorkflowError):
    """Raised when a user tries to access a workflow they don't own."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            code="workflow_forbidden",
            message=f"Workflow {workflow_id} is not owned by the current user.",
            category=WorkflowErrorCategory.FORBIDDEN,
            context={"workflow_id": workflow_id},
        )


class WorkflowArchivedError(WorkflowError):
    """Raised when trying to operate on an archived workflow."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            code="workflow_archived",
            message=f"Workflow {workflow_id} is archived and cannot be modified.",
            category=WorkflowErrorCategory.WORKFLOW_ARCHIVED,
            context={"workflow_id": workflow_id},
        )


class WorkflowCompletedError(WorkflowError):
    """Raised when trying to modify a completed workflow."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            code="workflow_completed",
            message=f"Workflow {workflow_id} is already completed.",
            category=WorkflowErrorCategory.WORKFLOW_COMPLETED,
            context={"workflow_id": workflow_id},
        )


class InvalidTransitionError(WorkflowError):
    """Raised when attempting an invalid workflow state transition."""

    def __init__(
        self,
        from_state: str,
        to_state: str,
        workflow_id: str | None = None,
    ) -> None:
        super().__init__(
            code="invalid_transition",
            message=(
                f"Invalid transition from {from_state} to {to_state}"
                f"{f' for workflow {workflow_id}' if workflow_id else ''}."
            ),
            category=WorkflowErrorCategory.INVALID_TRANSITION,
            context={
                "from_state": from_state,
                "to_state": to_state,
                "workflow_id": workflow_id,
            },
        )


class MissingInformationError(WorkflowError):
    """Raised when required information is missing to proceed."""

    def __init__(
        self,
        missing_fields: list[str],
        message: str | None = None,
    ) -> None:
        message = (
            message
            or f"Missing required information: {', '.join(missing_fields)}"
        )
        super().__init__(
            code="missing_information",
            message=message,
            category=WorkflowErrorCategory.MISSING_INFORMATION,
            context={"missing_fields": missing_fields},
        )


class RetrievalError(WorkflowError):
    """Raised when knowledge retrieval fails."""

    def __init__(
        self,
        message: str,
        context: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            code="retrieval_failed",
            message=message,
            category=WorkflowErrorCategory.RETRIEVAL_FAILED,
            context=context,
        )


class EligibilityError(WorkflowError):
    """Raised when eligibility evaluation fails."""

    def __init__(
        self,
        message: str,
        context: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            code="eligibility_failed",
            message=message,
            category=WorkflowErrorCategory.ELIGIBILITY_FAILED,
            context=context,
        )
