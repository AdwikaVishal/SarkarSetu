"""UploadedDocument schemas."""
from datetime import datetime
from typing import Any
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
        pattern="^(pending|processing|completed|failed|error)$",
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


# --- New API Response Schemas ---

class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    document_id: UUID
    filename: str
    status: str
    message: str


class DocumentListResponse(BaseModel):
    """Response for document list."""
    items: list[UploadedDocumentResponse]
    total: int


class DocumentResponse(UploadedDocumentResponse):
    """Extended document response with extraction details."""
    pass


class DocumentMatchingResponse(BaseModel):
    """Response for document matching against requirements."""
    document_id: UUID
    service: str
    overall_status: str
    checklist_coverage: float
    available_documents: list[dict[str, Any]]
    missing_documents: list[dict[str, Any]]
    incomplete_extraction: list[dict[str, Any]]
    needs_review: list[dict[str, Any]]
    review_items: list[dict[str, Any]]


class DocumentDeleteResponse(BaseModel):
    """Response for document deletion."""
    message: str
