"""Progress tracker for roadmap tasks.

Calculates and maintains roadmap and task progress safely.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap
from app.models.task import RoadmapTask
from app.services.roadmap.schemas import RoadmapProgress


class ProgressTracker:
    """Tracks and calculates roadmap and task progress.

    Handles progress calculation, recalculation on task updates,
    and ensures consistency.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # Statuses that count as "completed" for progress percentage
    COMPLETED_STATUSES = {"completed"}

    # Statuses that count as "active" (in progress or waiting)
    ACTIVE_STATUSES = {"in_progress", "needs_confirmation", "pending"}

    # Statuses that indicate blocking
    BLOCKED_STATUSES = {"blocked"}

    # Terminal statuses (no further action expected)
    TERMINAL_STATUSES = {"completed", "skipped", "cancelled"}

    async def calculate_roadmap_progress(
        self,
        roadmap_id: UUID,
    ) -> RoadmapProgress:
        """Calculate progress for a roadmap.

        Args:
            roadmap_id: The roadmap ID.

        Returns:
            RoadmapProgress with counts and percentage.
        """
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.roadmap_id == roadmap_id)
        )
        tasks = list(result.scalars().all())

        progress = RoadmapProgress()
        progress.total_tasks = len(tasks)

        for task in tasks:
            if task.status in self.COMPLETED_STATUSES:
                progress.completed_tasks += 1
            elif task.status in self.ACTIVE_STATUSES:
                progress.in_progress_tasks += 1
                if task.status == "needs_confirmation":
                    progress.needs_confirmation_tasks += 1
            elif task.status in self.BLOCKED_STATUSES:
                progress.blocked_tasks += 1
            elif task.status == "pending":
                progress.pending_tasks += 1
            elif task.status == "skipped":
                progress.skipped_tasks += 1
            elif task.status == "cancelled":
                progress.cancelled_tasks += 1

        # Calculate progress percentage based on completed vs total actionable tasks
        # Exclude cancelled and skipped from denominator
        actionable_tasks = sum(
            1 for t in tasks if t.status not in {"cancelled", "skipped"}
        )
        if actionable_tasks > 0:
            progress.progress_percentage = round(
                (progress.completed_tasks / actionable_tasks) * 100, 2
            )
        else:
            progress.progress_percentage = 0.0

        return progress

    async def update_roadmap_progress(
        self,
        roadmap_id: UUID,
    ) -> Roadmap:
        """Update the roadmap's progress percentage in the database.

        Args:
            roadmap_id: The roadmap ID.

        Returns:
            Updated Roadmap model.
        """
        progress = await self.calculate_roadmap_progress(roadmap_id)

        result = await self.db.execute(
            select(Roadmap).where(Roadmap.id == roadmap_id)
        )
        roadmap = result.scalar_one_or_none()

        if roadmap:
            roadmap.progress_percentage = int(progress.progress_percentage)
            roadmap.total_tasks = progress.total_tasks
            roadmap.completed_tasks = progress.completed_tasks
            roadmap.pending_tasks = progress.pending_tasks
            roadmap.blocked_tasks = progress.blocked_tasks

            # Update status based on progress
            if progress.total_tasks == 0:
                roadmap.status = "draft"
            elif progress.progress_percentage >= 100:
                roadmap.status = "completed"
                roadmap.completed_at = datetime.now(UTC)
            elif progress.blocked_tasks == progress.total_tasks:
                roadmap.status = "blocked"
            elif progress.needs_confirmation_tasks > 0:
                roadmap.status = "needs_information"
            elif progress.in_progress_tasks > 0:
                roadmap.status = "active"
            else:
                roadmap.status = "active"

            roadmap.updated_at = datetime.now(UTC)
            self.db.add(roadmap)
            await self.db.commit()
            await self.db.refresh(roadmap)

            return roadmap

        raise ValueError(f"Roadmap {roadmap_id} not found")

    async def update_task_status(
        self,
        task_id: UUID,
        new_status: str,
        completed_at: datetime | None = None,
    ) -> RoadmapTask:
        """Update a task's status and recalculate roadmap progress.

        Args:
            task_id: The task ID.
            new_status: New task status.
            completed_at: Optional completion timestamp.

        Returns:
            Updated RoadmapTask model.
        """
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = new_status
        task.updated_at = datetime.now(UTC)

        if new_status == "completed" and not completed_at:
            task.completed_at = datetime.now(UTC)
        elif completed_at:
            task.completed_at = completed_at

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # Update roadmap progress
        await self.update_roadmap_progress(task.roadmap_id)

        return task

    async def get_task_completion_stats(
        self,
        roadmap_id: UUID,
    ) -> dict[str, Any]:
        """Get detailed completion statistics for a roadmap.

        Args:
            roadmap_id: The roadmap ID.

        Returns:
            Dictionary with completion statistics.
        """
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.roadmap_id == roadmap_id)
        )
        tasks = list(result.scalars().all())

        stats: dict[str, Any] = {
            "total": len(tasks),
            "by_status": {},
            "by_category": {},
            "by_priority": {},
            "completion_rate": 0.0,
            "average_completion_time": None,
        }

        completed_times = []

        for task in tasks:
            # By status
            stats["by_status"][task.status] = stats["by_status"].get(task.status, 0) + 1

            # By category (if available)
            if hasattr(task, "category") and task.category:
                stats["by_category"][task.category] = stats["by_category"].get(task.category, 0) + 1

            # By priority
            if task.priority:
                stats["by_priority"][task.priority] = stats["by_priority"].get(task.priority, 0) + 1

            # Completion time
            if task.status == "completed" and task.completed_at and task.created_at:
                delta = task.completed_at - task.created_at
                completed_times.append(delta.total_seconds())

        completed = stats["by_status"].get("completed", 0)
        actionable = sum(v for k, v in stats["by_status"].items() if k not in {"cancelled", "skipped"})
        if actionable > 0:
            stats["completion_rate"] = round((completed / actionable) * 100, 2)

        if completed_times:
            stats["average_completion_time"] = round(sum(completed_times) / len(completed_times), 2)

        return stats

    async def check_roadmap_completion(
        self,
        roadmap_id: UUID,
    ) -> bool:
        """Check if all actionable tasks in a roadmap are completed.

        Args:
            roadmap_id: The roadmap ID.

        Returns:
            True if all actionable tasks are completed.
        """
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.roadmap_id == roadmap_id)
        )
        tasks = list(result.scalars().all())

        if not tasks:
            return False

        for task in tasks:
            if task.status not in self.TERMINAL_STATUSES:
                return False

        return True
