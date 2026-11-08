"""Roadmap schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoadmapBase(BaseModel):
    """Base roadmap schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    status: str = Field(
        default="draft",
        pattern="^(draft|active|completed|archived)$",
    )
    progress_percentage: int = Field(default=0, ge=0, le=100)


class RoadmapCreate(RoadmapBase):
    """Schema for creating a roadmap."""
    user_id: UUID
    business_profile_id: UUID


class RoadmapUpdate(BaseModel):
    """Schema for updating a roadmap."""
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=1)
    status: str | None = Field(
        None,
        pattern="^(draft|active|completed|archived)$",
    )
    progress_percentage: int | None = Field(None, ge=0, le=100)


class RoadmapResponse(RoadmapBase):
    """Schema for roadmap response."""
    id: UUID
    user_id: UUID
    business_profile_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
