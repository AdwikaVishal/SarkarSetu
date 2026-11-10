"""Upload validation for user-submitted PDF documents.

Validates file type, size, readability, and generates safe document IDs.
Never logs document contents.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from rag.config.logging_config import get_logger
from rag.config.settings import allowed_extensions, settings

logger = get_logger("upload_validator")


class UploadValidationError(Exception):
    """Raised when an uploaded file fails validation."""


@dataclass
class ValidatedUpload:
    """A validated, safely-named upload ready for processing."""

    document_id: str
    safe_filename: str
    stored_path: Path
    original_filename: str
    file_size: int
    content_hash: str
    page_count: int
    is_readable: bool


_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def generate_document_id() -> str:
    """Generate a unique document id."""
    return f"DOC_{uuid.uuid4().hex[:12]}"


def safe_filename(filename: str) -> str:
    """Return a safe filesystem name derived from the original filename."""
    base = Path(filename).name
    base = _UNSAFE_FILENAME_CHARS.sub("_", base)
    if not base or base in {".", ".."}:
        base = "document.pdf"
    return base


def compute_file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_upload(
    *,
    file_path: str | Path,
    original_filename: str | None = None,
    max_size_mb: int | None = None,
    allowed_extensions: set[str] | None = None,
    document_id: str | None = None,
) -> ValidatedUpload:
    """Validate an uploaded PDF file.

    Args:
        file_path: Path to the uploaded file (temporary location).
        original_filename: Original client filename (for safe naming).
        max_size_mb: Override max file size in MB.
        allowed_extensions: Override allowed extensions.
        document_id: Optional pre-assigned document id.

    Returns:
        ValidatedUpload with safe filename, stored path, page count.

    Raises:
        UploadValidationError: On any validation failure.
    """
    path = Path(file_path)
    if not path.exists():
        raise UploadValidationError(f"File not found: {path}")

    # File type check
    ext = path.suffix.lower()
    allowed = allowed_extensions or {
        e.strip().lower() for e in settings.allowed_extensions_csv.split(",") if e.strip()
    }
    if ext not in allowed:
        raise UploadValidationError(
            f"Unsupported file type '{ext}'. Allowed: {sorted(allowed)}"
        )

    # File size check
    max_bytes = (max_size_mb or settings.max_file_size_mb) * 1024 * 1024
    file_size = path.stat().st_size
    if file_size > max_bytes:
        raise UploadValidationError(
            f"File size {file_size} bytes exceeds limit {max_bytes} bytes"
        )
    if file_size == 0:
        raise UploadValidationError("Uploaded file is empty")

    # Readability / integrity check via PyMuPDF
    doc = None
    page_count = 0
    try:
        doc = fitz.open(str(path))
        page_count = doc.page_count
        if page_count == 0:
            raise UploadValidationError("PDF contains no pages")
        # Try reading first page to detect corruption
        _ = doc[0].get_text()
    except UploadValidationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise UploadValidationError(
            f"PDF is corrupted or unreadable: {exc}"
        ) from exc
    finally:
        if doc is not None:
            doc.close()

    # Content hash
    data = path.read_bytes()
    content_hash = compute_file_hash(data)

    doc_id = document_id or generate_document_id()
    stored_name = safe_filename(original_filename or path.name)
    safe_name = f"{doc_id}_{stored_name}"

    return ValidatedUpload(
        document_id=doc_id,
        safe_filename=safe_name,
        stored_path=path,
        original_filename=original_filename or path.name,
        file_size=file_size,
        content_hash=content_hash,
        page_count=page_count,
        is_readable=True,
    )
