"""Ingest government source PDFs into the RAG index.

Usage:
    python -m scripts.ingest_sources [--raw-dir rag/data/raw]

Reads PDF files from the raw directory, ingests each via the
IngestionPipeline, and prints a summary. Source registry and FAISS
index are updated persistently.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag.config.settings import ensure_directories
from rag.config.logging_config import configure_logging, get_logger
from rag.ingestion.pipeline import IngestionPipeline
from rag.storage.faiss_index import FaissIndex
from rag.storage.metadata_store import ChunkMetadataStore
from rag.sources.source_metadata import SourceRegistry
from rag.sources.source_versioning import SourceVersioning

logger = get_logger("ingest_sources")


def ingest_directory(
    *,
    raw_dir: str | Path,
    topic: str = "government_guidance",
    verification_status: str = "pending",
) -> list[dict]:
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        logger.warning("Raw directory does not exist: %s", raw_dir)
        return []

    registry = SourceRegistry()
    versioning = SourceVersioning(registry=registry)
    embedder = None  # lazy singleton
    index = FaissIndex()
    store = ChunkMetadataStore()
    pipeline = IngestionPipeline(
        registry=registry,
        versioning=versioning,
        index=index,
        metadata_store=store,
    )

    pdfs = sorted(raw_dir.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDF files found in %s", raw_dir)
        return []

    results = []
    for pdf in pdfs:
        source_id = pdf.stem.upper().replace(" ", "_")
        source_id = "".join(c for c in source_id if c.isalnum() or c == "_")
        title = pdf.stem.replace("_", " ").title()
        result = pipeline.ingest_document(
            file_path=str(pdf),
            source_id=source_id,
            title=title,
            authority="Government of India (illustrative)",
            source_url=f"https://www.india.gov.in/ illustrative-placeholder",
            topic=topic,
            verification_status=verification_status,
        )
        results.append(result.to_dict())
        logger.info(
            "Ingested %s -> status=%s chunks=%d",
            pdf.name, result.status, result.chunks_created
        )
        if result.errors:
            logger.error("Errors for %s: %s", pdf.name, result.errors)

    return results


def main() -> None:
    configure_logging()
    ensure_directories()
    parser = argparse.ArgumentParser(
        description="Ingest government source PDFs into the RAG index"
    )
    parser.add_argument(
        "--raw-dir", default="rag/data/raw",
        help="Directory containing source PDFs"
    )
    parser.add_argument(
        "--topic", default="government_guidance",
        help="Topic tag for ingested sources"
    )
    parser.add_argument(
        "--verification-status", default="pending",
        help="Verification status to assign to ingested sources"
    )
    args = parser.parse_args()

    results = ingest_directory(
        raw_dir=args.raw_dir,
        topic=args.topic,
        verification_status=args.verification_status,
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
