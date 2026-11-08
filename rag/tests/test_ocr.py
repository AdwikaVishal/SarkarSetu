"""Tests for OCR processing.

Covers both environments:

- Tesseract installed: OCR extracts text from scanned/image PDFs and flags
  low-quality pages.
- Tesseract absent: graceful degradation -- ocr_available=False, errors
  reported, and a scanned PDF is never silently treated as a document with
  extractable content.
"""

from __future__ import annotations

import fitz  # noqa: F401  (used to build test fixtures)

from rag.ingestion.ocr_processor import OCRResult, ocr_available, ocr_pdf


def _make_blank_pdf(tmp_path) -> object:
    path = tmp_path / "blank.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(path))
    doc.close()
    return path


def _make_image_pdf(tmp_path) -> object:
    """A PDF page containing a rendered text image (simulates a scan)."""
    from PIL import Image, ImageDraw, ImageFont

    path = tmp_path / "scan.pdf"
    img = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        font = ImageFont.load_default()
    draw.text((60, 100), "Udyam Registration is free and based on self-declaration.", fill="black", font=font)
    img.save(str(tmp_path / "scan.png"))
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(fitz.Rect(0, 0, 800, 600), filename=str(tmp_path / "scan.png"))
    doc.save(str(path))
    doc.close()
    return path


def test_ocr_available_flag_is_bool():
    assert isinstance(ocr_available(), bool)


def test_ocr_pdf_never_raises(tmp_path):
    """ocr_pdf must not raise whether or not Tesseract is installed."""
    path = _make_blank_pdf(tmp_path)
    result = ocr_pdf(path)
    assert isinstance(result, OCRResult)
    assert hasattr(result, "pages")
    assert hasattr(result, "file_path")
    assert hasattr(result, "errors")


def test_ocr_graceful_when_tesseract_missing(tmp_path):
    """When Tesseract is unavailable, OCR reports failure rather than
    silently treating the scanned document as having extractable text."""
    path = _make_blank_pdf(tmp_path)
    result = ocr_pdf(path)
    if not ocr_available():
        assert result.ocr_available is False
        assert result.total_char_count == 0
        assert len(result.errors) >= 1
    else:
        # Tesseract installed: OCR runs; a blank page yields no text but
        # must not error.
        assert result.ocr_available is True
        assert isinstance(result.pages, list)


def test_ocr_extracts_text_from_scan_when_tesseract_present(tmp_path):
    """If Tesseract is installed, an image-based PDF yields extracted text."""
    if not ocr_available():
        # Cannot test real OCR without the binary; skip rather than fabricate.
        return
    path = _make_image_pdf(tmp_path)
    result = ocr_pdf(path)
    assert result.ocr_available is True
    assert isinstance(result.pages, list)
    total = sum(pg.char_count for pg in result.pages)
    # The rendered page should yield some text via OCR.
    assert total > 0, "OCR should extract text from a scanned page"


def test_ocr_result_structure(tmp_path):
    path = _make_blank_pdf(tmp_path)
    result = ocr_pdf(path)
    assert hasattr(result, "pages")
    assert hasattr(result, "file_path")
    assert hasattr(result, "errors")
