"""Dependency resolver for roadmap tasks.

Validates and manages task dependencies, prevents circular dependencies,
and determines which tasks are ready to execute.
"""

from collections import defaultdict, deque
from typing import Any
from uuid import UUID

from app.services.roadmap.roadmap_errors import (
    CircularDependencyError,
    DependencyResolutionError,
    MissingPrerequisiteError,
)
from app.services.roadmap.schemas import (
    RoadmapDependencyGraph,
)


class DependencyResolver:
    """Resolves and validates task dependencies.

    Builds a dependency graph, detects cycles, and determines
    which tasks are ready to execute based on prerequisite completion.
    """

    def __init__(self) -> None:
        pass

    def build_dependency_graph(
        self,
        tasks: list[dict[str, Any]],
    ) -> RoadmapDependencyGraph:
        """Build a dependency graph from task definitions.

        Args:
            tasks: List of task dictionaries with 'id' and 'dependencies' fields.

        Returns:
            RoadmapDependencyGraph with nodes, edges, and ready/blocked tasks.
        """
        graph = RoadmapDependencyGraph()
        task_ids = set()
        edges = []

        for task in tasks:
            task_id = task.get("id")
            if not task_id:
                continue

            if isinstance(task_id, str):
                task_id = UUID(task_id)
            task_ids.add(task_id)

            dependencies = task.get("dependencies", [])
            for dep in dependencies:
                dep_id = dep.get("task_id")
                if isinstance(dep_id, str):
                    dep_id = UUID(dep_id)
                edges.append((dep_id, task_id))

        graph.task_ids = list(task_ids)
        graph.edges = edges

        # Find ready tasks (no unmet prerequisites)
        self._update_graph_state(graph, set())

        return graph

    def _update_graph_state(
        self,
        graph: RoadmapDependencyGraph,
        completed_task_ids: set[UUID],
    ) -> None:
        """Update blocked/ready task lists based on completed tasks."""
        # Build adjacency list for prerequisites
        prerequisites = defaultdict(set)
        dependents = defaultdict(set)

        for from_id, to_id in graph.edges:
            prerequisites[to_id].add(from_id)
            dependents[from_id].add(to_id)

        # Determine blocked and ready tasks
        blocked = []
        ready = []

        for task_id in graph.task_ids:
            if task_id in completed_task_ids:
                continue

            prereqs = prerequisites.get(task_id, set())
            unmet = prereqs - completed_task_ids

            if unmet:
                blocked.append(task_id)
            else:
                ready.append(task_id)

        graph.blocked_task_ids = blocked
        graph.ready_task_ids = ready

    def validate_dependencies(
        self,
        tasks: list[dict[str, Any]],
    ) -> list[str]:
        """Validate all task dependencies.

        Args:
            tasks: List of task dictionaries.

        Returns:
            List of validation warnings.

        Raises:
            MissingPrerequisiteError: If a prerequisite task doesn't exist.
            CircularDependencyError: If a circular dependency is detected.
        """
        task_ids = set()
        edges = []

        for task in tasks:
            task_id = task.get("id")
            if not task_id:
                continue
            if isinstance(task_id, str):
                task_id = UUID(task_id)
            task_ids.add(task_id)

            dependencies = task.get("dependencies", [])
            for dep in dependencies:
                dep_id = dep.get("task_id")
                if isinstance(dep_id, str):
                    dep_id = UUID(dep_id)
                if dep_id not in task_ids:
                    raise MissingPrerequisiteError(
                        task_id=task_id,
                        missing_prerequisite_id=dep_id,
                    )
                edges.append((dep_id, task_id))

        # Check for cycles using Kahn's algorithm
        self._detect_cycles(task_ids, edges)

        return []

    def _detect_cycles(
        self,
        task_ids: set[UUID],
        edges: list[tuple[UUID, UUID]],
    ) -> None:
        """Detect cycles in the dependency graph using Kahn's algorithm.

        Raises:
            CircularDependencyError: If a cycle is detected.
        """
        # Build adjacency and in-degree
        adj = defaultdict(set)
        in_degree = defaultdict(int)

        for task_id in task_ids:
            in_degree[task_id] = 0

        for from_id, to_id in edges:
            adj[from_id].add(to_id)
            in_degree[to_id] += 1

        # Kahn's algorithm
        queue = deque([tid for tid in task_ids if in_degree[tid] == 0])
        processed = []

        while queue:
            current = queue.popleft()
            processed.append(current)

            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(processed) != len(task_ids):
            # Cycle detected - find the cycle
            remaining = task_ids - set(processed)
            cycle = self._find_cycle(remaining, edges)
            raise CircularDependencyError(cycle=cycle)

    def _find_cycle(
        self,
        remaining: set[UUID],
        edges: list[tuple[UUID, UUID]],
    ) -> list[UUID]:
        """Find a cycle in the remaining graph using DFS."""
        adj = defaultdict(set)
        for from_id, to_id in edges:
            if from_id in remaining and to_id in remaining:
                adj[from_id].add(to_id)

        visited = set()
        rec_stack = set()
        cycle_path = []

        def dfs(node: UUID) -> list[UUID] | None:
            visited.add(node)
            rec_stack.add(node)
            cycle_path.append(node)

            for neighbor in adj.get(node, set()):
                if neighbor not in visited:
                    result = dfs(neighbor)
                    if result is not None:
                        return result
                elif neighbor in rec_stack:
                    # Found cycle - extract it
                    idx = cycle_path.index(neighbor)
                    return cycle_path[idx:]

            rec_stack.remove(node)
            cycle_path.pop()
            return None

        for node in remaining:
            if node not in visited:
                result = dfs(node)
                if result is not None:
                    return result

        return list(remaining)[:1] if remaining else []

    def get_ready_tasks(
        self,
        graph: RoadmapDependencyGraph,
        completed_task_ids: set[UUID],
    ) -> list[UUID]:
        """Get tasks that are ready to execute given completed tasks.

        Args:
            graph: The dependency graph.
            completed_task_ids: Set of completed task IDs.

        Returns:
            List of task IDs that have all prerequisites met.
        """
        self._update_graph_state(graph, completed_task_ids)
        return graph.ready_task_ids.copy()

    def get_blocked_tasks(
        self,
        graph: RoadmapDependencyGraph,
        completed_task_ids: set[UUID],
    ) -> list[UUID]:
        """Get tasks that are blocked by incomplete prerequisites.

        Args:
            graph: The dependency graph.
            completed_task_ids: Set of completed task IDs.

        Returns:
            List of blocked task IDs.
        """
        self._update_graph_state(graph, completed_task_ids)
        return graph.blocked_task_ids.copy()

    def validate_transition(
        self,
        task_id: UUID,
        current_status: str,
        new_status: str,
        graph: RoadmapDependencyGraph,
        completed_task_ids: set[UUID],
    ) -> None:
        """Validate a task status transition.

        Args:
            task_id: The task ID.
            current_status: Current task status.
            new_status: Requested new status.
            graph: The dependency graph.
            completed_task_ids: Set of completed task IDs.

        Raises:
            DependencyResolutionError: If transition is invalid.
        """
        valid_transitions = {
            "pending": {"in_progress", "blocked", "cancelled"},
            "in_progress": {"completed", "blocked", "needs_confirmation", "cancelled"},
            "blocked": {"pending", "cancelled"},
            "needs_confirmation": {"completed", "pending", "cancelled"},
            "completed": {"skipped"},  # Can mark completed as skipped
            "skipped": set(),  # Terminal
            "cancelled": set(),  # Terminal
        }

        if new_status not in valid_transitions.get(current_status, set()):
            raise DependencyResolutionError(
                f"Invalid transition from {current_status} to {new_status}",
                task_id=task_id,
            )

        # Additional check: cannot complete a task if prerequisites aren't met
        if new_status == "completed":
            ready_tasks = self.get_ready_tasks(graph, completed_task_ids)
            if task_id not in ready_tasks and task_id not in completed_task_ids:
                raise DependencyResolutionError(
                    f"Cannot complete task {task_id}: prerequisites not met",
                    task_id=task_id,
                )
