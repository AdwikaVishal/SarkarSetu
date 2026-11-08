"""Document Agent.

Reusable agent that processes user-uploaded documents: validation,
classification, field extraction, and requirement matching. Uses
deterministic extraction wherever possible. Exposes process_document
and match_documents_to_requirements for backend integration.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from rag.config.logging_config import get_logger
from rag.config.settings import settings
from rag.documents.classifier import classify_document, classification_to_schema
from rag.documents.field_extractor import extract_fields, extraction_to_schema
from rag.documents.schemas import (
    ExtractedField,
    FieldExtractionResult,
    ProcessDocumentResult,
    mask_sensitive,
)
from rag.documents.upload_validator import UploadValidationError, validate_upload
from rag.document_matching.matcher import (
    ExtractedDocument,
    match_documents_to_requirements,
)

logger = get_logger("document_agent")


def process_document(
    *,
    file_path: str,
    business_context: dict[str, Any] | None = None,
    service_type: str = "unknown",
) -> dict[str, Any]:
    """Process a user-uploaded PDF document end-to-end.

    Args:
        file_path: Path to the uploaded PDF (temporary or stored).
        business_context: Optional business profile context.
        service_type: The government service the document relates to.

    Returns:
        A ProcessDocumentResult dict with classification, field
        extraction, and masking applied.
    """
    business_context = business_context or {}
    warnings: list[str] = []
    extraction_errors: list[str] = []

    # --- Upload validation ---
    try:
        validated = validate_upload(file_path=file_path)
    except UploadValidationError as exc:
        logger.warning("Upload validation failed: %s", exc)
        return ProcessDocumentResult(
            document_id="DOC_ERROR",
            document_type="other/unknown",
            classification_confidence=0.0,
            validation_status="rejected",
            extraction_errors=[str(exc)],
            warnings=warnings,
        ).model_dump(mode="json")

    document_id = validated.document_id

    # --- Classification ---
    try:
        classified = classify_document(file_path=validated.stored_path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Classification failed for %s", document_id)
        classified = None  # type: ignore[assignment]
        extraction_errors.append(f"Classification failed: {exc}")
        warnings.append("Document classification could not be completed")

    if classified is None:
        return ProcessDocumentResult(
            document_id=document_id,
            document_type="other/unknown",
            classification_confidence=0.0,
            validation_status="needs_review",
            extraction_errors=extraction_errors,
            warnings=warnings,
            page_count=validated.page_count,
        ).model_dump(mode="json")

    # --- Field extraction ---
    try:
        extraction = extract_fields(
            file_path=validated.stored_path,
            document_type=classified.document_type,
            text=classified.extracted_text,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Field extraction failed for %s", document_id)
        extraction_errors.append(f"Field extraction failed: {exc}")
        warnings.append("Field extraction could not be completed")
        extraction_result = FieldExtractionResult(
            document_type=classified.document_type,
            extraction_method="pdf_text",
            validation_status="needs_review",
            overall_confidence=0.0,
        )
    else:
        extraction_result = extraction_to_schema(extraction, mask=True)

    # --- Sensitive value masking in logs only (not repeated here) ---
    logger.info(
        "Processed document %s type=%s pages=%s",
        document_id,
        classified.document_type,
        validated.page_count,
    )

    result = ProcessDocumentResult(
        document_id=document_id,
        document_type=classified.document_type,
        classification_confidence=classified.confidence,
        classification_method=classified.method,
        extracted_fields=extraction_result.extracted_fields,
        extraction_method=extraction_result.extraction_method,
        validation_status=extraction_result.validation_status,
        page_count=validated.page_count,
        char_count=len(classified.extracted_text) if classified.extracted_text else None,
        extraction_errors=extraction_errors,
        warnings=warnings,
    )
    return result.model_dump(mode="json")


def match_documents_to_requirements(
    extracted_documents: list[dict[str, Any]],
    required_documents: list[dict[str, Any]],
    *,
    service: str = "unknown",
) -> dict[str, Any]:
    """Delegate to the document matching engine.

    See rag.document_matching.matcher.match_documents_to_requirements.
    """
    from rag.document_matching.matcher import match_documents_to_requirements as _match

    return _match(
        extracted_documents=extracted_documents,
        required_documents=required_documents,
        service=service,
    )


# Backward-compatible alias (module-level function name matches import path)
process_document.__doc__ = (
    "Process a user-uploaded PDF document end-to-end. "
    "Returns a dict with document_id, document_type, extracted_fields, etc."
)
