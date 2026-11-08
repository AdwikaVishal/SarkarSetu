"""Roadmap engine schemas and enums.

Defines the typed contracts for roadmap and task operations.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RoadmapStatus(StrEnum):
    """Roadmap status enum."""

    DRAFT = "draft"
    ACTIVE = "active"
    NEEDS_INFORMATION = "needs_information"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    """Task status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    NEEDS_CONFIRMATION = "needs_confirmation"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TaskCategory(StrEnum):
    """Task category enum."""

    PROVIDE_INFORMATION = "provide_information"
    VERIFY_INFORMATION = "verify_information"
    PREPARE_DOCUMENT = "prepare_document"
    REVIEW_REQUIREMENT = "review_requirement"
    VISIT_OFFICIAL_PORTAL = "visit_official_portal"
    COMPLETE_USER_ACTION = "complete_user_action"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class TaskPriority(StrEnum):
    """Task priority enum."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskDependency(BaseModel):
    """A task dependency relationship."""

    task_id: UUID = Field(..., description="ID of the prerequisite task.")
    dependency_type: str = Field(
        default="blocks",
        description="Type of dependency (e.g., 'blocks', 'relates_to').",
    )


class EvidenceReference(BaseModel):
    """Reference to supporting evidence for a task."""

    source_id: str = Field(..., description="Source document or evidence ID.")
    source_type: str = Field(
        ..., description="Type of source (e.g., 'document', 'eligibility_assessment', 'government_source')."
    )
    description: str = Field(..., description="What this evidence supports.")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the evidence was retrieved.",
    )


class RoadmapTaskDefinition(BaseModel):
    """Definition of a task to be created in a roadmap."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    category: TaskCategory
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: list[TaskDependency] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)
    workflow_step_id: str | None = None
    completion_criteria: str | None = None
    due_date: datetime | None = None
    official_portal_url: str | None = None


class RoadmapGenerationContext(BaseModel):
    """Context for roadmap generation."""

    user_id: UUID
    business_profile_id: UUID | None = None
    workflow_execution_id: str | None = None
    service_type: str | None = None
    eligibility_assessment_id: str | None = None
    business_attributes: dict[str, Any] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    document_status: dict[str, Any] = Field(default_factory=dict)
    existing_roadmap_id: UUID | None = None


class RoadmapGenerationResult(BaseModel):
    """Result of roadmap generation."""

    roadmap_id: UUID
    version: int
    tasks_created: int
    tasks_updated: int
    tasks_preserved: int
    tasks_archived: int
    warnings: list[str] = Field(default_factory=list)


class RoadmapTaskUpdate(BaseModel):
    """Update to a roadmap task."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=1)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    completion_criteria: str | None = None
    due_date: datetime | None = None
    official_portal_url: str | None = None
    evidence_references: list[EvidenceReference] | None = None


class RoadmapProgress(BaseModel):
    """Progress tracking for a roadmap."""

    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    blocked_tasks: int = 0
    needs_confirmation_tasks: int = 0
    pending_tasks: int = 0
    skipped_tasks: int = 0
    cancelled_tasks: int = 0
    progress_percentage: float = 0.0


class RoadmapDependencyGraph(BaseModel):
    """Dependency graph for a roadmap."""

    task_ids: list[UUID] = Field(default_factory=list)
    edges: list[tuple[UUID, UUID]] = Field(default_factory=list)
    blocked_task_ids: list[UUID] = Field(default_factory=list)
    ready_task_ids: list[UUID] = Field(default_factory=list)
    has_cycles: bool = False
    cycle_details: list[list[UUID]] = Field(default_factory=list)


class PriorityScore(BaseModel):
    """Priority calculation breakdown."""

    base_priority: int = 0
    blocks_other_tasks: int = 0
    mandatory_information: int = 0
    next_workflow_step: int = 0
    eligibility_uncertainty: int = 0
    verified_requirement: int = 0
    total_score: int = 0
    calculated_priority: TaskPriority = TaskPriority.MEDIUM
    reasoning: list[str] = Field(default_factory=list)


# API Request/Response schemas

class RoadmapGenerateRequest(BaseModel):
    """Request to generate a roadmap."""

    business_profile_id: UUID
    workflow_execution_id: str | None = None
    service_type: str | None = None
    eligibility_assessment_id: str | None = None
    regenerate: bool = False


class RoadmapRegenerateRequest(BaseModel):
    """Request to regenerate a roadmap."""

    preserve_completed: bool = True
    reason: str | None = None


class RoadmapListResponse(BaseModel):
    """Response for listing roadmaps."""

    roadmaps: list["RoadmapResponse"] = Field(default_factory=list)
    total_count: int = 0


class RoadmapDetailResponse(BaseModel):
    """Detailed roadmap response with tasks."""

    roadmap: "RoadmapResponse"
    tasks: list["RoadmapTaskResponse"] = Field(default_factory=list)
    progress: RoadmapProgress
    dependency_graph: RoadmapDependencyGraph


class RoadmapResponse(BaseModel):
    """Roadmap response schema."""

    id: UUID
    user_id: UUID
    business_profile_id: UUID | None
    workflow_execution_id: str | None = None
    service_type: str | None = None
    eligibility_assessment_id: str | None = None
    title: str
    description: str
    status: RoadmapStatus
    version: int = 1
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    blocked_tasks: int = 0
    progress_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoadmapTaskResponse(BaseModel):
    """Roadmap task response schema."""

    id: UUID
    roadmap_id: UUID
    title: str
    description: str
    category: TaskCategory
    priority: TaskPriority
    status: TaskStatus
    sequence_number: int
    dependencies: list[TaskDependency] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)
    workflow_step_id: str | None = None
    completion_criteria: str | None = None
    due_date: datetime | None = None
    official_portal_url: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
