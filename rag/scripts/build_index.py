"""Build (rebuild) the FAISS knowledge base index from source documents.

Usage:
    python -m scripts.build_index [--raw-dir rag/data/raw] [--rebuild]

If no source PDFs exist, creates clearly-illustrative placeholder
documents (marked verification_status='unverified') so the retrieval
demo can run. Real government PDFs should be placed in rag/data/raw/
and re-ingested.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz  # PyMuPDF

from rag.config.settings import ensure_directories, settings
from rag.config.logging_config import configure_logging, get_logger
from rag.ingestion.pipeline import IngestionPipeline
from rag.storage.faiss_index import FaissIndex
from rag.storage.metadata_store import ChunkMetadataStore
from rag.sources.source_metadata import SourceRegistry
from rag.sources.source_versioning import SourceVersioning

logger = get_logger("build_index")

ILLUSTRATIVE_DOCS = {
    "udyam_registration_placeholder": (
        "Udyam Registration Guidelines (Illustrative Placeholder)\n\n"
        "Udyam Registration is the online registration process for Micro, "
        "Small and Medium Enterprises (MSME) in India, administered by the "
        "Ministry of MSMS. This is a PLACEHOLDER document pending collection "
        "of the official Udyam registration guidelines from "
        "https://udyamregistration.gov.in/.\n\n"
        "Classification:\n"
        "Micro enterprise: investment in plant and machinery or equipment "
        "not more than Rs 1 crore and annual turnover not more than Rs 5 "
        "crore.\n"
        "Small enterprise: investment not more than Rs 10 crore and annual "
        "turnover not more than Rs 50 crore.\n"
        "Medium enterprise: investment not more than Rs 50 crore and annual "
        "turnover not more than Rs 250 crore.\n\n"
        "Requirements:\n"
        "Aadhaar number of the proprietor/partner/director.\n"
        "PAN of the business and the applicant.\n"
        "No registration fee.\n"
        "Self-declaration based; no documents required to be uploaded.\n\n"
        "Official portal: https://udyamregistration.gov.in/ (placeholder - "
        "verify on official site)\n"
    ),
    "gst_registration_placeholder": (
        "GST Registration Guidelines (Illustrative Placeholder)\n\n"
        "Goods and Services Tax (GST) registration is required for suppliers "
        "whose aggregate turnover exceeds the prescribed threshold. This is a "
        "PLACEHOLDER document pending collection of official GST guidelines "
        "from https://www.gst.gov.in/.\n\n"
        "Thresholds:\n"
        "Goods suppliers: Rs 40 lakh (Rs 20 lakh for special category "
        "states).\n"
        "Service providers: Rs 20 lakh (Rs 10 lakh for special category "
        "states).\n"
        "Inter-state supply and e-commerce operators: registration required "
        "irrespective of threshold.\n\n"
        "Requirements:\n"
        "PAN of the applicant.\n"
        "Aadhaar number.\n"
        "Proof of business registration / incorporation.\n"
        "Address proof and bank account details.\n"
        "Digital signature (DSC) for companies and LLPs.\n\n"
        "Official portal: https://www.gst.gov.in/ (placeholder - verify on "
        "official site)\n"
    ),
    "msme_schemes_placeholder": (
        "MSME Support Schemes (Illustrative Placeholder)\n\n"
        "This is a PLACEHOLDER document listing illustrative MSME schemes "
        "pending collection from https://www.myscheme.gov.in/ and "
        "https://www.startupindia.gov.in/.\n\n"
        "Illustrative schemes:\n"
        "- Credit Guarantee Fund Trust for Micro and Small Enterprises "
        "(CGTMSE): collateral-free credit.\n"
        "- Prime Minister's Employment Generation Programme (PMEGP): "
        "subsidy for new micro enterprises.\n"
        "- Credit Linked Capital Subsidy Scheme (CLCSS): technology "
        "upgradation subsidy.\n\n"
        "Eligibility conditions vary by scheme and must be verified on the "
        "official scheme portal before application.\n\n"
        "Official portals: https://www.myscheme.gov.in/, "
        "https://www.startupindia.gov.in/ (placeholder - verify on official "
        "site)\n"
    ),
}


def create_illustrative_placeholders(raw_dir: Path) -> None:
    """Create illustrative placeholder PDFs when none exist."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    existing = list(raw_dir.glob("*.pdf"))
    if existing:
        return
    for name, text in ILLUSTRATIVE_DOCS.items():
        pdf_path = raw_dir / f"{name}.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=10)
        doc.save(str(pdf_path))
        doc.close()
        logger.info("Created illustrative placeholder %s", pdf_path.name)
    logger.warning(
        "Created illustrative placeholder documents. These are NOT verified "
        "government content. Replace them with real government PDFs and "
        "re-ingest."
    )


def build_index(*, raw_dir: str | Path, rebuild: bool = False) -> dict:
    raw_dir = Path(raw_dir)
    ensure_directories()

    create_illustrative_placeholders(raw_dir)

    registry = SourceRegistry()
    versioning = SourceVersioning(registry=registry)
    index = FaissIndex()
    store = ChunkMetadataStore()

    if rebuild:
        # Clear existing index and metadata
        index_path = settings.faiss_index_path
        index_path.parent.mkdir(parents=True, exist_ok=True)
        store.clear()
        index = FaissIndex()
        # Clear registry (rebuild from scratch)
        registry_path = settings.source_registry_path
        if registry_path.exists():
            registry_path.unlink()
        registry._loaded = False
        registry._sources = {}
        registry._by_url = {}

    pipeline = IngestionPipeline(
        registry=registry,
        versioning=versioning,
        index=index,
        metadata_store=store,
    )

    pdfs = sorted(raw_dir.glob("*.pdf"))
    summaries = []
    for pdf in pdfs:
        source_id = pdf.stem.upper().replace(" ", "_")
        source_id = "".join(c for c in source_id if c.isalnum() or c == "_")
        status = "unverified" if "placeholder" in pdf.stem.lower() else "pending"
        result = pipeline.ingest_document(
            file_path=str(pdf),
            source_id=source_id,
            title=pdf.stem.replace("_", " ").title(),
            authority="Government of India",
            source_url="https://www.india.gov.in/ illustrative-placeholder",
            topic="government_guidance",
            verification_status=status,
        )
        summaries.append(result.to_dict())
        logger.info(
            "Indexed %s -> %s chunks=%d indexed=%d",
            pdf.name, result.status, result.chunks_created,
            result.chunks_indexed,
        )

    return {
        "indexed_documents": len(pdfs),
        "total_vectors": index.count,
        "total_chunks": store.count(),
        "documents": summaries,
    }


def main() -> None:
    configure_logging()
    ensure_directories()
    parser = argparse.ArgumentParser(
        description="Build or rebuild the FAISS knowledge base index"
    )
    parser.add_argument(
        "--raw-dir", default="rag/data/raw",
        help="Directory containing source PDFs"
    )
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Rebuild the index from scratch"
    )
    args = parser.parse_args()

    summary = build_index(raw_dir=args.raw_dir, rebuild=args.rebuild)
    print("Index build summary:")
    print(f"  Documents indexed: {summary['indexed_documents']}")
    print(f"  Total vectors: {summary['total_vectors']}")
    print(f"  Total chunks: {summary['total_chunks']}")
    for doc in summary["documents"]:
        print(f"  - {doc['source_id']}: {doc['chunks_created']} chunks, "
              f"{doc['chunks_indexed']} indexed")


if __name__ == "__main__":
    main()
