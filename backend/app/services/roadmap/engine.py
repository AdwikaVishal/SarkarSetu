"""Roadmap engine - main orchestration service.

Coordinates roadmap generation, task management, progress tracking,
and integration with workflows, eligibility, and document intelligence.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BusinessProfile, Roadmap, RoadmapTask
from app.services.document_intelligence.document_service import DocumentIntelligenceService
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.ownership import OwnershipService
from app.services.roadmap.generator import RoadmapGenerator
from app.services.roadmap.progress_tracker import ProgressTracker
from app.services.roadmap.roadmap_errors import (
    RoadmapArchivedError,
    RoadmapCompletedError,
    RoadmapError,
    RoadmapErrorCategory,
)
from app.services.roadmap.schemas import (
    EvidenceReference,
    RoadmapGenerationContext,
    RoadmapGenerationResult,
    RoadmapProgress,
    RoadmapStatus,
    TaskStatus,
)
from app.services.roadmap.task_builder import TaskBuilder
from app.services.workflows.engine import WorkflowEngine
from app.services.workflows.state_manager import WorkflowStateManager

logger = logging.getLogger(__name__)


class RoadmapEngine:
    """Main roadmap orchestration engine.

    Integrates all roadmap operations:
    - Generation from workflow/eligibility/document context
    - Task creation and dependency management
    - Progress tracking
    - Regeneration and versioning
    """

    def __init__(
        self,
        db: AsyncSession,
        ownership_service: OwnershipService | None = None,
        eligibility_engine: EligibilityEngine | None = None,
        workflow_engine: WorkflowEngine | None = None,
        workflow_state_manager: WorkflowStateManager | None = None,
        document_service: DocumentIntelligenceService | None = None,
    ) -> None:
        self.db = db
        self.ownership = ownership_service or OwnershipService(db)
        self.eligibility_engine = eligibility_engine
        self.workflow_engine = workflow_engine
        self.workflow_state_manager = workflow_state_manager
        self.document_service = document_service

        self.generator = RoadmapGenerator()
        self.task_builder = TaskBuilder(db)
        self.progress_tracker = ProgressTracker(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_roadmap(
        self,
        user_id: UUID,
        business_profile_id: UUID,
        workflow_execution_id: str | None = None,
        service_type: str | None = None,
        eligibility_assessment_id: str | None = None,
        regenerate: bool = False,
    ) -> RoadmapGenerationResult:
        """Generate a personalized roadmap for the user.

        Args:
            user_id: Authenticated user ID.
            business_profile_id: Business profile ID.
            workflow_execution_id: Optional workflow execution ID.
            service_type: Optional service type identifier.
            eligibility_assessment_id: Optional eligibility assessment ID.
            regenerate: Whether to regenerate an existing roadmap.

        Returns:
            RoadmapGenerationResult with created roadmap and tasks.

        Raises:
            RoadmapForbiddenError: If user doesn't own the business profile.
            RoadmapArchivedError: If business profile is archived.
            RoadmapCompletedError: If roadmap is completed and regenerate=False.
        """
        # Validate ownership
        await self.ownership.get_user_business_profile(
            user_id, business_profile_id
        )

        # Check for existing active roadmap
        existing_roadmap = await self._get_active_roadmap(
            user_id, business_profile_id, service_type
        )

        if existing_roadmap and not regenerate:
            if existing_roadmap.status == RoadmapStatus.COMPLETED.value:
                raise RoadmapCompletedError(existing_roadmap.id)
            if existing_roadmap.status == RoadmapStatus.ARCHIVED.value:
                raise RoadmapArchivedError(existing_roadmap.id)

        # Build generation context
        context = await self._build_generation_context(
            user_id=user_id,
            business_profile_id=business_profile_id,
            workflow_execution_id=workflow_execution_id,
            service_type=service_type,
            eligibility_assessment_id=eligibility_assessment_id,
            existing_roadmap=existing_roadmap,
        )

        # Generate tasks
        task_definitions = await self.generator.generate(context)

        if regenerate and existing_roadmap:
            # Preserve completed tasks, archive obsolete ones
            result = await self._regenerate_roadmap(
                existing_roadmap, task_definitions, context
            )
        else:
            # Create new roadmap
            result = await self._create_new_roadmap(
                user_id, business_profile_id, task_definitions, context
            )

        return result

    async def get_roadmap(
        self,
        roadmap_id: UUID,
        user_id: UUID,
    ) -> Roadmap:
        """Get a roadmap by ID with ownership validation."""
        roadmap = await self.ownership.get_user_roadmap(user_id, roadmap_id)
        return roadmap

    async def list_roadmaps(
        self,
        user_id: UUID,
        business_profile_id: UUID | None = None,
        status: str | None = None,
    ) -> list[Roadmap]:
        """List roadmaps for a user."""
        query = select(Roadmap).where(Roadmap.user_id == user_id)

        if business_profile_id:
            query = query.where(Roadmap.business_profile_id == business_profile_id)
        if status:
            query = query.where(Roadmap.status == status)

        query = query.order_by(Roadmap.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def regenerate_roadmap(
        self,
        roadmap_id: UUID,
        user_id: UUID,
        preserve_completed: bool = True,
        reason: str | None = None,
    ) -> RoadmapGenerationResult:
        """Regenerate an existing roadmap with latest context.

        Args:
            roadmap_id: The roadmap ID.
            user_id: Authenticated user ID.
            preserve_completed: Whether to preserve completed tasks.
            reason: Optional reason for regeneration.

        Returns:
            RoadmapGenerationResult.
        """
        roadmap = await self.ownership.get_user_roadmap(user_id, roadmap_id)

        if roadmap.status == RoadmapStatus.ARCHIVED.value:
            raise RoadmapArchivedError(roadmap_id)

        # Get context from roadmap
        context = await self._build_generation_context(
            user_id=user_id,
            business_profile_id=roadmap.business_profile_id or UUID('00000000-0000-0000-0000-000000000000'),
            workflow_execution_id=roadmap.workflow_execution_id,
            service_type=roadmap.service_type,
            eligibility_assessment_id=roadmap.eligibility_assessment_id,
            existing_roadmap=roadmap,
        )

        # Generate new tasks
        task_definitions = await self.generator.generate(context)

        # Regenerate with preservation
        result = await self._regenerate_roadmap(
            roadmap, task_definitions, context, preserve_completed
        )

        return result

    async def update_task(
        self,
        roadmap_id: UUID,
        task_id: UUID,
        user_id: UUID,
        updates: dict[str, Any],
    ) -> RoadmapTask:
        """Update a task with ownership validation.

        Args:
            roadmap_id: The roadmap ID.
            task_id: The task ID.
            user_id: Authenticated user ID.
            updates: Dictionary of fields to update.

        Returns:
            Updated RoadmapTask.

        Raises:
            RoadmapForbiddenError: If user doesn't own the roadmap.
            InvalidTransitionError: If status transition is invalid.
        """
        await self.ownership.get_user_roadmap(user_id, roadmap_id)
        task = await self.ownership.get_user_roadmap_task(user_id, task_id)

        if task.roadmap_id != roadmap_id:
            raise RoadmapError(
                code="task_roadmap_mismatch",
                message=f"Task {task_id} does not belong to roadmap {roadmap_id}",
                category=RoadmapErrorCategory.CONFLICT,
            )

        # Validate status transition
        if "status" in updates:
            await self._validate_status_transition(
                task, updates["status"], roadmap_id
            )

        # Apply updates
        updated_task = await self.task_builder.update_task(task_id, updates)

        # Recalculate progress
        await self.progress_tracker.update_roadmap_progress(roadmap_id)

        return updated_task

    async def complete_task(
        self,
        roadmap_id: UUID,
        task_id: UUID,
        user_id: UUID,
    ) -> RoadmapTask:
        """Mark a task as complete with validation.

        Args:
            roadmap_id: The roadmap ID.
            task_id: The task ID.
            user_id: Authenticated user ID.

        Returns:
            Updated RoadmapTask.

        Raises:
            DependencyResolutionError: If prerequisites not met.
        """
        await self.ownership.get_user_roadmap(user_id, roadmap_id)
        task = await self.ownership.get_user_roadmap_task(user_id, task_id)

        if task.roadmap_id != roadmap_id:
            raise RoadmapError(
                code="task_roadmap_mismatch",
                message=f"Task {task_id} does not belong to roadmap {roadmap_id}",
                category=RoadmapErrorCategory.CONFLICT,
            )

        # Check if prerequisites are met
        can_execute, blocking = await self.task_builder.can_execute_task(task_id)
        if not can_execute:
            from app.services.roadmap.roadmap_errors import DependencyResolutionError
            raise DependencyResolutionError(
                f"Cannot complete task: {', '.join(blocking)}",
                task_id=task_id,
            )

        # Update status
        updated_task = await self.progress_tracker.update_task_status(
            task_id=task_id,
            new_status=TaskStatus.COMPLETED.value,
            completed_at=datetime.now(UTC),
        )

        return updated_task

    async def get_roadmap_progress(
        self,
        roadmap_id: UUID,
        user_id: UUID,
    ) -> RoadmapProgress:
        """Get progress for a roadmap."""
        await self.ownership.get_user_roadmap(user_id, roadmap_id)
        return await self.progress_tracker.calculate_roadmap_progress(roadmap_id)

    async def get_roadmap_with_tasks(
        self,
        roadmap_id: UUID,
        user_id: UUID,
    ) -> tuple[Roadmap, list[RoadmapTask]]:
        """Get a roadmap with all its tasks."""
        roadmap = await self.ownership.get_user_roadmap(user_id, roadmap_id)

        result = await self.db.execute(
            select(RoadmapTask)
            .where(RoadmapTask.roadmap_id == roadmap_id)
            .order_by(RoadmapTask.sequence_number)
        )
        tasks = list(result.scalars().all())

        return roadmap, tasks

    # ------------------------------------------------------------------
    # Private Helper Methods
    # ------------------------------------------------------------------

    async def _get_active_roadmap(
        self,
        user_id: UUID,
        business_profile_id: UUID,
        service_type: str | None,
    ) -> Roadmap | None:
        """Get the active roadmap for a business profile and service type."""
        query = select(Roadmap).where(
            Roadmap.user_id == user_id,
            Roadmap.business_profile_id == business_profile_id,
            Roadmap.status.in_([
                "draft", "active", "needs_information", "blocked"
            ]),
        )
        if service_type:
            query = query.where(Roadmap.service_type == service_type)

        query = query.order_by(Roadmap.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def _build_generation_context(
        self,
        user_id: UUID,
        business_profile_id: UUID | None,
        workflow_execution_id: str | None = None,
        service_type: str | None = None,
        eligibility_assessment_id: str | None = None,
        existing_roadmap: Roadmap | None = None,
    ) -> RoadmapGenerationContext:
        """Build the complete context for roadmap generation."""
        profile = None
        if business_profile_id:
            profile = await self.ownership.get_user_business_profile(
                user_id, business_profile_id
            )
        else:
            profile = None

        # Get business attributes
        business_attrs = self._profile_to_attributes(profile) if profile else {}

        # Get missing information from workflow
        missing_info = []
        if workflow_execution_id and self.workflow_state_manager:
            execution = await self.workflow_state_manager.get_workflow_execution(
                workflow_execution_id, user_id
            )
            if execution and execution.missing_information:
                missing_info = execution.missing_information.get("fields", [])

        # Get eligibility assessment if available
        if not eligibility_assessment_id and self.eligibility_engine:
            # Try to get latest assessment for this profile
            pass

        # Get document status
        doc_status = {}
        if self.document_service and business_profile_id:
            docs = await self.document_service.get_documents_for_business(
                business_profile_id, user_id
            )
            for doc in docs:
                if doc.extracted_data:
                    doc_status[str(doc.id)] = doc.extracted_data

        # Get evidence references
        evidence = []
        if workflow_execution_id and self.workflow_state_manager:
            execution = await self.workflow_state_manager.get_workflow_execution(
                workflow_execution_id, user_id
            )
            if execution and execution.evidence_references:
                evidence = [
                    EvidenceReference(
                        source_id=str(ref.get("document_id", "")),
                        source_type=ref.get("source_type", "government_source"),
                        description=ref.get("description", ""),
                        retrieved_at=datetime.fromisoformat(ref.get("retrieved_at", datetime.now(UTC).isoformat())),
                    )
                    for ref in execution.evidence_references
                ]

        return RoadmapGenerationContext(
            user_id=user_id,
            business_profile_id=business_profile_id,
            workflow_execution_id=workflow_execution_id,
            service_type=service_type,
            eligibility_assessment_id=eligibility_assessment_id,
            business_attributes=business_attrs,
            missing_information=missing_info,
            evidence_references=evidence,
            document_status=doc_status,
            existing_roadmap_id=existing_roadmap.id if existing_roadmap else None,
        )

    def _profile_to_attributes(self, profile: BusinessProfile) -> dict[str, Any]:
        """Convert business profile to attribute dictionary."""
        attrs = {
            "business_name": profile.business_name,
            "business_type": profile.business_type,
            "industry": profile.industry,
            "state": profile.state,
            "district": profile.district,
            "business_structure": profile.business_structure,
            "business_stage": profile.business_stage,
            "sales_channels": profile.sales_channels,
        }
        if profile.annual_turnover is not None:
            attrs["annual_turnover"] = str(profile.annual_turnover)
        if profile.employee_count is not None:
            attrs["employee_count"] = str(profile.employee_count)
        if profile.city:
            attrs["city"] = profile.city
        if profile.pincode:
            attrs["pincode"] = profile.pincode
        if profile.udyam_number:
            attrs["udyam_number"] = profile.udyam_number
        if profile.gstin:
            attrs["gstin"] = profile.gstin
        if profile.date_of_establishment:
            attrs["establishment_date"] = profile.date_of_establishment.isoformat()
        if profile.products_services:
            attrs["products_services"] = profile.products_services
        if profile.operating_mode:
            attrs["operating_mode"] = profile.operating_mode
        return attrs

    async def _create_new_roadmap(
        self,
        user_id: UUID,
        business_profile_id: UUID,
        task_definitions: list,
        context: RoadmapGenerationContext,
    ) -> RoadmapGenerationResult:
        """Create a new roadmap with tasks."""
        # Create roadmap
        roadmap = Roadmap(
            user_id=user_id,
            business_profile_id=business_profile_id,
            workflow_execution_id=context.workflow_execution_id,
            service_type=context.service_type,
            eligibility_assessment_id=context.eligibility_assessment_id,
            title=f"Roadmap for {context.service_type or 'Government Service'}",
            description=(
                f"Personalized action plan for {context.service_type or 'government service'} "
                f"based on your business profile."
            ),
            status=RoadmapStatus.DRAFT.value,
            version=1,
        )
        self.db.add(roadmap)
        await self.db.commit()
        await self.db.refresh(roadmap)

        # Create tasks
        if task_definitions:
            await self.task_builder.create_tasks(roadmap.id, task_definitions)

        # Update progress
        await self.progress_tracker.update_roadmap_progress(roadmap.id)

        # Update roadmap status
        roadmap.status = RoadmapStatus.ACTIVE.value
        await self.db.commit()

        return RoadmapGenerationResult(
            roadmap_id=roadmap.id,
            version=1,
            tasks_created=len(task_definitions),
            tasks_updated=0,
            tasks_preserved=0,
            tasks_archived=0,
        )

    async def _regenerate_roadmap(
        self,
        existing_roadmap: Roadmap,
        task_definitions: list,
        context: RoadmapGenerationContext,
        preserve_completed: bool = True,
    ) -> RoadmapGenerationResult:
        """Regenerate an existing roadmap with new tasks."""
        # Get existing tasks
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.roadmap_id == existing_roadmap.id)
        )
        existing_tasks = list(result.scalars().all())

        completed_task_ids = {
            t.id for t in existing_tasks if t.status == "completed"
        }

        # Map existing tasks by title for deduplication
        existing_by_title = {t.title: t for t in existing_tasks}

        tasks_created = 0
        tasks_updated = 0
        tasks_preserved = 0
        tasks_archived = 0

        for defn in task_definitions:
            existing = existing_by_title.get(defn.title)
            if existing:
                if existing.id in completed_task_ids and preserve_completed:
                    # Preserve completed task
                    tasks_preserved += 1
                    continue
                # Update existing task
                await self.task_builder.update_task(existing.id, {
                    "description": defn.description,
                    "priority": defn.priority.value,
                    "completion_criteria": defn.completion_criteria,
                    "due_date": defn.due_date,
                    "official_portal_url": defn.official_portal_url,
                })
                tasks_updated += 1
            else:
                # Create new task (will be created in batch below)
                tasks_created += 1

        # Create new tasks in batch
        new_definitions = [d for d in task_definitions if d.title not in existing_by_title]
        if new_definitions:
            await self.task_builder.create_tasks(existing_roadmap.id, new_definitions)

        # Archive tasks that no longer exist
        new_titles = {d.title for d in task_definitions}
        for task in existing_tasks:
            if task.title not in new_titles and task.status not in ("completed", "skipped"):
                task.status = "cancelled"
                task.updated_at = datetime.now(UTC)
                self.db.add(task)
                tasks_archived += 1

        # Update version
        existing_roadmap.version += 1
        existing_roadmap.updated_at = datetime.now(UTC)
        self.db.add(existing_roadmap)

        await self.db.commit()
        await self.progress_tracker.update_roadmap_progress(existing_roadmap.id)

        return RoadmapGenerationResult(
            roadmap_id=existing_roadmap.id,
            version=existing_roadmap.version,
            tasks_created=tasks_created,
            tasks_updated=tasks_updated,
            tasks_preserved=tasks_preserved,
            tasks_archived=tasks_archived,
        )

    async def _validate_status_transition(
        self,
        task: RoadmapTask,
        new_status: str,
        roadmap_id: UUID,
    ) -> None:
        """Validate a task status transition."""

        current_status = task.status
        valid_transitions = {
            "pending": {"in_progress", "blocked", "cancelled"},
            "in_progress": {"completed", "blocked", "needs_confirmation", "cancelled"},
            "blocked": {"pending", "cancelled"},
            "needs_confirmation": {"completed", "pending", "cancelled"},
            "completed": {"skipped"},
            "skipped": set(),
            "cancelled": set(),
        }

        if new_status not in valid_transitions.get(current_status, set()):
            from app.services.roadmap.roadmap_errors import InvalidTransitionError
            raise InvalidTransitionError(
                from_state=current_status,
                to_state=new_status,
                resource_id=task.id,
                resource_type="task",
            )

        # Check prerequisites for completion
        if new_status == "completed":
            can_execute, blocking = await self.task_builder.can_execute_task(task.id)
            if not can_execute:
                from app.services.roadmap.roadmap_errors import DependencyResolutionError
                raise DependencyResolutionError(
                    f"Cannot complete task: {', '.join(blocking)}",
                    task_id=task.id,
                )
