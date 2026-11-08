"""Workflow pipeline stages for SarkarSetu AI workflow engine.

Defines the sequential processing stages for incoming workflow
execution. Each stage is a focused, testable unit that operates on
a shared pipeline context.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class WorkflowPipelineContext:
    """Shared state across workflow pipeline stages.

    Attributes:
        workflow_id: Unique workflow execution ID.
        user_id: Authenticated user ID.
        conversation_id: Conversation ID.
        business_profile_id: Optional associated business profile ID.
        service_type: Service type identifier.
        message: Raw user message text.
        primary_intent: Primary intent classification result.
        secondary_intents: Secondary intent classification results.
        extracted_entities: Extracted entities from the user message.
        conversation_history: Recent conversation history for context.
        clarification_state: Pending clarification state, if any.
        retrieved_evidence: Retrieved government document evidence.
        request_id: Unique request correlation ID for tracing.
        started_at: Pipeline start timestamp.
        step_results: Results from executed workflow steps.
        overall_status: Overall workflow status.
        response: User-facing response text.
        structured_data: Structured data produced by the workflow.
        missing_information: Information needed from the user.
        clarification_question: Clarification question to ask, if required.
        warnings: Non-fatal warnings collected during processing.
        evidence_references: Source references for claims made.
        next_actions: Actionable next steps for the user.
        errors: Fatal errors that abort the pipeline.
    """

    user_id: UUID
    conversation_id: UUID
    workflow_id: UUID = field(default_factory=lambda: uuid4())
    business_profile_id: UUID | None = None
    service_type: str = ""
    message: str = ""
    primary_intent: str | None = None
    secondary_intents: list[str] = field(default_factory=list)
    extracted_entities: list[dict[str, Any]] = field(default_factory=list)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    clarification_state: dict[str, Any] | None = None
    retrieved_evidence: list[dict[str, Any]] = field(default_factory=list)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    step_results: list[dict[str, Any]] = field(default_factory=list)
    overall_status: str = ""
    response: str = ""
    structured_data: dict[str, Any] = field(default_factory=dict)
    missing_information: list[str] = field(default_factory=list)
    clarification_question: str | None = None
    warnings: list[str] = field(default_factory=list)
    evidence_references: list[dict[str, Any]] = field(default_factory=list)
    next_actions: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def elapsed_ms(self) -> float:
        """Return elapsed milliseconds since pipeline start."""
        return (datetime.now(UTC) - self.started_at).total_seconds() * 1000

    @property
    def has_fatal_error(self) -> bool:
        """Return True if any fatal error was recorded."""
        return len(self.errors) > 0


class WorkflowPipelineStage:
    """Base class for workflow pipeline stages.

    Each stage implements an async `run` method that receives and
    mutates the WorkflowPipelineContext. Stages should not raise
    exceptions for recoverable failures; instead they record warnings
    or errors on the context.
    """

    name: str = "base"

    async def run(self, ctx: WorkflowPipelineContext) -> None:
        """Execute the stage against the pipeline context."""
        raise NotImplementedError


class StageTimer:
    """Context manager for timing and logging pipeline stages."""

    def __init__(self, stage_name: str, ctx: WorkflowPipelineContext) -> None:
        self.stage_name = stage_name
        self.ctx = ctx
        self.start: float | None = None

    async def __aenter__(self) -> "StageTimer":
        self.start = time.perf_counter()
        logger.info(
            "Pipeline stage started",
            extra={
                "request_id": self.ctx.request_id,
                "stage": self.stage_name,
                "workflow_id": str(self.ctx.workflow_id),
                "user_id": str(self.ctx.user_id),
            },
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        elapsed = (time.perf_counter() - (self.start or 0)) * 1000
        if exc_type is not None:
            self.ctx.errors.append(f"{self.stage_name}: {exc_val}")
            logger.error(
                "Pipeline stage failed",
                extra={
                    "request_id": self.ctx.request_id,
                    "stage": self.stage_name,
                    "workflow_id": str(self.ctx.workflow_id),
                    "error": str(exc_val),
                    "elapsed_ms": elapsed,
                },
            )
        else:
            logger.info(
                "Pipeline stage completed",
                extra={
                    "request_id": self.ctx.request_id,
                    "stage": self.stage_name,
                    "workflow_id": str(self.ctx.workflow_id),
                    "elapsed_ms": round(elapsed, 2),
                },
            )


# Import datetime after class definitions to avoid circular import
from datetime import datetime  # noqa: E402
