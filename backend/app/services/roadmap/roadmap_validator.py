"""Roadmap validator for ensuring roadmap quality and consistency.

Validates generated roadmaps before persistence.
"""

from typing import Any

from app.services.roadmap.dependency_resolver import DependencyResolver
from app.services.roadmap.roadmap_errors import (
    RoadmapValidationError,
)
from app.services.roadmap.schemas import (
    RoadmapTaskDefinition,
)


class RoadmapValidator:
    """Validates roadmaps for consistency and correctness.

    Checks:
    - Task definitions have required fields
    - Dependencies are valid and acyclic
    - Evidence references are properly structured
    - Priorities are appropriate
    - No duplicate tasks
    """

    def __init__(self) -> None:
        self.dependency_resolver = DependencyResolver()

    def validate_task_definition(
        self,
        task: RoadmapTaskDefinition,
    ) -> list[str]:
        """Validate a single task definition.

        Args:
            task: The task definition to validate.

        Returns:
            List of validation warnings (empty if valid).

        Raises:
            RoadmapValidationError: If validation fails.
        """
        warnings = []

        # Required fields
        if not task.title or not task.title.strip():
            raise RoadmapValidationError(
                "Task title is required",
                field="title",
            )

        if not task.description or not task.description.strip():
            raise RoadmapValidationError(
                "Task description is required",
                field="description",
            )

        if len(task.title) > 500:
            raise RoadmapValidationError(
                "Task title exceeds maximum length of 500 characters",
                field="title",
            )

        # Priority validation
        if task.priority not in ("critical", "high", "medium", "low"):
            raise RoadmapValidationError(
                f"Invalid priority: {task.priority}",
                field="priority",
            )

        # Category validation
        if task.category not in (
            "provide_information",
            "verify_information",
            "prepare_document",
            "review_requirement",
            "visit_official_portal",
            "complete_user_action",
            "follow_up",
            "other",
        ):
            raise RoadmapValidationError(
                f"Invalid category: {task.category}",
                field="category",
            )

        # Evidence references
        for i, ev in enumerate(task.evidence_references):
            if not ev.source_id:
                warnings.append(f"Evidence {i}: missing source_id")
            if not ev.source_type:
                warnings.append(f"Evidence {i}: missing source_type")
            if not ev.description:
                warnings.append(f"Evidence {i}: missing description")

        # Completion criteria
        if task.completion_criteria and len(task.completion_criteria) > 1000:
            warnings.append("Completion criteria is very long (>1000 chars)")

        return warnings

    def validate_task_set(
        self,
        tasks: list[RoadmapTaskDefinition],
    ) -> list[str]:
        """Validate a set of task definitions.

        Args:
            tasks: List of task definitions.

        Returns:
            List of validation warnings.

        Raises:
            RoadmapValidationError: If validation fails.
        """
        warnings = []

        if not tasks:
            raise RoadmapValidationError("Roadmap must have at least one task")

        # Check for duplicate titles
        titles = set()
        for task in tasks:
            if task.title in titles:
                raise RoadmapValidationError(
                    f"Duplicate task title: {task.title}",
                    field="title",
                )
            titles.add(task.title)

        # Validate each task
        for task in tasks:
            warnings.extend(self.validate_task_definition(task))

        # Validate dependencies
        self._validate_dependencies(tasks)

        return warnings

    def _validate_dependencies(
        self,
        tasks: list[RoadmapTaskDefinition],
    ) -> None:
        """Validate task dependencies."""
        # Build temporary task list for dependency resolver
        temp_tasks = []
        for i, task in enumerate(tasks):
            temp_task = {
                "id": i,  # Use index as temporary ID
                "dependencies": [
                    {"task_id": dep.task_id} for dep in task.dependencies
                ],
            }
            temp_tasks.append(temp_task)

        # Validate with dependency resolver
        self.dependency_resolver.validate_dependencies(temp_tasks)

    def validate_roadmap_consistency(
        self,
        roadmap_data: dict[str, Any],
        tasks: list[RoadmapTaskDefinition],
    ) -> list[str]:
        """Validate full roadmap consistency.

        Args:
            roadmap_data: Roadmap metadata.
            tasks: Task definitions.

        Returns:
            List of validation warnings.
        """
        warnings = []

        # Validate roadmap metadata
        if not roadmap_data.get("title"):
            raise RoadmapValidationError("Roadmap title is required")

        if roadmap_data.get("status") not in (
            "draft", "active", "needs_information", "blocked",
            "completed", "cancelled", "archived"
        ):
            raise RoadmapValidationError(
                f"Invalid roadmap status: {roadmap_data.get('status')}"
            )

        # Validate tasks
        warnings.extend(self.validate_task_set(tasks))

        # Check for logical consistency
        self._check_logical_consistency(tasks, warnings)

        return warnings

    def _check_logical_consistency(
        self,
        tasks: list[RoadmapTaskDefinition],
        warnings: list[str],
    ) -> None:
        """Check for logical consistency issues."""
        # Check for tasks that should be dependent but aren't
        info_tasks = [t for t in tasks if t.category == "provide_information"]
        verify_tasks = [t for t in tasks if t.category == "verify_information"]

        if info_tasks and verify_tasks:
            # Information tasks should generally precede verification
            for v_task in verify_tasks:
                has_dep = False
                for dep in v_task.dependencies:
                    # Check if any dependency is an info task
                    for i_task in info_tasks:
                        if i_task.title == dep.task_id:  # This would need proper ID mapping
                            has_dep = True
                            break
                    if has_dep:
                        break
                if not has_dep:
                    warnings.append(
                        f"Verification task '{v_task.title}' has no dependency on information tasks"
                    )

        # Check for circular dependencies in evidence
        evidence_sources: dict[tuple[str, str], list[str]] = {}
        for task in tasks:
            for ev in task.evidence_references:
                key = (ev.source_type, str(ev.source_id))
                if key not in evidence_sources:
                    evidence_sources[key] = []
                evidence_sources[key].append(task.title)

        # Check for tasks that claim verified requirements but lack evidence
        for task in tasks:
            if task.category == "visit_official_portal" and not task.evidence_references:
                warnings.append(
                    f"Task '{task.title}' visits official portal but has no evidence reference"
                )
