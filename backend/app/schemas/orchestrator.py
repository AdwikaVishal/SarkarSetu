"""Orchestrator schemas.

Defines request and response models for the chat orchestration API,
including centralized response type enumeration.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ResponseType(str, Enum):
    """Centralized response type enum for orchestrator outputs.

    Values are extensible for future specialized agents.
    """

    GREETING = "greeting"
    GENERAL_GUIDANCE = "general_guidance"
    CLARIFICATION = "clarification"
    INTENT_UNCERTAIN = "intent_uncertain"
    WORKFLOW_NOT_AVAILABLE = "workflow_not_available"
    OUT_OF_SCOPE = "out_of_scope"
    ERROR = "error"


class ExtractedEntitySummary(BaseModel):
    """Lightweight summary of an extracted entity for API responses."""

    entity_type: str
    value: str
    confidence: float
    source: str
    needs_clarification: bool


class IntentSummary(BaseModel):
    """Lightweight summary of intent classification for API responses."""

    primary_intent: str
    secondary_intents: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: str
    requires_clarification: bool
    clarification_question: str | None = None


class AssistantResponse(BaseModel):
    """Structured assistant response validated by the AI service."""

    response_text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The assistant's response text.",
    )
    response_type: ResponseType = Field(
        ...,
        description="Type of response generated.",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for the response.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings collected during processing.",
    )


class ChatMessageRequest(BaseModel):
    """Request schema for POST /api/v1/chat/message."""

    conversation_id: UUID | None = Field(
        default=None,
        description="Optional ID of an existing conversation to continue.",
    )
    business_profile_id: UUID | None = Field(
        default=None,
        description="Optional ID of a business profile to associate with the conversation.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message text.",
    )
    idempotency_key: str | None = Field(
        default=None,
        max_length=255,
        description="Optional idempotency key to prevent duplicate processing.",
    )


class ChatMessageResponse(BaseModel):
    """Response schema for POST /api/v1/chat/message."""

    conversation_id: UUID
    user_message_id: UUID
    assistant_message_id: UUID
    assistant_response: str
    intent: IntentSummary
    extracted_entities: list[ExtractedEntitySummary] = Field(default_factory=list)
    clarification_required: bool = False
    clarification_question: str | None = None
    warnings: list[str] = Field(default_factory=list)
    response_type: ResponseType
    conversation_status: str
    ai_model: str | None = None
    provider: str | None = Field(
        default=None,
        description="AI provider used (gemini or local_fallback).",
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether the local fallback provider was used.",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for the response.",
    )
    created_at: datetime


class ConversationStatusResponse(BaseModel):
    """Response schema for GET /api/v1/chat/conversations/{id}/status."""

    conversation_id: UUID
    status: str
    clarification_pending: bool
    clarification_question: str | None = None
    business_profile_id: UUID | None = None
    last_message_at: datetime | None = None


class OrchestratorError(BaseModel):
    """Safe error response without leaking internal exceptions."""

    error: str = Field(..., description="User-safe error message.")
    response_type: ResponseType = ResponseType.ERROR
    details: dict[str, Any] | None = None


class RetrievalSourceResponse(BaseModel):
    """Response schema for a single retrieved knowledge source."""

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


class KnowledgeSearchRequest(BaseModel):
    """Request schema for POST /api/v1/knowledge/search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Search query describing what information is needed.",
    )
    conversation_id: UUID | None = Field(
        default=None,
        description="Optional conversation ID for context.",
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Optional filters (scheme name, department, state, etc.).",
    )
    limit: int | None = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of results to return.",
    )


class KnowledgeSearchResponse(BaseModel):
    """Response schema for POST /api/v1/knowledge/search."""

    query: str = Field(..., description="The search query that was processed.")
    results: list[RetrievalSourceResponse] = Field(
        default_factory=list,
        description="Retrieved knowledge sources with citations.",
    )
    total_count: int = Field(
        default=0,
        description="Number of results returned.",
    )
    provider_enabled: bool = Field(
        default=False,
        description="Whether the knowledge retrieval provider is enabled.",
    )
