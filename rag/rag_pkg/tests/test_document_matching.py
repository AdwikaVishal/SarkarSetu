"""Tests for document-to-requirement matching."""

from __future__ import annotations

from rag.document_matching.matcher import match_documents_to_requirements


def _make_doc(doc_id, doc_type, confidence=0.9, errors=None, fields=None, status="validated"):
    return {
        "document_id": doc_id,
        "document_type": doc_type,
        "classification_confidence": confidence,
        "extraction_errors": errors or [],
        "extracted_fields": fields or {},
        "validation_status": status,
    }


def test_all_required_documents_available():
    extracted = [
        _make_doc("D1", "pan", fields={"pan_identifier": {"value": "ABCDE1234F", "confidence": 0.9}}),
        _make_doc("D2", "aadhaar"),
        _make_doc("D3", "address_proof", fields={"address": {"value": "123 Street", "confidence": 0.8}}),
    ]
    required = [
        {"name": "PAN card", "category": "pan", "mandatory": True},
        {"name": "Aadhaar card", "category": "aadhaar", "mandatory": True},
        {"name": "Address proof", "category": "address_proof", "mandatory": False},
    ]
    result = match_documents_to_requirements(extracted, required, service="gst_registration")
    assert result["overall_status"] in ("complete", "needs_review")
    assert len(result["available_documents"]) >= 1


def test_some_documents_missing():
    extracted = [
        _make_doc("D1", "pan"),
    ]
    required = [
        {"name": "PAN card", "category": "pan", "mandatory": True},
        {"name": "Aadhaar card", "category": "aadhaar", "mandatory": True},
        {"name": "Bank statement", "category": "bank_statement", "mandatory": False},
    ]
    result = match_documents_to_requirements(extracted, required, service="gst_registration")
    assert len(result["missing_documents"]) >= 1
    missing_names = {m["name"] for m in result["missing_documents"]}
    assert "Aadhaar card" in missing_names


def test_incomplete_extraction_flagged():
    extracted = [
        _make_doc("D1", "pan", errors=["OCR failed"], status="needs_review"),
    ]
    required = [
        {"name": "PAN card", "category": "pan", "mandatory": True},
    ]
    result = match_documents_to_requirements(extracted, required, service="gst_registration")
    assert len(result["incomplete_extraction"]) >= 1 or len(result["missing_documents"]) >= 1


def test_incorrect_document_category():
    extracted = [
        _make_doc("D1", "bank_statement"),
    ]
    required = [
        {"name": "PAN card", "category": "pan", "mandatory": True},
    ]
    result = match_documents_to_requirements(extracted, required, service="gst_registration")
    missing_names = {m["name"] for m in result["missing_documents"]}
    assert "PAN card" in missing_names
