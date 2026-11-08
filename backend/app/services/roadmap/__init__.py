"""Personalized Roadmap & Task Engine for SarkarSetu AI.

Converts workflow outputs, eligibility assessments, and document intelligence
into structured, personalized, actionable roadmaps for entrepreneurs.

Components:
- RoadmapEngine: Main orchestration service
- RoadmapGenerator: Generates tasks from business context
- TaskBuilder: Creates persistent RoadmapTask records
- DependencyResolver: Validates and manages task dependencies
- PriorityCalculator: Calculates transparent task priorities
- ProgressTracker: Calculates and maintains roadmap progress
- EvidenceMapper: Maps evidence from various sources to tasks
- RoadmapValidator: Validates roadmap quality and consistency
"""

from app.services.roadmap.dependency_resolver import DependencyResolver
from app.services.roadmap.engine import RoadmapEngine
from app.services.roadmap.evidence_mapper import EvidenceMapper
from app.services.roadmap.generator import RoadmapGenerator
from app.services.roadmap.priority_calculator import PriorityCalculator
from app.services.roadmap.progress_tracker import ProgressTracker
from app.services.roadmap.roadmap_errors import (
    CircularDependencyError,
    DependencyResolutionError,
    IneligibleActionError,
    InvalidTransitionError,
    MissingEvidenceError,
    MissingPrerequisiteError,
    RoadmapArchivedError,
    RoadmapCompletedError,
    RoadmapError,
    RoadmapErrorCategory,
    RoadmapForbiddenError,
    RoadmapNotFoundError,
    RoadmapValidationError,
    TaskForbiddenError,
    TaskNotFoundError,
)
from app.services.roadmap.roadmap_validator import RoadmapValidator
from app.services.roadmap.schemas import (
    EvidenceReference,
    PriorityScore,
    RoadmapDependencyGraph,
    RoadmapDetailResponse,
    RoadmapGenerateRequest,
    RoadmapGenerationContext,
    RoadmapGenerationResult,
    RoadmapListResponse,
    RoadmapProgress,
    RoadmapRegenerateRequest,
    RoadmapResponse,
    RoadmapStatus,
    RoadmapTaskDefinition,
    RoadmapTaskResponse,
    RoadmapTaskUpdate,
    TaskCategory,
    TaskDependency,
    TaskPriority,
    TaskStatus,
)
from app.services.roadmap.task_builder import TaskBuilder

__all__ = [
    # Engine
    "RoadmapEngine",
    # Generator
    "RoadmapGenerator",
    # Task Builder
    "TaskBuilder",
    # Dependency Resolver
    "DependencyResolver",
    # Priority Calculator
    "PriorityCalculator",
    # Progress Tracker
    "ProgressTracker",
    # Evidence Mapper
    "EvidenceMapper",
    # Validator
    "RoadmapValidator",
    # Schemas
    "RoadmapStatus",
    "TaskStatus",
    "TaskCategory",
    "TaskPriority",
    "EvidenceReference",
    "RoadmapTaskDefinition",
    "RoadmapGenerationContext",
    "RoadmapGenerationResult",
    "RoadmapProgress",
    "RoadmapDependencyGraph",
    "PriorityScore",
    "TaskDependency",
    "RoadmapResponse",
    "RoadmapTaskResponse",
    "RoadmapGenerateRequest",
    "RoadmapRegenerateRequest",
    "RoadmapListResponse",
    "RoadmapDetailResponse",
    "RoadmapTaskUpdate",
    # Errors
    "RoadmapError",
    "RoadmapErrorCategory",
    "RoadmapValidationError",
    "RoadmapNotFoundError",
    "RoadmapForbiddenError",
    "RoadmapArchivedError",
    "RoadmapCompletedError",
    "InvalidTransitionError",
    "CircularDependencyError",
    "MissingPrerequisiteError",
    "IneligibleActionError",
    "MissingEvidenceError",
    "TaskNotFoundError",
    "TaskForbiddenError",
    "DependencyResolutionError",
]
