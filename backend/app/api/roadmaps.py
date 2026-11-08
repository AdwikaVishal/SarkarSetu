"""Roadmap API router.

Provides authenticated endpoints for personalized roadmap management:

- POST /api/v1/roadmaps/generate - Generate a personalized roadmap
- GET /api/v1/roadmaps - List user's roadmaps
- GET /api/v1/roadmaps/{roadmap_id} - Get roadmap with tasks
- POST /api/v1/roadmaps/{roadmap_id}/regenerate - Regenerate roadmap
- GET /api/v1/roadmaps/{roadmap_id}/progress - Get progress summary
- PATCH /api/v1/roadmaps/{roadmap_id}/tasks/{task_id} - Update task
- POST /api/v1/roadmaps/{roadmap_id}/tasks/{task_id}/complete - Complete task
- POST /api/v1/roadmaps/{roadmap_id}/tasks/{task_id}/skip - Skip task
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.services.roadmap.engine import RoadmapEngine
from app.services.roadmap.roadmap_errors import (
    RoadmapArchivedError,
    RoadmapCompletedError,
    RoadmapError,
    RoadmapForbiddenError,
    RoadmapNotFoundError,
    RoadmapValidationError,
)
from app.services.roadmap.schemas import (
    RoadmapDependencyGraph,
    RoadmapDetailResponse,
    RoadmapGenerateRequest,
    RoadmapListResponse,
    RoadmapProgress,
    RoadmapRegenerateRequest,
    RoadmapResponse,
    RoadmapStatus,
    RoadmapTaskResponse,
    RoadmapTaskUpdate,
    TaskCategory,
    TaskPriority,
    TaskStatus,
)

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


async def get_roadmap_engine(
    db: AsyncSession = Depends(get_db),
) -> RoadmapEngine:
    """Dependency to get RoadmapEngine instance."""
    from app.services.document_intelligence.document_service import DocumentIntelligenceService
    from app.services.eligibility_engine.engine import EligibilityEngine
    from app.services.eligibility_engine.rule_evaluator import RuleEvaluator
    from app.services.eligibility_engine.rule_registry import RuleRegistry
    from app.services.ownership import OwnershipService
    from app.services.workflows.engine import WorkflowEngine
    from app.services.workflows.state_manager import WorkflowStateManager

    ownership = OwnershipService(db)
    rule_registry = RuleRegistry(db)
    eligibility_engine = EligibilityEngine(
        registry=rule_registry,
        evaluator=RuleEvaluator(),
    )
    workflow_state_manager = WorkflowStateManager(db)
    workflow_engine = WorkflowEngine(
        state_manager=workflow_state_manager,
        step_executor=None,
        ai_service=None,
        conversation_service=None,
        clarification_service=None,
        eligibility_engine=eligibility_engine,
        retrieval_provider=None,
    )
    document_service = DocumentIntelligenceService(
        db=db,
        eligibility_engine=eligibility_engine,
    )

    return RoadmapEngine(
        db=db,
        ownership_service=ownership,
        eligibility_engine=eligibility_engine,
        workflow_engine=workflow_engine,
        workflow_state_manager=workflow_state_manager,
        document_service=document_service,
    )


@router.post(
    "/generate",
    response_model=RoadmapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a personalized roadmap",
    description=(
        "Generate a personalized action roadmap for a business profile. "
        "Integrates workflow state, eligibility assessments, and document intelligence "
        "to create an actionable plan."
    ),
)
async def generate_roadmap(
    request: RoadmapGenerateRequest,
    engine: RoadmapEngine = Depends(get_roadmap_engine),
    current_user: User = Depends(get_current_active_user),
) -> RoadmapResponse:
    """Generate a new personalized roadmap."""
    try:
        result = await engine.generate_roadmap(
            user_id=current_user.id,
            business_profile_id=request.business_profile_id,
            workflow_execution_id=request.workflow_execution_id,
            service_type=request.service_type,
            eligibility_assessment_id=request.eligibility_assessment_id,
            regenerate=request.regenerate,
        )

        # Return the created roadmap
        roadmap = await engine.get_roadmap(result.roadmap_id, current_user.id)
        return RoadmapResponse(
            id=roadmap.id,
            user_id=roadmap.user_id,
            business_profile_id=roadmap.business_profile_id,
            workflow_execution_id=roadmap.workflow_execution_id,
            service_type=roadmap.service_type,
            eligibility_assessment_id=roadmap.eligibility_assessment_id,
            title=roadmap.title,
            description=roadmap.description,
            status=RoadmapStatus(roadmap.status),
            version=roadmap.version,
            total_tasks=roadmap.total_tasks,
            completed_tasks=roadmap.completed_tasks,
            pending_tasks=roadmap.pending_tasks,
            blocked_tasks=roadmap.blocked_tasks,
            progress_percentage=roadmap.progress_percentage,
            created_at=roadmap.created_at,
            updated_at=roadmap.updated_at,
            completed_at=roadmap.completed_at,
        )

    except RoadmapValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e
    except RoadmapForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.to_dict(),
        ) from e
    except RoadmapArchivedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.to_dict(),
        ) from e
    except RoadmapCompletedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.to_dict(),
        ) from e
    except RoadmapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e
    except Exception as exc:  # noqa: BLE001
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Roadmap generation error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the roadmap.",
        ) from exc


@router.get(
    "/",
    response_model=RoadmapListResponse,
    summary="List user's roadmaps",
    description="List all roadmaps for the authenticated user.",
)
async def list_roadmaps(
    business_profile_id: UUID | None = None,
    status: str | None = None,
    engine: RoadmapEngine = Depends(get_roadmap_engine),
    current_user: User = Depends(get_current_active_user),
) -> RoadmapListResponse:
    """List all roadmaps for the authenticated user."""
    roadmaps = await engine.list_roadmaps(
        user_id=current_user.id,
        business_profile_id=business_profile_id,
        status=status,
    )

    roadmap_responses = [
        RoadmapResponse(
            id=r.id,
            user_id=r.user_id,
            business_profile_id=r.business_profile_id,
            workflow_execution_id=r.workflow_execution_id,
            service_type=r.service_type,
            eligibility_assessment_id=r.eligibility_assessment_id,
            title=r.title,
            description=r.description,
            status=RoadmapStatus(r.status),
            version=r.version,
            total_tasks=r.total_tasks,
            completed_tasks=r.completed_tasks,
            pending_tasks=r.pending_tasks,
            blocked_tasks=r.blocked_tasks,
            progress_percentage=r.progress_percentage,
            created_at=r.created_at,
            updated_at=r.updated_at,
            completed_at=r.completed_at,
        )
        for r in roadmaps
    ]

    return RoadmapListResponse(
        roadmaps=roadmap_responses,
        total_count=len(roadmap_responses),
    )


@router.get(
    "/{roadmap_id}",
    response_model=RoadmapDetailResponse,
    summary="Get roadmap with tasks",
    description="Get a roadmap with all its tasks and progress.",
)
async def get_roadmap(
    roadmap_id: UUID,
    engine: RoadmapEngine = Depends(get_roadmap_engine),
    current_user: User = Depends(get_current_active_user),
) -> RoadmapDetailResponse:
    """Get a roadmap with all its tasks and progress."""
    try:
        roadmap, tasks = await engine.get_roadmap_with_tasks(
            roadmap_id=roadmap_id,
            user_id=current_user.id,
        )
        progress = await engine.get_roadmap_progress(roadmap_id, current_user.id)

        return RoadmapDetailResponse(
            roadmap=RoadmapResponse(
                id=roadmap.id,
                user_id=roadmap.user_id,
                business_profile_id=roadmap.business_profile_id,
                workflow_execution_id=roadmap.workflow_execution_id,
                service_type=roadmap.service_type,
                eligibility_assessment_id=roadmap.eligibility_assessment_id,
                title=roadmap.title,
                description=roadmap.description,
                status=RoadmapStatus(roadmap.status),
                version=roadmap.version,
                total_tasks=roadmap.total_tasks,
                completed_tasks=roadmap.completed_tasks,
                pending_tasks=roadmap.pending_tasks,
                blocked_tasks=roadmap.blocked_tasks,
                progress_percentage=roadmap.progress_percentage,
                created_at=roadmap.created_at,
                updated_at=roadmap.updated_at,
                completed_at=roadmap.completed_at,
            ),
            tasks=[
                RoadmapTaskResponse(
                    id=t.id,
                    roadmap_id=t.roadmap_id,
                    title=t.title,
                    description=t.description,
                    category=TaskCategory(t.category),
                    priority=TaskPriority(t.priority),
                    status=TaskStatus(t.status),
                    sequence_number=t.sequence_number,
                    dependencies=t.source_references.get("dependencies", []) if t.source_references else [],
                    evidence_references=t.source_references.get("evidence_references", []) if t.source_references else [],
                    document_ids=[UUID(d) for d in t.source_references.get("document_ids", [])] if t.source_references else [],
                    workflow_step_id=t.source_references.get("workflow_step_id") if t.source_references else None,
                    completion_criteria=t.source_references.get("completion_criteria") if t.source_references else None,
                    due_date=t.due_date,
                    official_portal_url=t.official_portal_url,
                    completed_at=t.completed_at,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
                for t in tasks
            ],
            progress=progress,
            dependency_graph=RoadmapDependencyGraph(
                task_ids=[t.id for t in tasks],
                edges=[],
                blocked_task_ids=[],
                ready_task_ids=[],
                has_cycles=False,
                cycle_details=[],
            ),
        )

    except RoadmapNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict(),
        ) from e
    except RoadmapForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.to_dict(),
        ) from e
    except RoadmapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e
    except Exception as exc:  # noqa: BLE001
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Get roadmap error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the roadmap.",
        ) from exc


@router.post(
    "/{roadmap_id}/regenerate",
    response_model=RoadmapResponse,
    summary="Regenerate a roadmap",
    description="Regenerate a roadmap with the latest context.",
)
async def regenerate_roadmap(
    roadmap_id: UUID,
    request: RoadmapRegenerateRequest,
    engine: RoadmapEngine = Depends(get_roadmap_engine),
    current_user: User = Depends(get_current_active_user),
) -> RoadmapResponse:
    """Regenerate an existing roadmap."""
    try:
        result = await engine.regenerate_roadmap(
            roadmap_id=roadmap_id,
            user_id=current_user.id,
            preserve_completed=request.preserve_completed,
            reason=request.reason,
        )

        roadmap = await engine.get_roadmap(result.roadmap_id, current_user.id)
        return RoadmapResponse(
            id=roadmap.id,
            user_id=roadmap.user_id,
            business_profile_id=roadmap.business_profile_id,
            workflow_execution_id=roadmap.workflow_execution_id,
            service_type=roadmap.service_type,
            eligibility_assessment_id=roadmap.eligibility_assessment_id,
            title=roadmap.title,
            description=roadmap.description,
            status=RoadmapStatus(roadmap.status),
            version=roadmap.version,
            total_tasks=roadmap.total_tasks,
            completed_tasks=roadmap.completed_tasks,
            pending_tasks=roadmap.pending_tasks,
            blocked_tasks=roadmap.blocked_tasks,
            progress_percentage=roadmap.progress_percentage,
            created_at=roadmap.created_at,
            updated_at=roadmap.updated_at,
            completed_at=roadmap.completed_at,
        )

    except RoadmapNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict(),
        ) from e
    except RoadmapForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.to_dict(),
        ) from e
    except RoadmapArchivedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.to_dict(),
        ) from e
    except RoadmapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e
    except Exception as exc:  # noqa: BLE001
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Roadmap regeneration error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while regenerating the roadmap.",
        ) from exc


@router.get(
    "/{roadmap_id}/progress",
    response_model=RoadmapProgress,
    summary="Get roadmap progress",
    description="Get detailed progress information for a roadmap.",
)
async def get_roadmap_progress(
    roadmap_id: UUID,
    engine: RoadmapEngine = Depends(get_roadmap_engine),
    current_user: User = Depends(get_current_active_user),
) -> RoadmapProgress:
    """Get detailed progress for a roadmap."""
    try:
        progress = await engine.get_roadmap_progress(roadmap_id, current_user.id)
        return progress
    except RoadmapNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict(),
        ) from e
    except RoadmapForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.to_dict(),
        ) from e
    except RoadmapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e


@router.patch(
    "/{roadmap_id}/tasks/{task_id}",
    response_model=RoadmapTaskResponse,
    summary="Update a roadmap task",
    description="Update a task in a roadmap.",
)
async def update_task(
    roadmap_id: UUID,
    task_id: UUID,
    request: RoadmapTaskUpdate,
    engine: RoadmapEngine = Depends(get_roadmap_engine),
    current_user: User = Depends(get_current_active_user),
) -> RoadmapTaskResponse:
    """Update a task in a roadmap."""
    try:
        updates = request.model_dump(exclude_unset=True)
        task = await engine.update_task(
            roadmap_id=roadmap_id,
            task_id=task_id,
            user_id=current_user.id,
            updates=updates,
        )

        return RoadmapTaskResponse(
            id=task.id,
            roadmap_id=task.roadmap_id,
            title=task.title,
            description=task.description,
            category=TaskCategory(task.category),
            priority=TaskPriority(task.priority),
            status=TaskStatus(task.status),
            sequence_number=task.sequence_number,
            dependencies=task.source_references.get("dependencies", []) if task.source_references else [],
            evidence_references=task.source_references.get("evidence_references", []) if task.source_references else [],
            document_ids=[UUID(d) for d in task.source_references.get("document_ids", [])] if task.source_references else [],
            workflow_step_id=task.source_references.get("workflow_step_id") if task.source_references else None,
            completion_criteria=task.source_references.get("completion_criteria") if task.source_references else None,
            due_date=task.due_date,
            official_portal_url=task.official_portal_url,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    except RoadmapNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict(),
        ) from e
    except RoadmapForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.to_dict(),
        ) from e
    except RoadmapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e
    except Exception as exc:  # noqa: BLE001
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Update task error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the task.",
        ) from exc


@router.post(
    "/{roadmap_id}/tasks/{task_id}/complete",
    response_model=RoadmapTaskResponse,
    summary="Complete a roadmap task",
    description="Mark a task as complete with prerequisite validation.",
)
async def complete_task(
    roadmap_id: UUID,
    task_id: UUID,
    engine: RoadmapEngine = Depends(get_roadmap_engine),
    current_user: User = Depends(get_current_active_user),
) -> RoadmapTaskResponse:
    """Mark a task as complete with prerequisite validation."""
    try:
        task = await engine.complete_task(
            roadmap_id=roadmap_id,
            task_id=task_id,
            user_id=current_user.id,
        )

        return RoadmapTaskResponse(
            id=task.id,
            roadmap_id=task.roadmap_id,
            title=task.title,
            description=task.description,
            category=TaskCategory(task.category),
            priority=TaskPriority(task.priority),
            status=TaskStatus(task.status),
            sequence_number=task.sequence_number,
            dependencies=task.source_references.get("dependencies", []) if task.source_references else [],
            evidence_references=task.source_references.get("evidence_references", []) if task.source_references else [],
            document_ids=[UUID(d) for d in task.source_references.get("document_ids", [])] if task.source_references else [],
            workflow_step_id=task.source_references.get("workflow_step_id") if task.source_references else None,
            completion_criteria=task.source_references.get("completion_criteria") if task.source_references else None,
            due_date=task.due_date,
            official_portal_url=task.official_portal_url,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    except RoadmapNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict(),
        ) from e
    except RoadmapForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.to_dict(),
        ) from e
    except RoadmapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e
    except Exception as exc:  # noqa: BLE001
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Complete task error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while completing the task.",
        ) from exc


@router.post(
    "/{roadmap_id}/tasks/{task_id}/skip",
    response_model=RoadmapTaskResponse,
    summary="Skip a roadmap task",
    description="Mark a task as skipped.",
)
async def skip_task(
    roadmap_id: UUID,
    task_id: UUID,
    engine: RoadmapEngine = Depends(get_roadmap_engine),
    current_user: User = Depends(get_current_active_user),
) -> RoadmapTaskResponse:
    """Mark a task as skipped."""
    try:
        task = await engine.update_task(
            roadmap_id=roadmap_id,
            task_id=task_id,
            user_id=current_user.id,
            updates={"status": "skipped"},
        )

        return RoadmapTaskResponse(
            id=task.id,
            roadmap_id=task.roadmap_id,
            title=task.title,
            description=task.description,
            category=TaskCategory(task.category),
            priority=TaskPriority(task.priority),
            status=TaskStatus(task.status),
            sequence_number=task.sequence_number,
            dependencies=task.source_references.get("dependencies", []) if task.source_references else [],
            evidence_references=task.source_references.get("evidence_references", []) if task.source_references else [],
            document_ids=[UUID(d) for d in task.source_references.get("document_ids", [])] if task.source_references else [],
            workflow_step_id=task.source_references.get("workflow_step_id") if task.source_references else None,
            completion_criteria=task.source_references.get("completion_criteria") if task.source_references else None,
            due_date=task.due_date,
            official_portal_url=task.official_portal_url,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    except RoadmapNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict(),
        ) from e
    except RoadmapForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.to_dict(),
        ) from e
    except RoadmapError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e
    except Exception as exc:  # noqa: BLE001
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Skip task error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while skipping the task.",
        ) from exc
