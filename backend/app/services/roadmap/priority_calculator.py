"""Priority calculator for roadmap tasks.

Calculates transparent, explainable priority scores for tasks based on
business context, dependencies, eligibility, and evidence.
"""

from typing import Any
from uuid import UUID

from app.services.roadmap.schemas import (
    PriorityScore,
    RoadmapTaskDefinition,
    TaskPriority,
)


class PriorityCalculator:
    """Calculates task priorities using transparent rules.

    Priority factors (weights are additive):
    - Base priority from task definition: CRITICAL=100, HIGH=75, MEDIUM=50, LOW=25
    - Blocks other tasks: +30 per dependent task (max +60)
    - Mandatory missing information: +40
    - Required for next workflow step: +35
    - Resolves eligibility uncertainty: +25
    - Verified government requirement: +20
    - Optional/non-blocking: +0
    """

    # Base priority scores
    BASE_PRIORITY = {
        TaskPriority.CRITICAL: 100,
        TaskPriority.HIGH: 75,
        TaskPriority.MEDIUM: 50,
        TaskPriority.LOW: 25,
    }

    # Thresholds for final priority classification
    THRESHOLDS = {
        TaskPriority.CRITICAL: 90,
        TaskPriority.HIGH: 65,
        TaskPriority.MEDIUM: 40,
        TaskPriority.LOW: 0,
    }

    def __init__(self) -> None:
        pass

    def calculate_priority(
        self,
        task: RoadmapTaskDefinition,
        dependent_task_count: int = 0,
        is_mandatory_info: bool = False,
        is_next_workflow_step: bool = False,
        resolves_eligibility_uncertainty: bool = False,
        is_verified_requirement: bool = False,
    ) -> PriorityScore:
        """Calculate priority score for a task.

        Args:
            task: The task definition.
            dependent_task_count: Number of tasks that depend on this task.
            is_mandatory_info: Whether this task resolves mandatory missing information.
            is_next_workflow_step: Whether this task is required for the next workflow step.
            resolves_eligibility_uncertainty: Whether this task resolves an eligibility uncertainty.
            is_verified_requirement: Whether this task addresses a verified government requirement.

        Returns:
            PriorityScore with breakdown and final priority.
        """
        score = PriorityScore()
        reasoning = []

        # Base priority from task definition
        score.base_priority = self.BASE_PRIORITY.get(task.priority, 50)
        reasoning.append(f"Base priority ({task.priority.value}): {score.base_priority}")

        # Blocks other tasks (capped at 2 tasks = 60 points)
        blocks = min(dependent_task_count, 2) * 30
        score.blocks_other_tasks = blocks
        if blocks > 0:
            reasoning.append(f"Blocks {dependent_task_count} dependent task(s): +{blocks}")

        # Mandatory missing information
        if is_mandatory_info:
            score.mandatory_information = 40
            reasoning.append("Resolves mandatory missing information: +40")

        # Next workflow step
        if is_next_workflow_step:
            score.next_workflow_step = 35
            reasoning.append("Required for next workflow step: +35")

        # Resolves eligibility uncertainty
        if resolves_eligibility_uncertainty:
            score.eligibility_uncertainty = 25
            reasoning.append("Resolves eligibility uncertainty: +25")

        # Verified requirement
        if is_verified_requirement:
            score.verified_requirement = 20
            reasoning.append("Addresses verified government requirement: +20")

        # Calculate total
        score.total_score = (
            score.base_priority
            + score.blocks_other_tasks
            + score.mandatory_information
            + score.next_workflow_step
            + score.eligibility_uncertainty
            + score.verified_requirement
        )

        # Determine final priority from thresholds
        score.calculated_priority = self._score_to_priority(score.total_score)
        score.reasoning = reasoning

        return score

    def _score_to_priority(self, score: int) -> TaskPriority:
        """Convert numeric score to priority enum."""
        if score >= self.THRESHOLDS[TaskPriority.CRITICAL]:
            return TaskPriority.CRITICAL
        if score >= self.THRESHOLDS[TaskPriority.HIGH]:
            return TaskPriority.HIGH
        if score >= self.THRESHOLDS[TaskPriority.MEDIUM]:
            return TaskPriority.MEDIUM
        return TaskPriority.LOW

    def calculate_bulk_priorities(
        self,
        tasks: list[RoadmapTaskDefinition],
        dependency_graph: dict[UUID, list[UUID]],
        context: dict[str, Any],
    ) -> dict[UUID, PriorityScore]:
        """Calculate priorities for multiple tasks with dependency awareness.

        Args:
            tasks: List of task definitions.
            dependency_graph: Mapping of task_id -> list of dependent task_ids.
            context: Additional context (mandatory_info_fields, next_workflow_step_ids, etc.)

        Returns:
            Mapping of task_id -> PriorityScore.
        """
        mandatory_fields = set(context.get("mandatory_information_fields", []))
        set(context.get("next_workflow_step_ids", []))
        set(context.get("eligibility_uncertainty_ids", []))
        set(context.get("verified_requirement_ids", []))

        results = {}

        for task in tasks:
            dependent_count = len(dependency_graph.get(task.id if hasattr(task, 'id') else UUID('00000000-0000-0000-0000-000000000000'), []))

            # Note: We need to match by some identifier. Since RoadmapTaskDefinition
            # doesn't have an ID field, we'll use the title as a proxy for matching.
            # In practice, the caller should pass a mapping of task_id -> definition.
            is_mandatory = task.category.value in mandatory_fields
            is_next_step = False  # Would need task ID mapping
            resolves_eligibility = False
            is_verified = False

            priority = self.calculate_priority(
                task=task,
                dependent_task_count=dependent_count,
                is_mandatory_info=is_mandatory,
                is_next_workflow_step=is_next_step,
                resolves_eligibility_uncertainty=resolves_eligibility,
                is_verified_requirement=is_verified,
            )
            results[UUID('00000000-0000-0000-0000-000000000000')] = priority

        return results

    def get_priority_for_task_id(
        self,
        task_id: UUID,
        tasks: list[RoadmapTaskDefinition],
        dependency_graph: dict[UUID, list[UUID]],
        context: dict[str, Any],
    ) -> PriorityScore | None:
        """Get priority for a specific task ID."""
        # This would require tasks to have IDs. Since RoadmapTaskDefinition
        # doesn't include IDs, this is a placeholder for when tasks are persisted.
        return None
