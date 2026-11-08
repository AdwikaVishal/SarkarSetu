"""RoadmapTask schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoadmapTaskBase(BaseModel):
    """Base roadmap task schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    sequence_number: int = Field(..., ge=0)
    status: str = Field(
        default="pending",
        pattern="^(pending|in_progress|completed|blocked)$",
    )
    priority: str = Field(
        default="medium",
        pattern="^(low|medium|high|critical)$",
    )
    due_date: datetime | None = None
    official_portal_url: str | None = Field(None, max_length=1000)
    required_documents: list[str] | None = None
    source_references: list[str] | None = None


class RoadmapTaskCreate(RoadmapTaskBase):
    """Schema for creating a roadmap task."""
    roadmap_id: UUID


class RoadmapTaskUpdate(BaseModel):
    """Schema for updating a roadmap task."""
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, min_length=1)
    sequence_number: int | None = Field(None, ge=0)
    status: str | None = Field(
        None,
        pattern="^(pending|in_progress|completed|blocked)$",
    )
    priority: str | None = Field(
        None,
        pattern="^(low|medium|high|critical)$",
    )
    due_date: datetime | None = None
    official_portal_url: str | None = Field(None, max_length=1000)
    required_documents: list[str] | None = None
    source_references: list[str] | None = None
    completed_at: datetime | None = None


class RoadmapTaskResponse(RoadmapTaskBase):
    """Schema for roadmap task response."""
    id: UUID
    roadmap_id: UUID
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
