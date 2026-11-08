"""Orchestrator pipeline stages.

Defines the sequential processing stages for incoming user messages.
Each stage is a focused, testable unit that operates on a shared
pipeline context.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.schemas.agents import AgentResult
from app.schemas.entities import ExtractedEntity
from app.schemas.intent import IntentDetectionResult
from app.schemas.orchestrator import ResponseType

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """Shared state across pipeline stages.

    Attributes:
        user_id: Authenticated user ID.
        conversation_id: Existing or newly created conversation ID.
        business_profile_id: Optional associated business profile ID.
        message: Raw user message text.
        idempotency_key: Optional idempotency key.
        request_id: Unique request ID for tracing.
        started_at: Pipeline start timestamp.
        conversation: Retrieved or created Conversation ORM object.
        user_message: Persisted user Message ORM object.
        context_dict: Conversation context from ContextManager.
        clarification_state: Pending clarification info, if any.
        intent_result: Intent classification result.
        entities: Extracted entity list.
        response_type: Final response type enum.
        assistant_response_text: Generated assistant response.
        assistant_message: Persisted assistant Message ORM object.
        warnings: Non-fatal warnings collected during processing.
        errors: Fatal errors that abort the pipeline.
        ai_model: AI model name used.
        token_usage: Token usage info, if available.
    """

    user_id: UUID
    conversation_id: UUID | None = None
    business_profile_id: UUID | None = None
    message: str = ""
    idempotency_key: str | None = None
    request_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    conversation: Any = None
    user_message: Any = None
    context_dict: dict[str, object] = field(default_factory=dict)
    clarification_state: dict[str, object] | None = None
    intent_result: IntentDetectionResult | None = None
    entities: list[ExtractedEntity] = field(default_factory=list)
    agent_result: AgentResult | None = None

    response_type: ResponseType = ResponseType.GENERAL_GUIDANCE
    assistant_response_text: str = ""
    assistant_message: Any = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    ai_model: str | None = None
    token_usage: dict[str, object] | None = None

    @property
    def elapsed_ms(self) -> float:
        """Return elapsed milliseconds since pipeline start."""
        return (datetime.now(UTC) - self.started_at).total_seconds() * 1000

    @property
    def has_fatal_error(self) -> bool:
        """Return True if any fatal error was recorded."""
        return len(self.errors) > 0


@dataclass
class PipelineResult:
    """Final result of pipeline execution."""

    context: PipelineContext
    success: bool
    response_type: ResponseType
    assistant_response: str
    intent: IntentDetectionResult | None
    entities: list[ExtractedEntity]
    clarification_required: bool
    clarification_question: str | None
    warnings: list[str]
    conversation_status: str
    user_message_id: UUID | None
    assistant_message_id: UUID | None
    model_name: str | None
    error_message: str | None = None


class PipelineStage:
    """Base class for pipeline stages.

    Each stage implements an async `run` method that receives and
    mutates the PipelineContext. Stages should not raise exceptions
    for recoverable failures; instead they record warnings or errors
    on the context.
    """

    name: str = "base"

    async def run(self, ctx: PipelineContext) -> None:
        """Execute the stage against the pipeline context."""
        raise NotImplementedError


class StageTimer:
    """Context manager for timing and logging pipeline stages."""

    def __init__(self, stage_name: str, ctx: PipelineContext) -> None:
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
                "conversation_id": str(self.ctx.conversation_id)
                if self.ctx.conversation_id
                else None,
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
                    "elapsed_ms": round(elapsed, 2),
                },
            )
