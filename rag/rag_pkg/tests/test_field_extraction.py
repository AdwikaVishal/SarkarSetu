"""Tests for field extraction."""

from __future__ import annotations

from rag.documents.field_extractor import (
    extract_fields,
    extraction_to_schema,
)
from rag.documents.schemas import ExtractedField, FieldExtractionResult


def test_pan_and_gstin_extracted(pan_document_text):
    extraction = extract_fields(
        file_path="dummy.pdf", text=pan_document_text
    )
    pan_field = extraction.fields.get("pan_identifier")
    assert pan_field is not None
    assert pan_field.value == "ABCDE1234F"
    assert pan_field.confidence > 0


def test_missing_fields_are_none():
    extraction = extract_fields(
        file_path="dummy.pdf",
        text="A simple document with no identifiers or dates.",
    )
    assert extraction.fields.get("pan_identifier").value is None
    assert extraction.fields.get("gstin").value is None
    assert extraction.fields.get("registration_number").value is None


def test_extraction_to_schema_masks_sensitive(gst_document_text):
    extraction = extract_fields(file_path="dummy.pdf", text=gst_document_text)
    result = extraction_to_schema(extraction, mask=True)
    assert isinstance(result, FieldExtractionResult)
    pan = result.extracted_fields.get("pan_identifier")
    if pan and pan.value:
        assert pan.value != "ABCDE1234F"  # masked


def test_expiry_date_none_when_absent():
    extraction = extract_fields(
        file_path="dummy.pdf", text="No expiry date mentioned here."
    )
    assert extraction.fields.get("expiry_date").value is None
