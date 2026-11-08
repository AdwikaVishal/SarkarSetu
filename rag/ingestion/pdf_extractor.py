"""PDF text extraction using PyMuPDF (primary) and pdfplumber (fallback).

Preserves page boundaries so citations can reference exact pages.
Encrypted and corrupted PDFs are handled safely.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from rag.config.logging_config import get_logger

logger = get_logger("pdf_extractor")


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be extracted."""


class EncryptedPDFError(PDFExtractionError):
    """Raised when a PDF is encrypted and cannot be opened without a password."""


@dataclass
class PageText:
    """Extracted text for a single PDF page."""

    page_number: int  # 1-indexed
    text: str
    extraction_method: str  # "pdf_text" or "ocr"
    char_count: int
    metadata: dict[str, Any]


@dataclass
class PDFExtractionResult:
    """Result of extracting a PDF document."""

    file_path: str
    title: str | None
    page_count: int
    pages: list[PageText]
    total_char_count: int
    extraction_method: str  # dominant method used
    encrypted: bool
    errors: list[str]

    @property
    def has_extractable_text(self) -> bool:
        return self.total_char_count > 0


def extract_pdf(
    file_path: str | Path,
    *,
    password: str | None = None,
    min_chars_for_text: int = 10,
) -> PDFExtractionResult:
    """Extract text from a PDF page-by-page using PyMuPDF.

    Args:
        file_path: Path to the PDF file.
        password: Optional password for encrypted PDFs.
        min_chars_for_text: Minimum chars per page to treat as text-based.

    Returns:
        PDFExtractionResult with per-page text and metadata.
    """
    path = Path(file_path)
    if not path.exists():
        raise PDFExtractionError(f"File not found: {path}")

    errors: list[str] = []
    doc = None
    try:
        try:
            doc = fitz.open(str(path))
        except fitz.FileDataError as exc:
            if "encrypted" in str(exc).lower() or "password" in str(exc).lower():
                raise EncryptedPDFError(
                    f"PDF is encrypted and requires a password: {path}"
                ) from exc
            raise PDFExtractionError(
                f"Unable to read PDF (corrupted or unsupported): {path}: {exc}"
            ) from exc

        if doc.is_encrypted:
            try:
                doc.authenticate(password or "")
            except Exception as exc:  # noqa: BLE001
                raise EncryptedPDFError(
                    f"PDF is encrypted and could not be decrypted: {path}"
                ) from exc

        page_count = doc.page_count
        title = doc.metadata.get("title") if doc.metadata else None
        title = title or None

        pages: list[PageText] = []
        total_chars = 0
        text_pages = 0

        for index in range(page_count):
            page = doc[index]
            text = page.get_text("text") or ""
            method = "pdf_text"
            char_count = len(text)

            if char_count < min_chars_for_text:
                # Likely scanned or image-heavy page; mark for OCR fallback
                method = "pdf_text_insufficient"
                text = ""

            pages.append(
                PageText(
                    page_number=index + 1,
                    text=text,
                    extraction_method=method,
                    char_count=char_count,
                    metadata={},
                )
            )
            total_chars += char_count
            if char_count >= min_chars_for_text:
                text_pages += 1

        dominant = "pdf_text" if text_pages > 0 else "ocr_needed"

        return PDFExtractionResult(
            file_path=str(path),
            title=title,
            page_count=page_count,
            pages=pages,
            total_char_count=total_chars,
            extraction_method=dominant,
            encrypted=bool(doc.is_encrypted),
            errors=errors,
        )
    finally:
        if doc is not None:
            doc.close()


def extract_with_pdfplumber(file_path: str | Path) -> PDFExtractionResult:
    """Fallback extraction using pdfplumber when PyMuPDF yields little text.

    Preserves page boundaries and returns the same result shape.
    """
    import pdfplumber

    path = Path(file_path)
    pages: list[PageText] = []
    total_chars = 0
    errors: list[str] = []

    try:
        with pdfplumber.open(str(path)) as pdf:
            for index, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text() or ""
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "pdfplumber failed on page %d: %s", index + 1, exc
                    )
                    text = ""
                    errors.append(f"page {index + 1}: {exc}")
                char_count = len(text)
                pages.append(
                    PageText(
                        page_number=index + 1,
                        text=text,
                        extraction_method="pdf_text",
                        char_count=char_count,
                        metadata={},
                    )
                )
                total_chars += char_count
    except Exception as exc:  # noqa: BLE001
        raise PDFExtractionError(
            f"pdfplumber fallback failed for {path}: {exc}"
        ) from exc

    title: str | None = None
    return PDFExtractionResult(
        file_path=str(path),
        title=title,
        page_count=len(pages),
        pages=pages,
        total_char_count=total_chars,
        extraction_method="pdf_text",
        encrypted=False,
        errors=errors,
    )
