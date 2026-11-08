"""Agent schemas for SarkarSetu AI.

Defines AgentContext, AgentResult, status enums, and related data
models used by all specialized agents.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent execution status enum.

    Standardized statuses used across all agents. Arbitrary strings
    are not permitted.
    """

    COMPLETED = "completed"
    NEEDS_INFORMATION = "needs_information"
    NEEDS_RETRIEVAL = "needs_retrieval"
    NEEDS_VERIFICATION = "needs_verification"
    NOT_SUPPORTED = "not_supported"
    FAILED = "failed"


class RetrievalSource(BaseModel):
    """A single source reference from government document retrieval.

    All fields are optional to support graceful degradation when
    retrieval is unavailable or partial.
    """

    document_id: str | None = Field(
        default=None,
        description="Unique identifier of the source document.",
    )
    source_title: str | None = Field(
        default=None,
        description="Title of the source document.",
    )
    issuing_authority: str | None = Field(
        default=None,
        description="Government authority that issued the document.",
    )
    source_url: str | None = Field(
        default=None,
        description="URL where the source document can be accessed.",
    )
    publication_date: str | None = Field(
        default=None,
        description="Publication or effective date of the document, if known.",
    )
    relevant_excerpt: str | None = Field(
        default=None,
        description="Relevant excerpt from the document.",
    )
    page_or_section: str | None = Field(
        default=None,
        description="Page or section reference within the document.",
    )
    retrieval_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Retrieval relevance score.",
    )
    document_version: str | None = Field(
        default=None,
        description="Version of the document, if known.",
    )


class AgentContext(BaseModel):
    """Shared context passed to every agent.

    Contains all information needed for agent execution without
    exposing authentication tokens, password hashes, refresh tokens,
    or unnecessary sensitive identifiers.
    """

    user_id: UUID = Field(..., description="Authenticated user ID.")
    conversation_id: UUID = Field(..., description="Conversation ID.")
    business_profile_id: UUID | None = Field(
        default=None,
        description="Optional associated business profile ID.",
    )
    message: str = Field(..., description="Current user message text.")
    primary_intent: str | None = Field(
        default=None,
        description="Primary intent classification result.",
    )
    secondary_intents: list[str] = Field(
        default_factory=list,
        description="Secondary intent classification results.",
    )
    extracted_entities: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted entities from the user message.",
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Recent conversation history for context.",
    )
    clarification_state: dict[str, Any] | None = Field(
        default=None,
        description="Pending clarification state, if any.",
    )
    retrieved_evidence: list[RetrievalSource] = Field(
        default_factory=list,
        description="Retrieved government document evidence, if available.",
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique request correlation ID for tracing.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the context was created.",
    )

    def validate_context(self) -> list[str]:
        """Validate the context and return a list of error messages.

        Returns:
            List of validation error messages, empty if valid.
        """
        errors: list[str] = []
        if not self.user_id:
            errors.append("Authenticated user ID is required")
        if not self.conversation_id:
            errors.append("Conversation ID is required")
        if not self.message or not self.message.strip():
            errors.append("Message is empty or whitespace-only")
        return errors


class AgentResult(BaseModel):
    """Typed result returned by every agent.

    Contains all information needed to build a user-facing response
    without leaking internal implementation details.
    """

    agent_name: str = Field(..., description="Name of the agent that produced this result.")
    status: AgentStatus = Field(..., description="Execution status enum.")
    response: str = Field(
        ...,
        description="User-facing response text.",
    )
    structured_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data produced by the agent.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of information needed from the user.",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Clarification question to ask the user, if required.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings collected during processing.",
    )
    evidence_references: list[RetrievalSource] = Field(
        default_factory=list,
        description="Source references for any claims made.",
    )
    execution_duration_ms: float = Field(
        default=0.0,
        description="Agent execution duration in milliseconds.",
    )
    handoff_required: bool = Field(
        default=False,
        description="Whether a handoff to another agent or service is required.",
    )
    handoff_target: str | None = Field(
        default=None,
        description="Target agent or service for handoff, if applicable.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the result was created.",
    )
