"""Document Intelligence extraction provider contract schemas.

Defines the typed contract for receiving extracted document information
from an external extraction component. All payloads from extraction
providers must conform to these schemas.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentCategory(StrEnum):
    """Supported document categories for classification."""

    PAN = "pan"
    AADHAAR = "aadhaar"
    BUSINESS_REGISTRATION = "business_registration"
    GST = "gst"
    UDYAM = "udyam"
    BANK = "bank"
    ADDRESS_PROOF = "address_proof"
    BUSINESS_OWNERSHIP = "business_ownership"
    OTHER = "other"


class ExtractionStatus(StrEnum):
    """Status of the extraction process."""

    RECEIVED = "received"
    EXTRACTION_PENDING = "extraction_pending"
    EXTRACTED = "extracted"
    VALIDATION_PENDING = "validation_pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class FieldType(StrEnum):
    """Supported field types for normalization."""

    BUSINESS_NAME = "business_name"
    LEGAL_NAME = "legal_name"
    PAN = "pan"
    GSTIN = "gstin"
    UDYAM_NUMBER = "udyam_number"
    BUSINESS_ADDRESS = "business_address"
    PINCODE = "pincode"
    STATE = "state"
    CITY = "city"
    ESTABLISHMENT_DATE = "establishment_date"
    BUSINESS_ACTIVITY = "business_activity"
    OWNERSHIP_DETAILS = "ownership_details"
    UNKNOWN = "unknown"


class DocumentVerificationStatus(StrEnum):
    """Verification status of a document."""

    UNVERIFIED = "unverified"
    USER_CONFIRMED = "user_confirmed"
    DOCUMENT_VERIFIED = "document_verified"
    REJECTED = "rejected"


class ExtractedField(BaseModel):
    """A single extracted field from a document."""

    field_type: FieldType = Field(..., description="Normalized field type identifier.")
    raw_value: str = Field(..., description="Original extracted value from document.")
    normalized_value: str | None = Field(
        None, description="Normalized value after validation/formatting."
    )
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Extraction confidence score if provided."
    )
    page_reference: int | None = Field(
        None, description="Page number where field was found."
    )
    location: dict[str, Any] | None = Field(
        None, description="Bounding box or location coordinates."
    )
    verification_status: DocumentVerificationStatus = Field(
        default=DocumentVerificationStatus.UNVERIFIED,
        description="Verification status of this field.",
    )
    format_valid: bool | None = Field(
        None, description="Whether the raw value passes format validation."
    )


class DocumentExtractionResult(BaseModel):
    """Complete extraction result from an external provider.

    This is the main contract that extraction providers must fulfill.
    All fields are required unless explicitly optional.
    """

    document_id: UUID = Field(..., description="Unique document identifier.")
    user_id: UUID = Field(..., description="User who owns the document.")
    business_profile_id: UUID | None = Field(
        None, description="Associated business profile if applicable."
    )
    document_category: DocumentCategory = Field(
        ..., description="Classification of the document type."
    )
    filename: str = Field(..., min_length=1, max_length=500, description="Original filename.")
    mime_type: str = Field(..., min_length=1, max_length=100, description="MIME type of document.")
    extraction_status: ExtractionStatus = Field(
        default=ExtractionStatus.EXTRACTED,
        description="Current status of extraction processing.",
    )
    extracted_fields: list[ExtractedField] = Field(
        default_factory=list, description="All fields extracted from document."
    )
    page_count: int | None = Field(None, description="Total pages in document.")
    provider: str = Field(
        ..., min_length=1, max_length=100, description="Extraction provider identifier."
    )
    provider_version: str = Field(
        ..., min_length=1, max_length=50, description="Provider software version."
    )
    extraction_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When extraction was completed.",
    )
    source_document_reference: str | None = Field(
        None, description="Reference to original document storage location."
    )
    raw_response: dict[str, Any] | None = Field(
        None, description="Full raw provider response for audit."
    )

    def get_field(self, field_type: FieldType) -> ExtractedField | None:
        """Get a specific extracted field by type."""
        for field in self.extracted_fields:
            if field.field_type == field_type:
                return field
        return None

    def get_fields_by_type(self, field_type: FieldType) -> list[ExtractedField]:
        """Get all extracted fields of a specific type."""
        return [f for f in self.extracted_fields if f.field_type == field_type]


class ExtractionProviderPayload(BaseModel):
    """Payload received from extraction provider webhook/API.

    Wraps the extraction result with metadata for traceability.
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique request correlation ID.",
    )
    document_id: UUID = Field(..., description="Document identifier.")
    result: DocumentExtractionResult = Field(..., description="Extraction result payload.")
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this payload was received by the API.",
    )


class NormalizedField(BaseModel):
    """A normalized field ready for business profile integration."""

    field_type: FieldType
    value: str
    confidence: float | None
    provenance: str
    source_document_id: UUID
    source_field_raw_value: str
    format_valid: bool
    verified: bool = False


class FieldConflict(BaseModel):
    """Represents a conflict between existing profile and extracted data."""

    field_type: FieldType
    existing_value: str | None
    extracted_value: str
    normalized_value: str
    confidence: float | None
    conflict_reason: str
    source_document_id: UUID
    severity: str = "medium"
