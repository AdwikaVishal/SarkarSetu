"""Workflow context for SarkarSetu AI workflow engine.

Shared state passed between workflow steps during execution.
Contains all information needed for workflow processing without
exposing authentication tokens, password hashes, refresh tokens,
or unnecessary sensitive identifiers.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DataProvenance(str, Enum):
    """Provenance of input data used in workflow evaluation."""

    BUSINESS_PROFILE = "BUSINESS_PROFILE"
    USER_CONFIRMED = "USER_CONFIRMED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    UNKNOWN = "UNKNOWN"


class WorkflowContext(BaseModel):
    """Shared context passed to every workflow step.

    Contains all information needed for workflow execution without
    exposing authentication tokens, password hashes, refresh tokens,
    or unnecessary sensitive identifiers.
    """

    workflow_id: UUID = Field(..., description="Unique workflow execution ID.")
    user_id: UUID = Field(..., description="Authenticated user ID.")
    conversation_id: UUID = Field(..., description="Conversation ID.")
    business_profile_id: UUID | None = Field(
        default=None,
        description="Optional associated business profile ID.",
    )
    service_type: str = Field(
        ...,
        description="Service type identifier (e.g., 'udyam_registration', 'gst_registration', 'msme_schemes').",
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
    retrieved_evidence: list[dict[str, Any]] = Field(
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
        if not self.service_type:
            errors.append("Service type is required")
        return errors
