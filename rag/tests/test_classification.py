"""Tests for document classification."""

from __future__ import annotations

from rag.documents.classifier import classify_document, classification_to_schema
from rag.documents.schemas import DocumentClassification


def test_gst_document_classified(gst_document_text):
    classified = classify_document(file_path="dummy.pdf", text=gst_document_text)
    assert classified.document_type == "gst"
    assert classified.confidence > 0
    assert classified.method == "rule_based"


def test_pan_document_classified(pan_document_text):
    classified = classify_document(file_path="dummy.pdf", text=pan_document_text)
    assert classified.document_type == "pan"
    assert classified.confidence > 0


def test_unknown_document_type():
    classified = classify_document(
        file_path="dummy.pdf",
        text="This is a generic unrelated document about cooking recipes.",
    )
    assert classified.document_type == "other/unknown"
    assert classified.confidence == 0.0


def test_classification_to_schema(gst_document_text):
    classified = classify_document(file_path="dummy.pdf", text=gst_document_text)
    schema = classification_to_schema(classified)
    assert isinstance(schema, DocumentClassification)
    assert schema.document_type == classified.document_type
