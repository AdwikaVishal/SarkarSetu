"""Recommendation schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationBase(BaseModel):
    """Base recommendation schema."""
    category: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    recommendation_status: str = Field(
        default="pending",
        pattern="^(pending|accepted|rejected|expired)$",
    )
    eligibility_status: str = Field(
        default="unverified",
        pattern="^(eligible|potentially_eligible|ineligible|needs_information|unverified)$",
    )
    explanation: str | None = None
    evidence: dict | None = None


class RecommendationCreate(RecommendationBase):
    """Schema for creating a recommendation."""
    business_profile_id: UUID
    user_id: UUID


class RecommendationUpdate(BaseModel):
    """Schema for updating a recommendation."""
    category: str | None = Field(None, min_length=1, max_length=100)
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=1)
    recommendation_status: str | None = Field(
        None,
        pattern="^(pending|accepted|rejected|expired)$",
    )
    eligibility_status: str | None = Field(
        None,
        pattern="^(eligible|potentially_eligible|ineligible|needs_information|unverified)$",
    )
    explanation: str | None = None
    evidence: dict | None = None


class RecommendationResponse(RecommendationBase):
    """Schema for recommendation response."""
    id: UUID
    business_profile_id: UUID | None
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
