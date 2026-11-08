"""Document-to-requirement matching engine.

Compares a user's uploaded/extracted documents against a required
document checklist for a government service or scheme. Produces
availability, missing, review, and inconsistency lists. This is a
preparation/completeness check only — not official verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.config.logging_config import get_logger
from rag.documents.schemas import ExtractedField, MatchResult

logger = get_logger("document_matching")


# Default required documents per service (illustrative, not legally binding).
DEFAULT_REQUIREMENTS: dict[str, list[dict[str, Any]]] = {
    "udyam_registration": [
        {"name": "Aadhaar card", "category": "aadhaar", "mandatory": True},
        {"name": "PAN card", "category": "pan", "mandatory": True},
        {"name": "Business address proof", "category": "address_proof", "mandatory": False},
        {"name": "Bank account details", "category": "bank_statement", "mandatory": False},
    ],
    "gst_registration": [
        {"name": "PAN card", "category": "pan", "mandatory": True},
        {"name": "Aadhaar card", "category": "aadhaar", "mandatory": True},
        {"name": "Business registration certificate", "category": "business_registration", "mandatory": True},
        {"name": "Address proof", "category": "address_proof", "mandatory": True},
        {"name": "Bank statement", "category": "bank_statement", "mandatory": True},
    ],
    "msme_scheme": [
        {"name": "Udyam certificate", "category": "udyam", "mandatory": True},
        {"name": "Aadhaar card", "category": "aadhaar", "mandatory": True},
        {"name": "Bank statement", "category": "bank_statement", "mandatory": False},
    ],
}


@dataclass
class ExtractedDocument:
    document_id: str
    document_type: str
    classification_confidence: float
    extracted_fields: dict[str, ExtractedField]
    extraction_errors: list[str]
    validation_status: str


def get_required_documents(service: str) -> list[dict[str, Any]]:
    """Return the default checklist for a service.

    These are illustrative requirements; users should verify against
    official government sources.
    """
    return list(DEFAULT_REQUIREMENTS.get(service, []))


def match_documents_to_requirements(
    extracted_documents: list[dict[str, Any]],
    required_documents: list[dict[str, Any]],
    *,
    service: str = "unknown",
) -> dict[str, Any]:
    """Match extracted documents against required documents.

    Args:
        extracted_documents: List of processed document dicts (each with
            document_type, classification_confidence, extracted_fields,
            validation_status, extraction_errors).
        required_documents: List of requirement dicts (each with name,
            category, mandatory).
        service: Service/scheme name for the report.

    Returns:
        A match result dict (see MatchResult).
    """
    result = MatchResult(service=service)

    # Index extracted documents by category
    available_categories: dict[str, list[dict[str, Any]]] = {}
    for doc in extracted_documents:
        category = doc.get("document_type", "other/unknown")
        available_categories.setdefault(category, []).append(doc)

    for requirement in required_documents:
        req_name = requirement.get("name", "Unnamed requirement")
        req_category = requirement.get("category", "other/unknown")
        mandatory = bool(requirement.get("mandatory", False))
        docs = available_categories.get(req_category, [])

        if not docs:
            entry = {
                "name": req_name,
                "category": req_category,
                "mandatory": mandatory,
                "reason": "No document of this category was uploaded",
            }
            result.missing_documents.append(entry)
            continue

        # Pick the highest-confidence document in the category
        best = max(docs, key=lambda d: d.get("classification_confidence", 0.0))
        best_conf = best.get("classification_confidence", 0.0)
        errors = best.get("extraction_errors", [])
        validation_status = best.get("validation_status", "needs_review")

        entry = {
            "name": req_name,
            "category": req_category,
            "mandatory": mandatory,
            "document_id": best.get("document_id"),
            "document_type": best.get("document_type"),
            "classification_confidence": best_conf,
            "extracted_fields": best.get("extracted_fields", {}),
        }

        # Incomplete extraction if required fields missing or errors present
        has_errors = bool(errors) or validation_status != "validated"
        missing_core = _core_fields_missing(req_category, best.get("extracted_fields", {}))

        if has_errors or missing_core:
            entry["reason"] = "Extraction incomplete or needs manual review"
            entry["missing_fields"] = missing_core
            result.incomplete_extraction.append(entry)
        elif best_conf < 0.5:
            entry["reason"] = "Low classification confidence"
            result.needs_review.append(entry)
        else:
            result.available_documents.append(entry)

    # Determine overall status
    missing_mandatory = [
        m for m in result.missing_documents if m.get("mandatory")
    ]
    if result.missing_documents or result.incomplete_extraction or result.needs_review:
        if missing_mandatory:
            result.overall_status = "incomplete"
        else:
            result.overall_status = "needs_review"
    else:
        result.overall_status = "complete"

    total = len(required_documents)
    covered = len(result.available_documents)
    result.checklist_coverage = round(covered / total, 2) if total else 0.0

    return result.model_dump(mode="json")


def _core_fields_missing(
    category: str, fields: dict[str, Any]
) -> list[str]:
    """Return core fields expected but missing for a category."""
    core: dict[str, list[str]] = {
        "pan": ["pan_identifier"],
        "gstin": ["gstin"],
        "aadhaar": [],
        "udyam": ["registration_number"],
        "business_registration": ["business_name", "registration_number"],
        "address_proof": ["address"],
        "bank_statement": [],
    }
    expected = core.get(category, [])
    missing = [f for f in expected if fields.get(f) in (None, {})]
    return missing

