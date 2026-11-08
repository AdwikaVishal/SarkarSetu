"""Roadmap engine error types.

Structured error categories and error types for the roadmap engine.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID


class RoadmapErrorCategory(StrEnum):
    """Categories of roadmap errors."""

    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    INVALID_TRANSITION = "invalid_transition"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MISSING_PREREQUISITE = "missing_prerequisite"
    INELIGIBLE_ACTION = "ineligible_action"
    MISSING_EVIDENCE = "missing_evidence"
    INTERNAL_ERROR = "internal_error"


class RoadmapError(Exception):
    """Structured roadmap error."""

    def __init__(
        self,
        code: str,
        message: str,
        category: RoadmapErrorCategory = RoadmapErrorCategory.INTERNAL_ERROR,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.category = category
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "context": self.context,
        }


class RoadmapValidationError(RoadmapError):
    """Raised when roadmap input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged_context: dict[str, Any] = dict(context) if context else {}
        if field:
            merged_context["field"] = field
        super().__init__(
            code="validation_error",
            message=message,
            category=RoadmapErrorCategory.VALIDATION_ERROR,
            context=merged_context,
        )


class RoadmapNotFoundError(RoadmapError):
    """Raised when a roadmap is not found."""

    def __init__(self, roadmap_id: UUID) -> None:
        super().__init__(
            code="roadmap_not_found",
            message=f"Roadmap {roadmap_id} not found.",
            category=RoadmapErrorCategory.NOT_FOUND,
            context={"roadmap_id": str(roadmap_id)},
        )


class RoadmapForbiddenError(RoadmapError):
    """Raised when user tries to access a roadmap they don't own."""

    def __init__(self, roadmap_id: UUID, user_id: UUID) -> None:
        super().__init__(
            code="roadmap_forbidden",
            message=f"Roadmap {roadmap_id} is not owned by user {user_id}.",
            category=RoadmapErrorCategory.FORBIDDEN,
            context={"roadmap_id": str(roadmap_id), "user_id": str(user_id)},
        )


class RoadmapArchivedError(RoadmapError):
    """Raised when trying to operate on an archived roadmap."""

    def __init__(self, roadmap_id: UUID) -> None:
        super().__init__(
            code="roadmap_archived",
            message=f"Roadmap {roadmap_id} is archived and cannot be modified.",
            category=RoadmapErrorCategory.CONFLICT,
            context={"roadmap_id": str(roadmap_id)},
        )


class RoadmapCompletedError(RoadmapError):
    """Raised when trying to modify a completed roadmap without regeneration."""

    def __init__(self, roadmap_id: UUID) -> None:
        super().__init__(
            code="roadmap_completed",
            message=f"Roadmap {roadmap_id} is completed. Use regenerate to create a new version.",
            category=RoadmapErrorCategory.CONFLICT,
            context={"roadmap_id": str(roadmap_id)},
        )


class InvalidTransitionError(RoadmapError):
    """Raised when attempting an invalid roadmap or task state transition."""

    def __init__(
        self,
        from_state: str,
        to_state: str,
        resource_id: UUID | None = None,
        resource_type: str = "roadmap",
    ) -> None:
        super().__init__(
            code="invalid_transition",
            message=f"Invalid {resource_type} transition from {from_state} to {to_state}"
            f"{f' for {resource_id}' if resource_id else ''}.",
            category=RoadmapErrorCategory.INVALID_TRANSITION,
            context={
                "from_state": from_state,
                "to_state": to_state,
                "resource_id": str(resource_id) if resource_id else None,
                "resource_type": resource_type,
            },
        )


class CircularDependencyError(RoadmapError):
    """Raised when a circular dependency is detected."""

    def __init__(
        self,
        cycle: list[UUID],
        message: str | None = None,
    ) -> None:
        super().__init__(
            code="circular_dependency",
            message=message or f"Circular dependency detected: {' -> '.join(str(t) for t in cycle)}",
            category=RoadmapErrorCategory.CIRCULAR_DEPENDENCY,
            context={"cycle": [str(t) for t in cycle]},
        )


class MissingPrerequisiteError(RoadmapError):
    """Raised when a task prerequisite is missing."""

    def __init__(
        self,
        task_id: UUID,
        missing_prerequisite_id: UUID,
    ) -> None:
        super().__init__(
            code="missing_prerequisite",
            message=f"Task {task_id} depends on prerequisite {missing_prerequisite_id} which does not exist.",
            category=RoadmapErrorCategory.MISSING_PREREQUISITE,
            context={"task_id": str(task_id), "missing_prerequisite_id": str(missing_prerequisite_id)},
        )


class IneligibleActionError(RoadmapError):
    """Raised when an action is not eligible based on assessment."""

    def __init__(
        self,
        action: str,
        assessment_status: str,
        message: str | None = None,
    ) -> None:
        super().__init__(
            code="ineligible_action",
            message=message or f"Action '{action}' is not eligible with assessment status: {assessment_status}",
            category=RoadmapErrorCategory.INELIGIBLE_ACTION,
            context={"action": action, "assessment_status": assessment_status},
        )


class MissingEvidenceError(RoadmapError):
    """Raised when required evidence is missing for a task."""

    def __init__(
        self,
        task_id: UUID,
        evidence_type: str,
        message: str | None = None,
    ) -> None:
        super().__init__(
            code="missing_evidence",
            message=message or f"Task {task_id} requires {evidence_type} evidence which is not available.",
            category=RoadmapErrorCategory.MISSING_EVIDENCE,
            context={"task_id": str(task_id), "evidence_type": evidence_type},
        )


class TaskNotFoundError(RoadmapError):
    """Raised when a task is not found."""

    def __init__(self, task_id: UUID) -> None:
        super().__init__(
            code="task_not_found",
            message=f"Task {task_id} not found.",
            category=RoadmapErrorCategory.NOT_FOUND,
            context={"task_id": str(task_id)},
        )


class TaskForbiddenError(RoadmapError):
    """Raised when user tries to access a task they don't own."""

    def __init__(self, task_id: UUID, user_id: UUID) -> None:
        super().__init__(
            code="task_forbidden",
            message=f"Task {task_id} is not owned by user {user_id}.",
            category=RoadmapErrorCategory.FORBIDDEN,
            context={"task_id": str(task_id), "user_id": str(user_id)},
        )


class DependencyResolutionError(RoadmapError):
    """Raised when dependency resolution fails."""

    def __init__(
        self,
        message: str,
        task_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged = dict(context) if context else {}
        if task_id:
            merged["task_id"] = str(task_id)
        super().__init__(
            code="dependency_resolution_error",
            message=message,
            category=RoadmapErrorCategory.INTERNAL_ERROR,
            context=merged,
        )
