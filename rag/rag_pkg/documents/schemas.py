"""Pydantic schemas for document intelligence."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    """A single extracted field with confidence and masking support."""

    value: Any | None = Field(
        default=None, description="Extracted value; None when unavailable"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Extraction confidence (0.0 = no confidence)",
    )
    method: str | None = Field(
        default=None, description="Extraction method used"
    )

    def masked_value(self, *, mask: bool = True) -> Any:
        """Return the value, optionally masked if it looks sensitive."""
        if self.value is None:
            return None
        if not mask:
            return self.value
        return mask_sensitive(self.value)


class DocumentClassification(BaseModel):
    """Classification result for an uploaded document."""

    document_type: str = Field(
        ..., description="One of the supported categories or other/unknown"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Classification confidence",
    )
    method: str = Field(
        default="rule_based", description="Classification method used"
    )
    reasons: list[str] = Field(
        default_factory=list, description="Human-readable reasons"
    )


class FieldExtractionResult(BaseModel):
    """Result of extracting fields from a document."""

    document_type: str = Field(
        ..., description="Classified document type"
    )
    extracted_fields: dict[str, ExtractedField] = Field(
        default_factory=dict,
        description="Field name -> ExtractedField",
    )
    extraction_method: str = Field(
        default="pdf_text", description="Extraction method"
    )
    validation_status: str = Field(
        default="needs_review",
        description="needs_review / validated / rejected",
    )
    overall_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
    )


class ProcessDocumentResult(BaseModel):
    """Structured output of process_document."""

    document_id: str = Field(..., description="Unique document identifier")
    document_type: str = Field(
        ..., description="Classified document type"
    )
    classification_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
    )
    classification_method: str = Field(default="rule_based")
    extracted_fields: dict[str, ExtractedField] = Field(default_factory=dict)
    extraction_method: str = Field(default="pdf_text")
    validation_status: str = Field(default="needs_review")
    page_count: int | None = Field(default=None)
    char_count: int | None = Field(default=None)
    extraction_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    masked: bool = Field(
        default=True, description="Whether sensitive values are masked in output"
    )


class MatchResult(BaseModel):
    """Result of matching documents to requirements."""

    service: str
    available_documents: list[dict[str, Any]] = Field(default_factory=list)
    missing_documents: list[dict[str, Any]] = Field(default_factory=list)
    needs_review: list[dict[str, Any]] = Field(default_factory=list)
    incomplete_extraction: list[dict[str, Any]] = Field(default_factory=list)
    inconsistencies: list[dict[str, Any]] = Field(default_factory=list)
    overall_status: str = Field(
        default="incomplete",
        description="complete / incomplete / needs_review",
    )
    checklist_coverage: float = Field(
        default=0.0, ge=0.0, le=1.0,
    )


def mask_sensitive(value: Any) -> Any:
    """Mask sensitive identifiers in ordinary log/demo responses.

    PAN, GSTIN, Aadhaar-like strings are partially masked. Other values
    are returned unchanged.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    text = str(value)
    # PAN-like: ABCDE1234F -> mask first 8, keep last char
    pan_pattern = re_pan()
    if pan_pattern.fullmatch(text):
        return text[:3] + "******" + text[-1:]
    # GSTIN-like 15 chars
    gstin_pattern = re_gstin()
    if gstin_pattern.fullmatch(text):
        return text[:2] + "*********" + text[-2:]
    # Aadhaar-like 12 digits
    aadhaar_pattern = re_aadhaar()
    if aadhaar_pattern.fullmatch(text):
        return "**** **** " + text[-4:]
    # Long numeric strings (account numbers)
    if text.isdigit() and len(text) >= 8:
        return "****" + text[-4:]
    return text


import re  # noqa: E402


def re_pan() -> re.Pattern[str]:
    return re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def re_gstin() -> re.Pattern[str]:
    return re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def re_aadhaar() -> re.Pattern[str]:
    return re.compile(r"^[0-9]{12}$")
