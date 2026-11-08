"""Validation utilities for document intelligence.

Validates extraction provider payloads, field formats, and business rules.
"""

import re
from typing import Any

from app.services.document_intelligence.document_errors import (
    ExtractionValidationError,
)
from app.services.document_intelligence.schemas import (
    DocumentCategory,
    DocumentExtractionResult,
    ExtractedField,
    ExtractionProviderPayload,
    FieldType,
)

# Validation patterns
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
UDYAM_PATTERN = re.compile(r"^UDYAM-[A-Z]{2}-\d{2}-\d{7}$")
PINCODE_PATTERN = re.compile(r"^[0-9]{6}$")


class ExtractionValidator:
    """Validates extraction provider payloads and results."""

    REQUIRED_PAYLOAD_FIELDS = [
        "request_id",
        "document_id",
        "result",
    ]

    REQUIRED_RESULT_FIELDS = [
        "document_id",
        "user_id",
        "document_category",
        "filename",
        "mime_type",
        "extraction_status",
        "provider",
        "provider_version",
    ]

    SUPPORTED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/tiff",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def validate_payload(self, payload: ExtractionProviderPayload) -> list[str]:
        """Validate an extraction provider payload.

        Args:
            payload: The payload to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Check required top-level fields
        for field in self.REQUIRED_PAYLOAD_FIELDS:
            if not hasattr(payload, field) or getattr(payload, field) is None:
                errors.append(f"Missing required field: {field}")

        # Validate result if present
        if payload.result:
            errors.extend(self.validate_result(payload.result))

        return errors

    def validate_result(self, result: DocumentExtractionResult) -> list[str]:
        """Validate an extraction result.

        Args:
            result: The extraction result to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_RESULT_FIELDS:
            if not hasattr(result, field) or getattr(result, field) is None:
                errors.append(f"Missing required result field: {field}")

        # Validate document_id matches
        if hasattr(result, "document_id") and result.document_id:
            # This would be validated against the payload document_id at API level
            pass

        # Validate MIME type
        if result.mime_type not in self.SUPPORTED_MIME_TYPES:
            errors.append(
                f"Unsupported MIME type: {result.mime_type}. "
                f"Supported: {', '.join(self.SUPPORTED_MIME_TYPES)}"
            )

        # Validate document category
        if result.document_category not in DocumentCategory:
            errors.append(f"Invalid document category: {result.document_category}")

        # Validate extraction status
        if result.extraction_status not in [
            "received",
            "extraction_pending",
            "extracted",
            "validation_pending",
            "verified",
            "rejected",
            "needs_review",
            "failed",
        ]:
            errors.append(f"Invalid extraction status: {result.extraction_status}")

        # Validate provider info
        if not result.provider or len(result.provider) < 1:
            errors.append("Provider name is required")
        if not result.provider_version or len(result.provider_version) < 1:
            errors.append("Provider version is required")

        # Validate extracted fields
        if result.extracted_fields:
            for i, extracted_field in enumerate(result.extracted_fields):
                errors.extend(self.validate_field(extracted_field, i))

        return errors

    def validate_field(self, field: ExtractedField, index: int) -> list[str]:
        """Validate a single extracted field.

        Args:
            field: The extracted field to validate.
            index: Field index for error reporting.

        Returns:
            List of validation error messages.
        """
        errors = []

        # Validate field type
        if field.field_type not in FieldType:
            errors.append(f"Field {index}: Invalid field type: {field.field_type}")
            return errors

        # Validate raw value exists
        if not field.raw_value or not field.raw_value.strip():
            errors.append(f"Field {index} ({field.field_type}): Raw value is empty")

        # Validate confidence if provided
        if field.confidence is not None:
            if not 0.0 <= field.confidence <= 1.0:
                errors.append(
                    f"Field {index} ({field.field_type}): "
                    f"Confidence must be between 0.0 and 1.0"
                )

        # Validate format for known identifier types
        if field.field_type == FieldType.PAN and field.raw_value:
            if not PAN_PATTERN.match(field.raw_value.replace(" ", "").upper()):
                errors.append(
                    f"Field {index} (PAN): Invalid PAN format: {field.raw_value}"
                )

        if field.field_type == FieldType.GSTIN and field.raw_value:
            if not GSTIN_PATTERN.match(field.raw_value.replace(" ", "").upper()):
                errors.append(
                    f"Field {index} (GSTIN): Invalid GSTIN format: {field.raw_value}"
                )

        if field.field_type == FieldType.UDYAM_NUMBER and field.raw_value:
            if not UDYAM_PATTERN.match(field.raw_value.replace(" ", "").upper()):
                errors.append(
                    f"Field {index} (UDYAM): Invalid Udyam format: {field.raw_value}"
                )

        if field.field_type == FieldType.PINCODE and field.raw_value:
            if not PINCODE_PATTERN.match(field.raw_value.replace(" ", "")):
                errors.append(
                    f"Field {index} (PINCODE): Invalid pincode format: {field.raw_value}"
                )

        return errors

    def validate_category_fields(
        self, result: DocumentExtractionResult
    ) -> list[str]:
        """Validate that extracted fields match document category expectations.

        Args:
            result: The extraction result.

        Returns:
            List of validation warnings (not errors).
        """
        warnings = []

        category_expected_fields = {
            DocumentCategory.PAN: {FieldType.PAN},
            DocumentCategory.AADHAAR: {FieldType.PAN},  # Aadhaar often has PAN
            DocumentCategory.GST: {FieldType.GSTIN, FieldType.PAN},
            DocumentCategory.UDYAM: {FieldType.UDYAM_NUMBER, FieldType.PAN},
            DocumentCategory.BUSINESS_REGISTRATION: {
                FieldType.BUSINESS_NAME,
                FieldType.PAN,
            },
            DocumentCategory.ADDRESS_PROOF: {
                FieldType.BUSINESS_ADDRESS,
                FieldType.PINCODE,
                FieldType.STATE,
                FieldType.CITY,
            },
        }

        expected = category_expected_fields.get(result.document_category, set())
        found = {f.field_type for f in result.extracted_fields}

        missing_expected = expected - found
        if missing_expected:
            warnings.append(
                f"Document category {result.document_category.value} "
                f"typically contains: {', '.join(f.value for f in missing_expected)}"
            )

        return warnings


def validate_extraction_payload(payload: dict[str, Any]) -> ExtractionProviderPayload:
    """Validate and parse a raw extraction payload.

    Args:
        payload: Raw payload dictionary.

    Returns:
        Validated ExtractionProviderPayload.

    Raises:
        ExtractionValidationError: If payload is invalid.
    """
    try:
        validated = ExtractionProviderPayload.model_validate(payload)
    except Exception as e:
        raise ExtractionValidationError(
            f"Payload validation failed: {e}",
            context={"raw_payload": str(payload)[:500]},
        ) from e

    # Additional validation
    validator = ExtractionValidator()
    errors = validator.validate_payload(validated)
    if errors:
        raise ExtractionValidationError(
            f"Payload validation failed: {'; '.join(errors)}",
            context={"errors": errors},
        )

    return validated


def validate_document_category(category: str) -> DocumentCategory:
    """Validate and parse document category string.

    Args:
        category: Category string.

    Returns:
        DocumentCategory enum.

    Raises:
        ExtractionValidationError: If category is invalid.
    """
    try:
        return DocumentCategory(category.lower())
    except ValueError as err:
        raise ExtractionValidationError(
            f"Invalid document category: {category}. "
            f"Supported: {[c.value for c in DocumentCategory]}",
            field="document_category",
        ) from err
