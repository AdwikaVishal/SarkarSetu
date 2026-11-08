"""OCR fallback for scanned or image-based PDFs.

Renders PDF pages to images and applies Tesseract OCR. When the Tesseract
binary is unavailable, degradation is graceful: extraction is marked as
OCR-required but not silently treated as an empty document.
"""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from PIL import Image

from rag.config.logging_config import get_logger

logger = get_logger("ocr_processor")


class OCRUnavailableError(Exception):
    """Raised when Tesseract is not installed or not configured."""


@dataclass
class OCRPageResult:
    page_number: int
    text: str
    char_count: int
    confidence_avg: float | None
    low_quality: bool


@dataclass
class OCRResult:
    file_path: str
    pages: list[OCRPageResult]
    total_char_count: int
    ocr_available: bool
    errors: list[str]


def _resolve_tesseract_cmd(tesseract_cmd: str | None) -> str | None:
    if tesseract_cmd and Path(tesseract_cmd).exists():
        return tesseract_cmd
    # Common Windows install locations
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    # Check PATH
    found = shutil.which("tesseract")
    if found:
        return found
    return None


def ocr_available(tesseract_cmd: str | None = None) -> bool:
    """Return True if the Tesseract binary is available."""
    return _resolve_tesseract_cmd(tesseract_cmd) is not None


def ocr_pdf(
    file_path: str | Path,
    *,
    tesseract_cmd: str | None = None,
    dpi: int = 200,
    low_quality_char_threshold: int = 80,
) -> OCRResult:
    """Run OCR on every page of a PDF.

    Args:
        file_path: Path to the PDF file.
        tesseract_cmd: Optional path to tesseract executable.
        dpi: Render resolution for page images.
        low_quality_char_threshold: Pages below this char count are flagged
            as low-quality extraction.

    Returns:
        OCRResult with per-page OCR text.
    """
    path = Path(file_path)
    if not path.exists():
        return OCRResult(
            file_path=str(path),
            pages=[],
            total_char_count=0,
            ocr_available=False,
            errors=[f"File not found: {path}"],
        )

    cmd = _resolve_tesseract_cmd(tesseract_cmd)
    if cmd is None:
        logger.warning(
            "Tesseract binary not found; OCR fallback unavailable for %s", path
        )
        return OCRResult(
            file_path=str(path),
            pages=[],
            total_char_count=0,
            ocr_available=False,
            errors=[
                "Tesseract OCR binary not installed. Install Tesseract OCR "
                "and set RAG_TESSERACT_CMD or add it to PATH to enable OCR."
            ],
        )

    try:
        import pytesseract  # noqa: PLC0415 - lazy import

        pytesseract.pytesseract.tesseract_cmd = cmd
    except ImportError as exc:  # noqa: BLE001
        return OCRResult(
            file_path=str(path),
            pages=[],
            total_char_count=0,
            ocr_available=False,
            errors=[f"pytesseract library not installed: {exc}"],
        )

    pages: list[OCRPageResult] = []
    total_chars = 0
    errors: list[str] = []

    doc = None
    try:
        doc = fitz.open(str(path))
        for index in range(doc.page_count):
            page = doc[index]
            try:
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes(
                    "RGB", [pix.width, pix.height], pix.samples
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to render page %d for OCR: %s", index + 1, exc
                )
                errors.append(f"page {index + 1} render: {exc}")
                pages.append(
                    OCRPageResult(
                        page_number=index + 1,
                        text="",
                        char_count=0,
                        confidence_avg=None,
                        low_quality=True,
                    )
                )
                continue

            try:
                data = pytesseract.image_to_data(
                    img, output_type=pytesseract.Output.DICT
                )
                text = pytesseract.image_to_string(img)
            except Exception as exc:  # noqa: BLE001
                logger.warning("OCR failed on page %d: %s", index + 1, exc)
                errors.append(f"page {index + 1} ocr: {exc}")
                text = ""
                data = {"conf": []}

            conf_values = [
                float(c)
                for c in data.get("conf", [])
                if c not in (None, -1, "")
            ]
            confidence_avg = (
                sum(conf_values) / len(conf_values) if conf_values else None
            )
            char_count = len(text)
            low_quality = char_count < low_quality_char_threshold

            pages.append(
                OCRPageResult(
                    page_number=index + 1,
                    text=text,
                    char_count=char_count,
                    confidence_avg=confidence_avg,
                    low_quality=low_quality or (
                        confidence_avg is not None
                        and confidence_avg < 40.0
                    ),
                )
            )
            total_chars += char_count
    finally:
        if doc is not None:
            doc.close()

    return OCRResult(
        file_path=str(path),
        pages=pages,
        total_char_count=total_chars,
        ocr_available=True,
        errors=errors,
    )
