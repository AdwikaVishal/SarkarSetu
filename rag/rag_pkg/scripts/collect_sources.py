"""Collect authentic official government sources.

Downloads official government pages, extracts readable text, records full
provenance metadata (URL, authority, title, retrieval date, SHA-256 hash),
creates a text-based PDF for indexing, and registers each source with
verification_status="pending" (pending human review — never auto-verified).

Usage:
    python -m rag.scripts.collect_sources
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup

from rag.config.settings import ensure_directories, settings
from rag.config.logging_config import configure_logging, get_logger
from rag.ingestion.pipeline import IngestionPipeline
from rag.sources.source_metadata import SourceMetadata, SourceRegistry
from rag.sources.source_versioning import SourceVersioning

logger = get_logger("collect_sources")

# Official government sources to collect. Each entry: source_id, url,
# issuing authority, topic.
SOURCES = [
    {
        "source_id": "UDYAM_001",
        "url": "https://udyamregistration.gov.in/",
        "authority": "Ministry of MSME, Government of India",
        "topic": "udyam_registration",
    },
    {
        "source_id": "MSME_001",
        "url": "https://msme.gov.in/",
        "authority": "Ministry of MSME, Government of India",
        "topic": "msme_classification",
    },
    {
        "source_id": "GST_001",
        "url": "https://www.gst.gov.in/",
        "authority": "Central Board of Indirect Taxes & Customs (CBIC) / GSTN",
        "topic": "gst_registration",
    },
    {
        "source_id": "MYSCHEME_001",
        "url": "https://www.myscheme.gov.in/",
        "authority": "Ministry of Electronics and Information Technology (MeitY), Government of India",
        "topic": "msme_schemes",
    },
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_text(html: str) -> tuple[str, str]:
    """Return (title, main_text) extracted from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style/nav/footer noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(" ", strip=True)

    # Get main text, collapse whitespace
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return title, text.strip()


def _build_pdf(title: str, text: str, source_url: str, output_path: Path) -> int:
    """Create a text-based PDF from extracted content. Returns page count."""
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    # Title
    page.insert_text((72, y), title or "Government Source Document", fontsize=12)
    y += 24
    page.insert_text((72, y), f"Source: {source_url}", fontsize=9)
    y += 20
    # Body, wrapped at ~110 chars
    for line in text.split("\n"):
        if not line.strip():
            y += 10
            continue
        wrapped = [line[i : i + 100] for i in range(0, len(line), 100)]
        for chunk in wrapped:
            if y > 740:
                page = doc.new_page()
                y = 72
            page.insert_text((72, y), chunk, fontsize=9)
            y += 11
        y += 4
    doc.save(str(output_path))
    doc.close()
    return 1  # page count approximate; re-open to get exact


def collect_source(
    *,
    source_id: str,
    url: str,
    authority: str,
    topic: str,
    raw_dir: Path,
    pipeline: IngestionPipeline,
    registry: SourceRegistry,
    versioning: SourceVersioning,
) -> dict[str, Any]:
    """Collect a single official source and register + index it."""
    result: dict[str, Any] = {
        "source_id": source_id,
        "url": url,
        "status": "failed",
        "title": None,
        "retrieved_at": None,
        "published_at": None,
        "version": None,
        "content_hash": None,
        "verification_status": "pending",
        "error": None,
    }

    try:
        resp = requests.get(
            url, timeout=30, headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()
        html = resp.text
        result["retrieved_at"] = datetime.now(UTC).isoformat()
        result["content_hash"] = _sha256_bytes(html.encode("utf-8"))

        title, text = _extract_text(html)
        result["title"] = title or ""

        # Save raw HTML
        raw_path = raw_dir / f"{source_id}.html"
        raw_path.write_text(html, encoding="utf-8")

        # Build a text-based PDF for indexing
        pdf_path = raw_dir / f"{source_id}.pdf"
        page_count = _build_pdf(title or source_id, text, url, pdf_path)

        # Re-open PDF for exact page count
        doc = fitz.open(str(pdf_path))
        page_count = doc.page_count
        doc.close()

        # Register source (pending verification)
        source_meta = SourceMetadata(
            source_id=source_id,
            title=title or source_id,
            authority=authority,
            source_url=url,
            document_type="html",
            topic=topic,
            content_hash=result["content_hash"],
            file_path=str(pdf_path),
            page_count=page_count,
            extraction_method="pdf_text",
            verification_status="pending",
            notes=(
                "Fetched from official government website. "
                "Pending human verification before user-facing use."
            ),
        )
        registry.add(source_meta)

        # Ingest into the RAG index
        ingest_result = pipeline.ingest_document(
            file_path=str(pdf_path),
            source_id=source_id,
            title=title or source_id,
            authority=authority,
            source_url=url,
            topic=topic,
            verification_status="pending",
        )

        result.update(
            status="collected",
            page_count=page_count,
            chunks_created=ingest_result.chunks_created,
            chunks_indexed=ingest_result.chunks_indexed,
            errors=ingest_result.errors,
            warnings=ingest_result.warnings,
        )
        logger.info(
            "Collected %s (%s) -> %d chunks indexed", source_id, url, ingest_result.chunks_indexed
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to collect %s", url)
        result["status"] = "failed"
        result["error"] = str(exc)

    return result


def main() -> None:
    configure_logging()
    ensure_directories()
    raw_dir = Path(settings.rag_raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    registry = SourceRegistry()
    versioning = SourceVersioning(registry=registry)
    pipeline = IngestionPipeline(registry=registry, versioning=versioning)

    results = []
    for src in SOURCES:
        results.append(
            collect_source(
                source_id=src["source_id"],
                url=src["url"],
                authority=src["authority"],
                topic=src["topic"],
                raw_dir=raw_dir,
                pipeline=pipeline,
                registry=registry,
                versioning=versioning,
            )
        )

    print("\n=== Source Collection Summary ===")
    for r in results:
        print(
            f"[{r['source_id']}] {r['status']} | {r['url']}"
            + (f" | title={r['title'][:60]}" if r.get("title") else "")
            + (f" | chunks_indexed={r.get('chunks_indexed')}" if r.get("chunks_indexed") is not None else "")
            + (f" | error={r['error']}" if r.get("error") else "")
        )

    total_indexed = sum(r.get("chunks_indexed") or 0 for r in results)
    collected = sum(1 for r in results if r["status"] == "collected")
    print(f"\nCollected: {collected}/{len(SOURCES)}")
    print(f"Total chunks indexed: {total_indexed}")
    print("\nVerification status for all collected sources: pending (awaiting human review).")


if __name__ == "__main__":
    main()
