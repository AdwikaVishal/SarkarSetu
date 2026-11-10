"""Recommendation schemas."""
from datetime import datetime
from typing import Any
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


# --- New API Schemas ---

class SchemeDetail(BaseModel):
    """Scheme metadata."""
    id: str
    name: str
    full_name: str
    category: str
    ministry: str
    description: str
    official_url: str


class RecommendationDetail(BaseModel):
    """Detailed recommendation for a scheme."""
    scheme: SchemeDetail
    eligibility_status: str
    explanation: str
    required_documents: list[str]
    missing_information: list[str]
    official_sources: list[dict[str, str]]
    matched_rules: list[str]
    failed_rules: list[str]


class RecommendationRequest(BaseModel):
    """Request for personalized recommendations."""
    business_profile_id: UUID
    service_filter: str | None = None


class RecommendationResponse(BaseModel):
    """Response with personalized recommendations."""
    business_profile_id: UUID
    total_schemes_evaluated: int
    eligible_count: int
    potentially_eligible_count: int
    needs_info_count: int
    ineligible_count: int
    recommendations: list[RecommendationDetail]
    missing_information: list[str]


class RecommendationListResponse(BaseModel):
    """Response for listing cached recommendations."""
    items: list[RecommendationResponse]
    total: int
