"""Tests for PDF extraction."""

from __future__ import annotations

import pytest

from rag.ingestion.pdf_extractor import (
    EncryptedPDFError,
    PDFExtractionError,
    extract_pdf,
    extract_with_pdfplumber,
)


def test_valid_text_pdf(text_pdf):
    result = extract_pdf(text_pdf)
    assert result.page_count == 2
    assert result.has_extractable_text
    assert result.total_char_count > 0
    assert result.pages[0].page_number == 1
    assert "Udyam Registration" in result.pages[0].text
    assert result.pages[1].page_number == 2
    assert "Classification" in result.pages[1].text
    assert result.extraction_method == "pdf_text"


def test_page_boundary_preserved(text_pdf):
    result = extract_pdf(text_pdf)
    assert len(result.pages) == 2
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2


def test_empty_pdf(empty_pdf):
    result = extract_pdf(empty_pdf)
    # PyMuPDF still reports a page even for an empty doc we created with no pages
    assert result.total_char_count == 0
    assert not result.has_extractable_text


def test_corrupted_pdf(corrupted_pdf):
    with pytest.raises(PDFExtractionError):
        extract_pdf(corrupted_pdf)


def test_unsupported_file_rejected(unsupported_file):
    from rag.ingestion.pipeline import IngestionPipeline

    pipeline = IngestionPipeline()
    result = pipeline.ingest_document(
        file_path=str(unsupported_file),
        source_id="TEST_UNSUPPORTED",
        title="Not a PDF",
        authority="Test",
        source_url="https://example.com",
    )
    assert result.status == "failed"
    assert result.chunks_created == 0


def test_pdfplumber_fallback(text_pdf):
    result = extract_with_pdfplumber(text_pdf)
    assert result.page_count == 2
    assert result.has_extractable_text
    assert result.total_char_count > 0
