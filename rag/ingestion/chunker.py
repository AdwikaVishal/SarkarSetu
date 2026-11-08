"""Intelligent, heading-aware text chunking.

Produces chunks of roughly 500-800 tokens with configurable overlap,
preserving page-level traceability and source metadata. Important
conditions and headings are not split unnecessarily.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from rag.config.logging_config import get_logger

logger = get_logger("chunker")


@dataclass
class Chunk:
    """A single document chunk with full source traceability."""

    chunk_id: str
    source_id: str
    document_title: str
    authority: str
    page_number: int
    section: str
    text: str
    source_url: str
    retrieved_at: str
    extraction_method: str
    verification_status: str
    token_count: int
    chunk_index: int

    def to_record(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_id": self.source_id,
            "document_title": self.document_title,
            "authority": self.authority,
            "page_number": self.page_number,
            "section": self.section,
            "text": self.text,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at,
            "extraction_method": self.extraction_method,
            "verification_status": self.verification_status,
            "token_count": self.token_count,
            "chunk_index": self.chunk_index,
        }


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 tokens per word for English.

    Used purely for sizing chunks; the embedding model does its own
    tokenization.
    """
    if not text:
        return 0
    words = text.split()
    return max(1, int(len(words) * 0.75))


_HEADING_PATTERNS = [
    re.compile(r"^(?P<num>\d+(?:\.\d+)*)\s+(?P<title>.+)$", re.MULTILINE),
    re.compile(r"^[A-Z][A-Z0-9 ,&'\-]{4,}$", re.MULTILINE),
    re.compile(r"^(?P<num>[IVXLC]+\.)\s+(?P<title>.+)$", re.MULTILINE),
]


def _detect_section(text: str) -> str:
    """Detect a heading/section name at the start of a text block."""
    for pattern in _HEADING_PATTERNS:
        match = pattern.search(text)
        if match:
            groupdict = match.groupdict()
            title = groupdict.get("title") or match.group(0) or ""
            return title.strip()[:80]
    return ""


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on blank lines."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs


def chunk_document(
    *,
    source_id: str,
    document_title: str,
    authority: str,
    source_url: str,
    retrieved_at: str,
    pages_text: list[tuple[int, str]],
    extraction_method: str = "pdf_text",
    verification_status: str = "verified",
    target_tokens: int = 600,
    overlap_tokens: int = 100,
    id_prefix: str = "chunk",
) -> list[Chunk]:
    """Chunk a document page-by-page, heading-aware.

    Args:
        source_id: Source identifier.
        document_title: Document title.
        authority: Issuing authority.
        source_url: Official source URL.
        retrieved_at: ISO retrieval timestamp.
        pages_text: List of (page_number, cleaned_text).
        extraction_method: How text was extracted.
        verification_status: Source verification status.
        target_tokens: Target chunk size in tokens.
        overlap_tokens: Overlap between chunks in tokens.
        id_prefix: Prefix for generated chunk ids.

    Returns:
        List of Chunk objects with page-level traceability.
    """
    chunks: list[Chunk] = []
    counter = 0

    for page_number, text in pages_text:
        if not text or not text.strip():
            continue

        section = _detect_section(text)
        page_chunks = _chunk_text(
            text=text,
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens,
        )

        for chunk_text in page_chunks:
            counter += 1
            chunk_id = f"{id_prefix}_{source_id}_{counter:04d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    document_title=document_title,
                    authority=authority,
                    page_number=page_number,
                    section=section,
                    text=chunk_text,
                    source_url=source_url,
                    retrieved_at=retrieved_at,
                    extraction_method=extraction_method,
                    verification_status=verification_status,
                    token_count=estimate_tokens(chunk_text),
                    chunk_index=counter,
                )
            )

    logger.info(
        "Chunked document %s into %d chunks across %d pages",
        source_id,
        len(chunks),
        len(pages_text),
    )
    return chunks


def _chunk_text(
    text: str,
    *,
    target_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Split a single page's text into overlapping chunks.

    Prefers paragraph boundaries; falls back to sentence/word boundaries
    when a paragraph exceeds the target size.
    """
    paragraphs = _split_paragraphs(text)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    def flush() -> None:
        nonlocal current, current_tokens
        if current:
            chunks.append("\n\n".join(current))
        current = []
        current_tokens = 0

    for paragraph in paragraphs:
        para_tokens = estimate_tokens(paragraph)
        if para_tokens == 0:
            continue

        if para_tokens > target_tokens:
            # Paragraph too large: split by sentences, then words
            flush()
            chunks.extend(_split_large_paragraph(paragraph, target_tokens, overlap_tokens))
            continue

        if current_tokens + para_tokens > target_tokens and current:
            flush()
            # Start new chunk with overlap from previous tail
            overlap = _take_overlap(chunks[-1] if chunks else "", overlap_tokens)
            if overlap:
                current = [overlap]
                current_tokens = estimate_tokens(overlap)

        current.append(paragraph)
        current_tokens += para_tokens

    flush()
    return chunks


def _take_overlap(text: str, overlap_tokens: int) -> str:
    """Take the trailing `overlap_tokens` worth of words from text."""
    if overlap_tokens <= 0 or not text:
        return ""
    words = text.split()
    target_words = int(overlap_tokens / 0.75)
    if target_words <= 0:
        return ""
    return " ".join(words[-target_words:])


def _split_large_paragraph(
    paragraph: str,
    target_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Split an oversized paragraph by sentence, then by words."""
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        stokens = estimate_tokens(sentence)
        if current_tokens + stokens > target_tokens and current:
            chunks.append(" ".join(current))
            overlap = _take_overlap(" ".join(current), overlap_tokens)
            current = [overlap] if overlap else []
            current_tokens = estimate_tokens(" ".join(current)) if current else 0
        current.append(sentence)
        current_tokens += stokens

    if current:
        chunks.append(" ".join(current))

    # Final fallback: word-based split for any remaining oversized chunk
    final: list[str] = []
    for chunk in chunks:
        if estimate_tokens(chunk) <= target_tokens:
            final.append(chunk)
        else:
            final.extend(_split_by_words(chunk, target_tokens, overlap_tokens))
    return final


def _split_by_words(
    text: str,
    target_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    words = text.split()
    target_words = max(1, int(target_tokens / 0.75))
    overlap_words = max(0, int(overlap_tokens / 0.75))
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + target_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap_words
        if start <= 0:
            start = end
    return chunks
