"""Pytest fixtures and helpers for the RAG subsystem tests.

All test documents are synthetic. No real personal identity documents
are used as fixtures.
"""

from __future__ import annotations

import os
from pathlib import Path

import fitz  # PyMuPDF
import pytest

TEST_DATA_DIR = Path(__file__).resolve().parent / "fixtures"


def make_pdf(path: Path, pages_text: list[str]) -> Path:
    """Create a synthetic PDF with one text block per page.

    Text is inserted line-by-line so long content is not clipped by
    PyMuPDF's single-text-run limits.
    """
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        y = 72
        for line in text.split("\n") or [""]:
            if not line.strip():
                y += 12
                continue
            # Wrap long lines to ~100 characters so they stay on the page
            wrapped = [line[i : i + 100] for i in range(0, len(line), 100)]
            for chunk in wrapped:
                page.insert_text((72, y), chunk, fontsize=8)
                y += 11
            y += 4
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def fixtures_dir(tmp_path) -> Path:
    return tmp_path / "fixtures"


@pytest.fixture
def text_pdf(tmp_path) -> Path:
    return make_pdf(
        tmp_path / "valid_text.pdf",
        [
            "Page 1: Udyam Registration is the online registration process "
            "for Micro, Small and Medium Enterprises in India.",
            "Page 2: Classification. Micro enterprise: investment not more "
            "than Rs 1 crore and turnover not more than Rs 5 crore.",
        ],
    )


@pytest.fixture
def empty_pdf(tmp_path) -> Path:
    return make_pdf(tmp_path / "empty.pdf", [""])


@pytest.fixture
def single_page_pdf(tmp_path) -> Path:
    return make_pdf(
        tmp_path / "single.pdf",
        ["GST registration threshold is Rs 40 lakh for goods suppliers."],
    )


@pytest.fixture
def long_pdf(tmp_path) -> Path:
    text = (
        "MSME Support Schemes. "
        "The Credit Guarantee Fund Trust for Micro and Small Enterprises "
        "(CGTMSE) provides collateral-free credit to borrowers. "
        "The Prime Minister's Employment Generation Programme (PMEGP) "
        "provides subsidy for new micro enterprises. "
        "The Credit Linked Capital Subsidy Scheme (CLCSS) supports "
        "technology upgradation. "
        "Eligibility conditions vary by scheme and must be verified on the "
        "official scheme portal before application. "
    ) * 40
    return make_pdf(tmp_path / "long.pdf", [text])


@pytest.fixture
def scanned_pdf(tmp_path) -> Path:
    """A PDF with no extractable text (simulates a scanned document)."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(fitz.Rect(0, 0, 600, 800), stream=b"")
    doc.save(str(tmp_path / "scanned.pdf"))
    doc.close()
    return tmp_path / "scanned.pdf"


@pytest.fixture
def corrupted_pdf(tmp_path) -> Path:
    path = tmp_path / "corrupted.pdf"
    path.write_bytes(b"%PDF-1.4 not a real pdf truncated")
    return path


@pytest.fixture
def unsupported_file(tmp_path) -> Path:
    path = tmp_path / "document.txt"
    path.write_text("not a pdf")
    return path


@pytest.fixture
def gst_document_text() -> str:
    return (
        "GST Registration Certificate\n"
        "GSTIN: 22AAAAA0000A1Z5\n"
        "Legal Name: Example Business Private Limited\n"
        "Trade Name: Example Business\n"
        "Constitution of Business: Private Limited Company\n"
        "Address: 123 MG Road, Bengaluru, Karnataka 560001\n"
        "Date of Liability: 01/04/2024\n"
        "Period of Validity: From 01/04/2024 to Not Applicable\n"
    )


@pytest.fixture
def pan_document_text() -> str:
    return (
        "INCOME TAX DEPARTMENT, GOVT OF INDIA\n"
        "PERMANENT ACCOUNT NUMBER CARD\n"
        "Name: RAMESH KUMAR\n"
        "PAN: ABCDE1234F\n"
        "Father's Name: SURESH KUMAR\n"
        "Date of Birth: 01/01/1985\n"
    )
