"""Intent detection and entity extraction schemas.

Defines Pydantic models for intent classification, entity extraction,
and combined analysis requests and responses.
"""


from pydantic import BaseModel, Field

from app.schemas.entities import ExtractedEntity
from app.schemas.intent_enums import (
    ConfidenceLevel,
    Intent,
    LanguageCode,
    RiskFlag,
    UrgencyLevel,
)


class IntentDetectionResult(BaseModel):
    """Result of intent classification.

    Attributes:
        primary_intent: The primary intent detected.
        secondary_intents: Secondary intents detected, if any.
        confidence: Confidence score between 0.0 and 1.0.
        confidence_level: Derived confidence level (high/medium/low).
        requires_clarification: Whether clarification is needed.
        clarification_question: Question to ask user if clarification needed.
        reasoning_summary: Non-sensitive explanation of classification.
        detected_language: Language detected in the message.
        is_follow_up: Whether this is a follow-up to a previous message.
        referenced_entity: Optional entity reference.
        urgency: Urgency level of the request.
        risk_flags: Risk flags identified.
        taxonomy_version: Version of the intent taxonomy used.
    """

    primary_intent: Intent = Field(..., description="Primary intent detected")
    secondary_intents: list[Intent] = Field(
        default_factory=list,
        description="Secondary intents detected",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    confidence_level: ConfidenceLevel = Field(
        ..., description="Confidence level (high/medium/low)"
    )
    requires_clarification: bool = Field(
        default=False,
        description="Whether clarification is needed",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask user if clarification needed",
    )
    reasoning_summary: str = Field(
        ...,
        description="Non-sensitive explanation of classification",
    )
    detected_language: LanguageCode = Field(
        ..., description="Language detected in the message"
    )
    is_follow_up: bool = Field(
        default=False,
        description="Whether this is a follow-up to a previous message",
    )
    referenced_entity: str | None = Field(
        default=None,
        description="Optional entity reference",
    )
    urgency: UrgencyLevel = Field(
        default=UrgencyLevel.NORMAL,
        description="Urgency level of the request",
    )
    risk_flags: list[RiskFlag] = Field(
        default_factory=list,
        description="Risk flags identified",
    )
    taxonomy_version: str = Field(
        default="1.0.0",
        description="Version of the intent taxonomy used",
    )


class IntentClassificationRequest(BaseModel):
    """Request schema for intent classification."""

    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID for context",
    )
    business_profile_id: str | None = Field(
        default=None,
        description="Optional business profile ID for context",
    )
    include_history: bool = Field(
        default=False,
        description="Whether to include conversation history",
    )


class IntentClassificationResponse(BaseModel):
    """Response schema for intent classification."""

    intent_detection: IntentDetectionResult = Field(
        ..., description="Intent detection result"
    )


class EntityExtractionRequest(BaseModel):
    """Request schema for entity extraction."""

    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID for context",
    )
    business_profile_id: str | None = Field(
        default=None,
        description="Optional business profile ID for context",
    )
    include_history: bool = Field(
        default=False,
        description="Whether to include conversation history",
    )


class EntityExtractionResponse(BaseModel):
    """Response schema for entity extraction."""

    entities: list[ExtractedEntity] = Field(
        default_factory=list,
        description="Extracted entities",
    )
    detected_language: LanguageCode = Field(
        ..., description="Language detected in the message"
    )


class IntentAnalysisRequest(BaseModel):
    """Request schema for combined intent and entity analysis."""

    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID for context",
    )
    business_profile_id: str | None = Field(
        default=None,
        description="Optional business profile ID for context",
    )
    include_history: bool = Field(
        default=False,
        description="Whether to include conversation history",
    )


class IntentAnalysisResponse(BaseModel):
    """Response schema for combined intent and entity analysis."""

    intent: IntentDetectionResult = Field(..., description="Intent detection result")
    entities: list[ExtractedEntity] = Field(
        default_factory=list,
        description="Extracted entities",
    )
    requires_clarification: bool = Field(
        default=False,
        description="Whether clarification is needed",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask user if clarification needed",
    )
    summary: str = Field(
        ..., description="Summary of intent and entities"
    )
