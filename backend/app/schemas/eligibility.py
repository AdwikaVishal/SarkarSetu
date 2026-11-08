"""EligibilityResult schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EligibilityResultBase(BaseModel):
    """Base eligibility result schema."""
    rule_set_version: str = Field(..., min_length=1, max_length=50)
    assessment_status: str = Field(..., min_length=1, max_length=50)
    result_data: dict
    missing_information: dict = Field(default_factory=dict)


class EligibilityResultCreate(EligibilityResultBase):
    """Schema for creating an eligibility result."""
    user_id: UUID
    business_profile_id: UUID
    recommendation_id: UUID | None = None


class EligibilityResultUpdate(BaseModel):
    """Schema for updating an eligibility result."""
    rule_set_version: str | None = Field(None, min_length=1, max_length=50)
    assessment_status: str | None = Field(None, min_length=1, max_length=50)
    result_data: dict | None = None
    missing_information: dict | None = None


class EligibilityResultResponse(EligibilityResultBase):
    """Schema for eligibility result response."""
    id: UUID
    user_id: UUID
    business_profile_id: UUID | None
    recommendation_id: UUID | None
    evaluated_at: datetime

    model_config = {"from_attributes": True}
