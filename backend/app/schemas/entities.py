"""Shared entity data models.

Defines Pydantic models for extracted entities used across
intent detection, entity extraction, and AI service schemas.
"""

from pydantic import BaseModel, Field

from app.schemas.intent_enums import EntityType


class ExtractedEntity(BaseModel):
    """A single extracted entity with metadata.

    Attributes:
        entity_type: The type of entity extracted.
        value: The extracted value.
        confidence: Confidence score between 0.0 and 1.0.
        source: Source of the entity ('user_message' or 'business_profile').
        needs_clarification: Whether this entity needs clarification.
    """

    entity_type: EntityType = Field(..., description="Type of entity extracted")
    value: str = Field(..., description="Extracted entity value")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score",
    )
    source: str = Field(
        ...,
        description="Source of entity: 'user_message' or 'business_profile'",
    )
    needs_clarification: bool = Field(
        default=False,
        description="Whether this entity needs clarification",
    )
