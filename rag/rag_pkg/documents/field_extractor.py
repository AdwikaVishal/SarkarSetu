"""Field extraction from user-uploaded documents.

Extracts document type, name, business name, address, PAN, GSTIN,
registration number, issue date, and expiry date. Never invents missing
fields; returns None when unavailable. Sensitive values are masked in
ordinary outputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rag.config.logging_config import get_logger
from rag.config.settings import settings
from rag.documents.schemas import (
    ExtractedField,
    FieldExtractionResult,
    mask_sensitive,
)
from rag.ingestion.pdf_extractor import extract_pdf
from rag.ingestion.text_cleaner import clean_text

logger = get_logger("field_extractor")


@dataclass
class FieldExtraction:
    document_type: str
    fields: dict[str, ExtractedField]
    method: str
    overall_confidence: float


_PAN_RE = re.compile(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b")
_GSTIN_RE = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b")
_AADHAAR_RE = re.compile(r"\b([0-9]{4}\s[0-9]{4}\s[0-9]{4})\b")
_DATE_RE = re.compile(
    r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b"
)
_REGISTRATION_RE = re.compile(
    r"(?i)(registration\s*(?:number|no)?|regn\.?\s*no\.?|udyam\s*no\.?)[:\s]*([A-Z0-9\-/]{5,})"
)
_NAME_LABELS = re.compile(r"(?i)(name|proprietor|partner|director)\s*:\s*([^\n]{2,60})")
_BUSINESS_LABELS = re.compile(
    r"(?i)(business|firm|company|establishment|trade)\s*(?:name)?\s*:\s*([^\n]{2,80})"
)
_ADDRESS_LABELS = re.compile(
    r"(?i)(address|premises)\s*:\s*([^\n]{5,100})"
)


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if match:
        # Return the last capturing group that has content
        for group in match.groups()[::-1]:
            if group:
                return group.strip()
    return None


def extract_fields(
    *,
    file_path: str | Path,
    document_type: str | None = None,
    text: str | None = None,
) -> FieldExtraction:
    """Extract structured fields from a document.

    Args:
        file_path: Path to the PDF.
        document_type: Known document type (helps tune extraction).
        text: Pre-extracted text (if None, extracted from PDF).

    Returns:
        FieldExtraction with extracted fields and confidence.
    """
    if text is None:
        try:
            extraction = extract_pdf(file_path, min_chars_for_text=1)
            text = "\n".join(p.text for p in extraction.pages)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Text extraction failed during field extraction: %s", exc)
            text = ""

    cleaned = clean_text(text)
    fields: dict[str, ExtractedField] = {}
    method = "pdf_text"

    # PAN
    pan = _first_match(_PAN_RE, cleaned)
    fields["pan_identifier"] = ExtractedField(
        value=pan, confidence=0.9 if pan else 0.0, method="regex"
    )
    # GSTIN
    gstin = _first_match(_GSTIN_RE, cleaned)
    fields["gstin"] = ExtractedField(
        value=gstin, confidence=0.9 if gstin else 0.0, method="regex"
    )
    # Registration number
    reg = _first_match(_REGISTRATION_RE, cleaned)
    fields["registration_number"] = ExtractedField(
        value=reg, confidence=0.7 if reg else 0.0, method="regex"
    )
    # Name
    name = _first_match(_NAME_LABELS, cleaned)
    fields["name"] = ExtractedField(
        value=name, confidence=0.6 if name else 0.0, method="regex"
    )
    # Business name
    business_name = _first_match(_BUSINESS_LABELS, cleaned)
    fields["business_name"] = ExtractedField(
        value=business_name, confidence=0.6 if business_name else 0.0, method="regex"
    )
    # Address
    address = _first_match(_ADDRESS_LABELS, cleaned)
    fields["address"] = ExtractedField(
        value=address, confidence=0.5 if address else 0.0, method="regex"
    )
    # Issue date (first date found)
    issue_date = _first_match(_DATE_RE, cleaned)
    fields["issue_date"] = ExtractedField(
        value=issue_date, confidence=0.5 if issue_date else 0.0, method="regex"
    )
    # Expiry date: not reliably inferred; leave None unless labeled
    expiry_label = re.search(r"(?i)(expiry|valid until|valid up to)\s*:\s*([^\n]{2,20})", cleaned)
    expiry_date = expiry_label.group(2).strip() if expiry_label else None
    fields["expiry_date"] = ExtractedField(
        value=expiry_date, confidence=0.7 if expiry_date else 0.0, method="regex"
    )

    confidences = [f.confidence for f in fields.values() if f.value is not None]
    overall = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    return FieldExtraction(
        document_type=document_type or "other/unknown",
        fields=fields,
        method=method,
        overall_confidence=overall,
    )


def extraction_to_schema(extraction: FieldExtraction, *, mask: bool = True) -> FieldExtractionResult:
    masked_fields: dict[str, ExtractedField] = {}
    for key, field in extraction.fields.items():
        value = field.masked_value(mask=mask) if mask else field.value
        masked_fields[key] = ExtractedField(
            value=value,
            confidence=field.confidence,
            method=field.method,
        )
    return FieldExtractionResult(
        document_type=extraction.document_type,
        extracted_fields=masked_fields,
        extraction_method=extraction.method,
        validation_status="needs_review",
        overall_confidence=extraction.overall_confidence,
    )
