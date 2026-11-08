"""Field normalization for document intelligence.

Deterministic normalization of extracted document fields for integration
with business profiles and eligibility engine.
"""

import re
from datetime import datetime
from uuid import UUID

from app.services.document_intelligence.document_errors import NormalizationError
from app.services.document_intelligence.schemas import (
    DocumentExtractionResult,
    DocumentVerificationStatus,
    ExtractedField,
    FieldType,
    NormalizedField,
)

# PAN regex: 5 letters, 4 digits, 1 letter
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")

# GSTIN regex: 2 digits state code + 10 chars PAN + 1 entity + 1 check
GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

# UDYAM regex: UDYAM-<state>-<district>-<number>
UDYAM_PATTERN = re.compile(r"^UDYAM-[A-Z]{2}-\d{2}-\d{7}$")

# PINCODE regex: 6 digits
PINCODE_PATTERN = re.compile(r"^[0-9]{6}$")


def normalize_pan(value: str) -> tuple[str, bool]:
    """Normalize PAN identifier.

    Args:
        value: Raw PAN value.

    Returns:
        Tuple of (normalized_value, format_valid).
    """
    # Remove spaces and make uppercase
    normalized = value.replace(" ", "").upper()
    format_valid = bool(PAN_PATTERN.match(normalized))
    return normalized, format_valid


def normalize_gstin(value: str) -> tuple[str, bool]:
    """Normalize GSTIN identifier.

    Args:
        value: Raw GSTIN value.

    Returns:
        Tuple of (normalized_value, format_valid).
    """
    normalized = value.replace(" ", "").upper()
    format_valid = bool(GSTIN_PATTERN.match(normalized))
    return normalized, format_valid


def normalize_udyam_number(value: str) -> tuple[str, bool]:
    """Normalize Udyam registration number.

    Args:
        value: Raw Udyam number.

    Returns:
        Tuple of (normalized_value, format_valid).
    """
    normalized = value.replace(" ", "").upper()
    format_valid = bool(UDYAM_PATTERN.match(normalized))
    return normalized, format_valid


def normalize_pincode(value: str) -> tuple[str, bool]:
    """Normalize pincode.

    Args:
        value: Raw pincode value.

    Returns:
        Tuple of (normalized_value, format_valid).
    """
    normalized = value.replace(" ", "")
    format_valid = bool(PINCODE_PATTERN.match(normalized))
    return normalized, format_valid


def normalize_business_name(value: str) -> tuple[str, bool]:
    """Normalize business name.

    Args:
        value: Raw business name.

    Returns:
        Tuple of (normalized_value, format_valid). Always format_valid=True.
    """
    # Strip extra whitespace, preserve case
    normalized = " ".join(value.split())
    return normalized, True


def normalize_address(value: str) -> tuple[str, bool]:
    """Normalize address.

    Args:
        value: Raw address.

    Returns:
        Tuple of (normalized_value, format_valid). Always format_valid=True.
    """
    # Strip extra whitespace
    normalized = " ".join(value.split())
    return normalized, True


def normalize_state(value: str) -> tuple[str, bool]:
    """Normalize state name.

    Args:
        value: Raw state value.

    Returns:
        Tuple of (normalized_value, format_valid).
    """
    normalized = " ".join(value.split()).title()
    # Basic validation - non-empty
    format_valid = len(normalized) > 0
    return normalized, format_valid


def normalize_city(value: str) -> tuple[str, bool]:
    """Normalize city name.

    Args:
        value: Raw city value.

    Returns:
        Tuple of (normalized_value, format_valid).
    """
    normalized = " ".join(value.split()).title()
    format_valid = len(normalized) > 0
    return normalized, format_valid


def normalize_establishment_date(value: str) -> tuple[str, bool]:
    """Normalize establishment date to ISO format.

    Args:
        value: Raw date value in various formats.

    Returns:
        Tuple of (normalized_value, format_valid).
    """
    # Try common date formats
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            return dt.date().isoformat(), True
        except ValueError:
            continue

    return value.strip(), False


def normalize_business_activity(value: str) -> tuple[str, bool]:
    """Normalize business activity description.

    Args:
        value: Raw business activity.

    Returns:
        Tuple of (normalized_value, format_valid). Always format_valid=True.
    """
    normalized = " ".join(value.split())
    return normalized, True


def normalize_ownership_details(value: str) -> tuple[str, bool]:
    """Normalize ownership details.

    Args:
        value: Raw ownership details.

    Returns:
        Tuple of (normalized_value, format_valid). Always format_valid=True.
    """
    normalized = " ".join(value.split())
    return normalized, True


# Mapping of field types to normalization functions
NORMALIZERS = {
    FieldType.PAN: normalize_pan,
    FieldType.GSTIN: normalize_gstin,
    FieldType.UDYAM_NUMBER: normalize_udyam_number,
    FieldType.PINCODE: normalize_pincode,
    FieldType.BUSINESS_NAME: normalize_business_name,
    FieldType.LEGAL_NAME: normalize_business_name,
    FieldType.BUSINESS_ADDRESS: normalize_address,
    FieldType.STATE: normalize_state,
    FieldType.CITY: normalize_city,
    FieldType.ESTABLISHMENT_DATE: normalize_establishment_date,
    FieldType.BUSINESS_ACTIVITY: normalize_business_activity,
    FieldType.OWNERSHIP_DETAILS: normalize_ownership_details,
}


def normalize_field(
    field: ExtractedField,
    source_document_id: UUID,
) -> NormalizedField:
    """Normalize a single extracted field.

    Args:
        field: The extracted field to normalize.
        source_document_id: ID of source document for provenance.

    Returns:
        NormalizedField with provenance and verification info.

    Raises:
        NormalizationError: If field type is unknown.
    """
    normalizer = NORMALIZERS.get(field.field_type)

    if normalizer is None:
        # Unknown field type - pass through with warning
        return NormalizedField(
            field_type=field.field_type,
            value=field.raw_value,
            confidence=field.confidence,
            provenance="UNKNOWN",
            source_document_id=source_document_id,
            source_field_raw_value=field.raw_value,
            format_valid=True,
            verified=field.verification_status == DocumentVerificationStatus.DOCUMENT_VERIFIED,
        )

    normalized_value, format_valid = normalizer(field.raw_value)

    # Use normalized value from field if already provided and matches
    if field.normalized_value and field.normalized_value == normalized_value:
        final_value = normalized_value
    else:
        final_value = normalized_value

    return NormalizedField(
        field_type=field.field_type,
        value=final_value,
        confidence=field.confidence,
        provenance="UNKNOWN",  # Will be set by caller based on context
        source_document_id=source_document_id,
        source_field_raw_value=field.raw_value,
        format_valid=format_valid,
        verified=field.verification_status == DocumentVerificationStatus.DOCUMENT_VERIFIED,
    )


def normalize_extraction_result(
    result: DocumentExtractionResult,
) -> list[NormalizedField]:
    """Normalize all fields in an extraction result.

    Args:
        result: The extraction result to normalize.

    Returns:
        List of normalized fields.
    """
    if not isinstance(result, DocumentExtractionResult):
        raise NormalizationError("Expected DocumentExtractionResult")

    normalized = []
    for field in result.extracted_fields:
        try:
            normalized_field = normalize_field(field, result.document_id)
            normalized.append(normalized_field)
        except Exception as e:
            raise NormalizationError(
                f"Failed to normalize field {field.field_type}: {e}",
                field_type=field.field_type.value,
            ) from e

    return normalized
