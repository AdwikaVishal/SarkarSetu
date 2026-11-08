"""UploadedDocument schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UploadedDocumentBase(BaseModel):
    """Base uploaded document schema."""
    original_filename: str = Field(..., min_length=1, max_length=500)
    storage_key: str = Field(..., min_length=1, max_length=500)
    content_type: str = Field(..., min_length=1, max_length=100)
    file_size: int = Field(..., gt=0)
    processing_status: str = Field(
        default="pending",
        pattern="^(pending|processing|completed|failed)$",
    )
    document_type: str | None = Field(None, max_length=100)
    extracted_data: dict | None = None


class UploadedDocumentCreate(UploadedDocumentBase):
    """Schema for creating an uploaded document record."""
    user_id: UUID
    business_profile_id: UUID | None = None


class UploadedDocumentUpdate(BaseModel):
    """Schema for updating an uploaded document record."""
    original_filename: str | None = Field(None, min_length=1, max_length=500)
    processing_status: str | None = Field(
        None,
        pattern="^(pending|processing|completed|failed)$",
    )
    document_type: str | None = Field(None, max_length=100)
    extracted_data: dict | None = None


class UploadedDocumentResponse(UploadedDocumentBase):
    """Schema for uploaded document response."""
    id: UUID
    user_id: UUID
    business_profile_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
