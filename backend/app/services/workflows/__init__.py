"""Workflow engine package for SarkarSetu AI.

Provides deterministic, auditable workflow execution for government
service journeys (Udyam registration, GST registration, MSME scheme
discovery). Agents coordinate through this engine to deliver complete,
step-by-step conversational workflows.

Components:
- WorkflowEngine - Core engine that executes workflow steps
- WorkflowRegistry - Registers and resolves workflows by service type
- BaseWorkflow - Abstract base class for service-specific workflows
- WorkflowContext - Shared state during execution
- WorkflowStateManager - Persists/loads workflow state to database
- StepExecutor - Executes individual workflow steps
- WorkflowResult - Typed result of workflow execution
- WorkflowError / WorkflowErrorCategory - Error handling
"""

from app.services.workflows.base import BaseWorkflow
from app.services.workflows.context import WorkflowContext
from app.services.workflows.engine import WorkflowEngine
from app.services.workflows.registry import WorkflowRegistry
from app.services.workflows.state_manager import WorkflowStateManager
from app.services.workflows.step_executor import StepExecutor
from app.services.workflows.workflow_errors import WorkflowError, WorkflowErrorCategory
from app.services.workflows.workflow_result import WorkflowResult

__all__ = [
    "WorkflowEngine",
    "WorkflowRegistry",
    "BaseWorkflow",
    "WorkflowContext",
    "WorkflowStateManager",
    "StepExecutor",
    "WorkflowResult",
    "WorkflowError",
    "WorkflowErrorCategory",
]
