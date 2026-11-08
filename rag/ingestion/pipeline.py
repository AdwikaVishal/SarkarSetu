"""Document ingestion pipeline.

Flow:

source collection -> file validation -> PDF extraction -> OCR fallback
-> text cleaning -> metadata extraction -> chunking -> embedding
generation -> FAISS indexing -> source registry update.

Each step is independently testable.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rag.config.logging_config import get_logger
from rag.config.settings import settings, allowed_extensions
from rag.embeddings.embedder import Embedder, EmbeddingError
from rag.ingestion.chunker import Chunk, chunk_document, estimate_tokens
from rag.ingestion.ocr_processor import OCRResult, ocr_available, ocr_pdf
from rag.ingestion.pdf_extractor import (
    EncryptedPDFError,
    PDFExtractionError,
    PDFExtractionResult,
    extract_pdf,
    extract_with_pdfplumber,
)
from rag.ingestion.text_cleaner import clean_pages
from rag.sources.source_metadata import SourceMetadata, SourceRegistry
from rag.sources.source_versioning import SourceVersioning
from rag.storage.faiss_index import FaissIndex
from rag.storage.metadata_store import ChunkMetadataStore

logger = get_logger("ingestion")


@dataclass
class IngestResult:
    """Result of ingesting a single document."""

    source_id: str
    status: str  # success / partial / failed
    document_title: str | None
    authority: str
    source_url: str
    page_count: int
    chunks_created: int
    chunks_indexed: int
    extraction_method: str
    verification_status: str
    content_hash: str | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "document_title": self.document_title,
            "authority": self.authority,
            "source_url": self.source_url,
            "page_count": self.page_count,
            "chunks_created": self.chunks_created,
            "chunks_indexed": self.chunks_indexed,
            "extraction_method": self.extraction_method,
            "verification_status": self.verification_status,
            "content_hash": self.content_hash,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class IngestionPipeline:
    """Orchestrates the full ingestion of a government source document."""

    def __init__(
        self,
        *,
        registry: SourceRegistry | None = None,
        versioning: SourceVersioning | None = None,
        embedder: Embedder | None = None,
        index: FaissIndex | None = None,
        metadata_store: ChunkMetadataStore | None = None,
        min_chars_for_text: int = 10,
    ) -> None:
        self.registry = registry or SourceRegistry()
        self.versioning = versioning or SourceVersioning(registry=self.registry)
        self.embedder = embedder or Embedder()
        self.index = index or FaissIndex()
        self.metadata_store = metadata_store or ChunkMetadataStore()
        self.min_chars_for_text = min_chars_for_text

    def ingest_document(
        self,
        *,
        file_path: str | Path,
        source_id: str,
        title: str,
        authority: str,
        source_url: str,
        topic: str = "",
        verification_status: str = "pending",
        password: str | None = None,
        id_prefix: str = "chunk",
    ) -> IngestResult:
        """Ingest a single PDF document into the RAG index.

        Returns an IngestResult describing what was done. On failure the
        result still contains partial information so callers can decide
        whether to retry or flag for manual review.
        """
        path = Path(file_path)
        errors: list[str] = []
        warnings: list[str] = []

        # --- File validation ---
        if not path.exists():
            return self._failure(
                source_id=source_id,
                status="failed",
                title=None,
                authority=authority,
                source_url=source_url,
                errors=[f"File not found: {path}"],
            )

        if path.suffix.lower() not in allowed_extensions():
            return self._failure(
                source_id=source_id,
                status="failed",
                title=title,
                authority=authority,
                source_url=source_url,
                errors=[
                    f"Unsupported file type '{path.suffix}'. "
                    f"Allowed: {settings.allowed_extensions_csv}"
                ],
            )

        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if path.stat().st_size > max_bytes:
            return self._failure(
                source_id=source_id,
                status="failed",
                title=title,
                authority=authority,
                source_url=source_url,
                errors=[
                    f"File size {path.stat().st_size} bytes exceeds limit "
                    f"{max_bytes} bytes"
                ],
            )

        # --- Change detection ---
        file_bytes = path.read_bytes()
        content_hash = self._hash_bytes(file_bytes)
        existing = self.registry.get(source_id)
        if existing and existing.content_hash == content_hash:
            logger.info(
                "Source %s unchanged since last ingestion; skipping re-index",
                source_id,
            )
            return IngestResult(
                source_id=source_id,
                status="success",
                document_title=existing.title or title,
                authority=existing.authority or authority,
                source_url=existing.source_url or source_url,
                page_count=existing.page_count or 0,
                chunks_created=0,
                chunks_indexed=0,
                extraction_method=existing.extraction_method or "pdf_text",
                verification_status=existing.verification_status,
                content_hash=content_hash,
                warnings=["Content unchanged; index already up to date"],
            )

        # --- PDF extraction ---
        extraction: PDFExtractionResult | None = None
        try:
            extraction = extract_pdf(path, password=password, min_chars_for_text=self.min_chars_for_text)
        except EncryptedPDFError as exc:
            return self._failure(
                source_id=source_id,
                status="failed",
                title=title,
                authority=authority,
                source_url=source_url,
                errors=[str(exc)],
            )
        except PDFExtractionError as exc:
            # Try pdfplumber fallback
            logger.warning("PyMuPDF failed (%s); trying pdfplumber", exc)
            try:
                extraction = extract_with_pdfplumber(path)
                warnings.append("PyMuPDF extraction failed; used pdfplumber fallback")
            except PDFExtractionError as exc2:
                return self._failure(
                    source_id=source_id,
                    status="failed",
                    title=title,
                    authority=authority,
                    source_url=source_url,
                    errors=[f"PyMuPDF: {exc}", f"pdfplumber: {exc2}"],
                )

        # --- OCR fallback for scanned / low-text pages ---
        ocr_used = False
        pages_for_cleaning: list[tuple[int, str]] = []
        low_quality_pages: list[int] = []

        if extraction and extraction.total_char_count < self.min_chars_for_text * extraction.page_count:
            # Entire document lacks extractable text -> OCR fallback
            if ocr_available(settings.tesseract_cmd):
                ocr_result = ocr_pdf(path, tesseract_cmd=settings.tesseract_cmd)
                ocr_used = True
                for page in ocr_result.pages:
                    pages_for_cleaning.append((page.page_number, page.text))
                    if page.low_quality:
                        low_quality_pages.append(page.page_number)
                if ocr_result.errors:
                    warnings.extend(ocr_result.errors)
                if ocr_result.total_char_count == 0:
                    warnings.append("OCR returned no text; document may be image-only or corrupt")
            else:
                warnings.append(
                    "Tesseract OCR unavailable; scanned PDF text may be incomplete"
                )
                # Use whatever PyMuPDF extracted (may be empty)
                for page in extraction.pages:
                    pages_for_cleaning.append((page.page_number, page.text))
        else:
            for page in extraction.pages:
                pages_for_cleaning.append((page.page_number, page.text))
                if page.extraction_method == "pdf_text_insufficient":
                    low_quality_pages.append(page.page_number)
                    if ocr_available(settings.tesseract_cmd):
                        # OCR this specific page
                        ocr_result = ocr_pdf(
                            path,
                            tesseract_cmd=settings.tesseract_cmd,
                        )
                        ocr_used = True
                        # OCR result covers all pages; pick this page
                        ocr_page = next(
                            (p for p in ocr_result.pages if p.page_number == page.page_number),
                            None,
                        )
                        if ocr_page and ocr_page.text:
                            pages_for_cleaning[-1] = (
                                page.page_number,
                                ocr_page.text,
                            )
                            if ocr_page.low_quality:
                                low_quality_pages.append(page.page_number)

        # --- Text cleaning ---
        cleaned_pages = clean_pages(pages_for_cleaning, remove_repeated=True)

        # --- Metadata extraction ---
        document_title = extraction.title if extraction else title
        document_title = document_title or title

        # --- Chunking ---
        chunks = chunk_document(
            source_id=source_id,
            document_title=document_title,
            authority=authority,
            source_url=source_url,
            retrieved_at=datetime.now(UTC).isoformat(),
            pages_text=cleaned_pages,
            extraction_method=("ocr" if ocr_used else "pdf_text"),
            verification_status=verification_status,
            target_tokens=settings.chunk_target_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
            id_prefix=id_prefix,
        )

        if not chunks:
            return self._failure(
                source_id=source_id,
                status="failed",
                title=document_title,
                authority=authority,
                source_url=source_url,
                errors=["No text could be extracted or chunked from the document"],
                content_hash=content_hash,
            )

        # --- Embedding generation ---
        texts = [chunk.text for chunk in chunks]
        try:
            embeddings = self.embedder.generate_embeddings(texts)
        except EmbeddingError as exc:
            return self._failure(
                source_id=source_id,
                status="failed",
                title=document_title,
                authority=authority,
                source_url=source_url,
                errors=[f"Embedding generation failed: {exc}"],
                content_hash=content_hash,
            )

        # --- FAISS indexing ---
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        try:
            self.index.add(embeddings, chunk_ids)
            self.index.save(settings.faiss_index_path)
        except Exception as exc:  # noqa: BLE001 - indexing failure
            errors.append(f"FAISS indexing failed: {exc}")
            chunks_indexed = 0
        else:
            chunks_indexed = len(chunks)

        # --- Metadata store ---
        records = [chunk.to_record() for chunk in chunks]
        try:
            self.metadata_store.write_records(records)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Metadata store write warning: {exc}")

        # --- Source registry update ---
        source_meta = SourceMetadata(
            source_id=source_id,
            title=document_title,
            authority=authority,
            source_url=source_url,
            document_type="pdf",
            topic=topic,
            content_hash=content_hash,
            file_path=str(path),
            page_count=extraction.page_count if extraction else 0,
            extraction_method=("ocr" if ocr_used else "pdf_text"),
            verification_status=verification_status,
        )
        self.registry.add(source_meta)

        status = "success"
        if errors:
            status = "partial"
        if low_quality_pages:
            warnings.append(
                f"Low-quality extraction on pages: {sorted(set(low_quality_pages))}"
            )

        return IngestResult(
            source_id=source_id,
            status=status,
            document_title=document_title,
            authority=authority,
            source_url=source_url,
            page_count=extraction.page_count if extraction else 0,
            chunks_created=len(chunks),
            chunks_indexed=chunks_indexed,
            extraction_method=("ocr" if ocr_used else "pdf_text"),
            verification_status=verification_status,
            content_hash=content_hash,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def _hash_bytes(data: bytes) -> str:
        import hashlib

        return hashlib.sha256(data).hexdigest()

    def _failure(
        self,
        *,
        source_id: str,
        status: str,
        title: str | None,
        authority: str,
        source_url: str,
        errors: list[str],
        content_hash: str | None = None,
        warnings: list[str] | None = None,
        ) -> IngestResult:
        return IngestResult(
            source_id=source_id,
            status=status,
            document_title=title,
            authority=authority,
            source_url=source_url,
            page_count=0,
            chunks_created=0,
            chunks_indexed=0,
            extraction_method="none",
            verification_status="pending",
            content_hash=content_hash,
            errors=errors,
            warnings=warnings or [],
        )


# ---------------------------------------------------------------------------
# Module-level convenience function matching the Person 1 integration contract.
# `from rag.ingestion.pipeline import ingest_document` works directly.
# ---------------------------------------------------------------------------

_default_pipeline: IngestionPipeline | None = None


def _get_default_pipeline() -> IngestionPipeline:
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = IngestionPipeline()
    return _default_pipeline


def ingest_document(
    file_path: str,
    metadata: dict,
) -> dict:
    """Ingest a single document using a default pipeline.

    Standalone convenience wrapper so the function can be imported directly:

        from rag.ingestion.pipeline import ingest_document

    Args:
        file_path: Path to the source document.
        metadata: Dictionary with source_id, title, authority, source_url,
            topic, and verification_status (all except file_path are optional
            with sensible defaults).

    Returns:
        IngestResult as a dict.
    """
    pipeline = _get_default_pipeline()
    result = pipeline.ingest_document(
        file_path=file_path,
        source_id=metadata.get("source_id", Path(file_path).stem.upper()),
        title=metadata.get("title", ""),
        authority=metadata.get("authority", ""),
        source_url=metadata.get("source_url", ""),
        topic=metadata.get("topic", ""),
        verification_status=metadata.get("verification_status", "pending"),
    )
    return result.to_dict()

