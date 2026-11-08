"""Tests for the Document Agent and upload validation."""

from __future__ import annotations

import os

import pytest

from rag.agents.document_agent import process_document
from rag.documents.upload_validator import (
    UploadValidationError,
    generate_document_id,
    safe_filename,
    validate_upload,
)


def test_generate_document_id_unique():
    id1 = generate_document_id()
    id2 = generate_document_id()
    assert id1 != id2
    assert id1.startswith("DOC_")


def test_safe_filename_neutralizes_unsafe_chars():
    assert safe_filename("../../../etc/passwd") == "passwd"
    assert safe_filename("a/b/../my document.pdf") == "my_document.pdf"


def test_validate_upload_rejects_unsupported(tmp_path):
    path = tmp_path / "document.txt"
    path.write_text("hello")
    with pytest.raises(UploadValidationError):
        validate_upload(file_path=str(path), original_filename="document.txt")


def test_process_document_rejects_corrupted(corrupted_pdf):
    result = process_document(
        file_path=str(corrupted_pdf),
        business_context={},
        service_type="gst_registration",
    )
    assert result["validation_status"] == "rejected"
    assert result["document_type"] == "other/unknown"


def test_process_document_structured_output(text_pdf, gst_document_text):
    result = process_document(
        file_path=str(text_pdf),
        business_context={},
        service_type="udyam_registration",
    )
    assert "document_id" in result
    assert "document_type" in result
    assert "classification_confidence" in result
    assert "extracted_fields" in result
    assert "validation_status" in result
    assert result["document_id"].startswith("DOC_")
