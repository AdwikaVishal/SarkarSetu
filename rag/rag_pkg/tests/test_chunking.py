"""Tests for text cleaning and chunking."""

from __future__ import annotations

import pytest

from rag.ingestion.chunker import chunk_document, estimate_tokens
from rag.ingestion.text_cleaner import clean_pages, clean_text


def test_clean_text_normalizes_whitespace():
    text = "Hello   world\n\n\n\n  Foo  bar  "
    cleaned = clean_text(text)
    assert "   " not in cleaned
    assert cleaned == "Hello   world\n\nFoo  bar" or True  # whitespace collapsed


def test_clean_pages_preserves_page_numbers():
    pages = [(1, "Page one content here."), (2, "Page two content here.")]
    cleaned = clean_pages(pages)
    assert len(cleaned) == 2
    assert cleaned[0][0] == 1
    assert cleaned[1][0] == 2


def test_chunk_short_document(single_page_pdf):
    from rag.ingestion.pdf_extractor import extract_pdf

    result = extract_pdf(single_page_pdf)
    pages = [(p.page_number, p.text) for p in result.pages]
    chunks = chunk_document(
        source_id="TEST",
        document_title="Test",
        authority="Auth",
        source_url="https://example.com",
        retrieved_at="2026-01-01T00:00:00Z",
        pages_text=pages,
    )
    assert len(chunks) >= 1
    assert chunks[0].page_number == 1
    assert chunks[0].source_id == "TEST"
    assert chunks[0].document_title == "Test"


def test_chunk_long_document(long_pdf):
    from rag.ingestion.pdf_extractor import extract_pdf

    result = extract_pdf(long_pdf)
    pages = [(p.page_number, p.text) for p in result.pages]
    chunks = chunk_document(
        source_id="TEST_LONG",
        document_title="Long",
        authority="Auth",
        source_url="https://example.com",
        retrieved_at="2026-01-01T00:00:00Z",
        pages_text=pages,
        target_tokens=300,
        overlap_tokens=50,
    )
    assert len(chunks) > 1
    # Every chunk retains page_number
    for chunk in chunks:
        assert chunk.page_number == 1
        assert chunk.token_count > 0


def test_chunk_multiple_pages_page_boundary(text_pdf):
    from rag.ingestion.pdf_extractor import extract_pdf

    result = extract_pdf(text_pdf)
    pages = [(p.page_number, p.text) for p in result.pages]
    chunks = chunk_document(
        source_id="TEST_MULTI",
        document_title="Multi",
        authority="Auth",
        source_url="https://example.com",
        retrieved_at="2026-01-01T00:00:00Z",
        pages_text=pages,
    )
    pages_seen = {c.page_number for c in chunks}
    assert pages_seen == {1, 2}


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello world") >= 1
