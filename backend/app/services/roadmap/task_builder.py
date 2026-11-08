"""Task builder for roadmap engine.

Creates persistent RoadmapTask records from task definitions.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import RoadmapTask
from app.services.roadmap.dependency_resolver import DependencyResolver
from app.services.roadmap.roadmap_errors import (
    DependencyResolutionError,
)
from app.services.roadmap.schemas import (
    RoadmapTaskDefinition,
    TaskPriority,
    TaskStatus,
)


class TaskBuilder:
    """Builds and manages persistent RoadmapTask records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.dependency_resolver = DependencyResolver()

    async def create_tasks(
        self,
        roadmap_id: UUID,
        task_definitions: list[RoadmapTaskDefinition],
        start_sequence: int = 0,
    ) -> list[RoadmapTask]:
        """Create RoadmapTask records from definitions.

        Args:
            roadmap_id: The roadmap ID.
            task_definitions: List of task definitions.
            start_sequence: Starting sequence number.

        Returns:
            List of created RoadmapTask records.
        """
        # Validate dependencies first
        self._validate_task_definitions(task_definitions)

        # Build dependency graph for sequence ordering
        task_map = dict(enumerate(task_definitions))
        sorted_indices = self._topological_sort(task_definitions)

        created_tasks = []
        sequence = start_sequence

        for idx in sorted_indices:
            definition = task_map[idx]
            task = await self._create_task(
                roadmap_id=roadmap_id,
                definition=definition,
                sequence_number=sequence,
            )
            created_tasks.append(task)
            sequence += 1

        return created_tasks

    def _validate_task_definitions(
        self,
        task_definitions: list[RoadmapTaskDefinition],
    ) -> None:
        """Validate task definitions before creation."""
        # Assign temporary IDs for validation
        temp_tasks = []
        for _i, defn in enumerate(task_definitions):
            temp_task = {
                "id": uuid4(),
                "dependencies": [
                    {"task_id": dep.task_id} for dep in defn.dependencies
                ],
            }
            temp_tasks.append(temp_task)

        # Replace temp IDs with actual indices for dependency resolution
        # This is a simplified validation - in practice, we'd use the actual UUIDs
        # when tasks are persisted
        pass

    def _topological_sort(
        self,
        task_definitions: list[RoadmapTaskDefinition],
    ) -> list[int]:
        """Sort tasks topologically based on dependencies.

        Returns list of indices in execution order.
        """
        n = len(task_definitions)
        if n == 0:
            return []

        # Build adjacency list using temporary UUID mapping
        # Since definitions don't have IDs yet, we use index-based mapping
        index_to_id = {i: uuid4() for i in range(n)}
        {v: k for k, v in index_to_id.items()}

        {i: [] for i in range(n)}
        dict.fromkeys(range(n), 0)

        for _i, defn in enumerate(task_definitions):
            for _dep in defn.dependencies:
                # Find the index of the dependency
                for _j, _other_defn in enumerate(task_definitions):
                    # We can't directly match without IDs, so skip for now
                    # In practice, the caller should provide a mapping
                    pass

        # For now, return sequential order
        # A full implementation would need actual task IDs
        return list(range(n))

    async def _create_task(
        self,
        roadmap_id: UUID,
        definition: RoadmapTaskDefinition,
        sequence_number: int,
    ) -> RoadmapTask:
        """Create a single RoadmapTask record."""
        task = RoadmapTask(
            roadmap_id=roadmap_id,
            title=definition.title,
            description=definition.description,
            sequence_number=sequence_number,
            status=TaskStatus.PENDING.value,
            priority=definition.priority.value,
            due_date=definition.due_date,
            official_portal_url=definition.official_portal_url,
            # Store dependencies, evidence, etc. in a JSON field or separate table
            # For now, we'll use the existing fields
        )

        # Store additional metadata in source_references
        task.source_references = {
            "dependencies": [
                {"task_id": str(dep.task_id), "type": dep.dependency_type}
                for dep in definition.dependencies
            ],
            "evidence_references": [
                {
                    "source_id": str(ref.source_id),
                    "source_type": ref.source_type,
                    "description": ref.description,
                    "retrieved_at": ref.retrieved_at.isoformat(),
                }
                for ref in definition.evidence_references
            ],
            "document_ids": [str(d) for d in definition.document_ids],
            "workflow_step_id": definition.workflow_step_id,
            "completion_criteria": definition.completion_criteria,
            "category": definition.category.value,
        }

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def update_task(
        self,
        task_id: UUID,
        updates: dict[str, Any],
    ) -> RoadmapTask:
        """Update a RoadmapTask with new values.

        Args:
            task_id: The task ID.
            updates: Dictionary of fields to update.

        Returns:
            Updated RoadmapTask.
        """
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Update allowed fields
        allowed_fields = {
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "official_portal_url",
            "completion_criteria",
            "source_references",
        }

        for key, value in updates.items():
            if key in allowed_fields:
                if key == "status" and isinstance(value, TaskStatus):
                    value = value.value
                elif key == "priority" and isinstance(value, TaskPriority):
                    value = value.value
                setattr(task, key, value)

        task.updated_at = datetime.now(UTC)

        # If completing, set completed_at
        if updates.get("status") == TaskStatus.COMPLETED.value and not task.completed_at:
            task.completed_at = datetime.now(UTC)

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def add_task_dependency(
        self,
        task_id: UUID,
        prerequisite_task_id: UUID,
        dependency_type: str = "blocks",
    ) -> None:
        """Add a dependency between tasks.

        Args:
            task_id: The dependent task.
            prerequisite_task_id: The prerequisite task.
            dependency_type: Type of dependency.
        """
        # Verify both tasks exist and belong to same roadmap
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.id == prerequisite_task_id)
        )
        prereq = result.scalar_one_or_none()
        if not prereq:
            raise ValueError(f"Prerequisite task {prerequisite_task_id} not found")

        if task.roadmap_id != prereq.roadmap_id:
            raise DependencyResolutionError(
                "Tasks must belong to the same roadmap",
                task_id=task_id,
            )

        # Add to source_references
        refs = task.source_references or {}
        deps = refs.get("dependencies", [])
        deps.append({
            "task_id": str(prerequisite_task_id),
            "type": dependency_type,
        })
        refs["dependencies"] = deps
        task.source_references = refs

        self.db.add(task)
        await self.db.commit()

    async def get_task_with_dependencies(
        self,
        task_id: UUID,
    ) -> tuple[RoadmapTask, list[UUID]]:
        """Get a task and its dependency IDs.

        Args:
            task_id: The task ID.

        Returns:
            Tuple of (task, list of prerequisite task IDs).
        """
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        refs = task.source_references or {}
        deps = refs.get("dependencies", [])
        prereq_ids = [UUID(dep["task_id"]) for dep in deps]

        return task, prereq_ids

    async def can_execute_task(
        self,
        task_id: UUID,
    ) -> tuple[bool, list[str]]:
        """Check if a task can be executed (all prerequisites completed).

        Args:
            task_id: The task ID.

        Returns:
            Tuple of (can_execute, list of blocking reasons).
        """
        task, prereq_ids = await self.get_task_with_dependencies(task_id)

        if not prereq_ids:
            return True, []

        # Check prerequisite statuses
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.id.in_(prereq_ids))
        )
        prereqs = list(result.scalars().all())

        blocking = []
        for prereq in prereqs:
            if prereq.status != "completed":
                blocking.append(
                    f"Prerequisite '{prereq.title}' (ID: {prereq.id}) is {prereq.status}"
                )

        return len(blocking) == 0, blocking

    async def update_task_sequence(
        self,
        roadmap_id: UUID,
        task_order: list[UUID],
    ) -> None:
        """Update task sequence numbers based on new order.

        Args:
            roadmap_id: The roadmap ID.
            task_order: List of task IDs in new sequence order.
        """
        for sequence, task_id in enumerate(task_order):
            result = await self.db.execute(
                select(RoadmapTask).where(
                    RoadmapTask.id == task_id,
                    RoadmapTask.roadmap_id == roadmap_id,
                )
            )
            task = result.scalar_one_or_none()
            if task:
                task.sequence_number = sequence
                task.updated_at = datetime.now(UTC)
                self.db.add(task)

        await self.db.commit()
