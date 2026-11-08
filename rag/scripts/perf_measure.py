"""Performance and deployment measurements for the RAG subsystem."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Users\Saatvika Reddy\SarkarSetu")

from rag.config.settings import ensure_directories, settings
from rag.embeddings.embedder import Embedder
from rag.ingestion.pdf_extractor import extract_pdf
from rag.ingestion.ocr_processor import ocr_pdf, ocr_available
from rag.retrieval.engine import RetrievalEngine
from rag.storage.faiss_index import FaissIndex


def elapsed(fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, (time.perf_counter() - t0) * 1000  # ms


def main():
    ensure_directories()
    print("=== RAG Performance / Deployment Measurements ===\n")

    # 1. Embedding model load time (first call loads the singleton)
    embedder = Embedder()
    _, load_ms = elapsed(lambda: embedder.load_embedding_model())
    print(f"1. Embedding model load time: {load_ms:.0f} ms (dimension={embedder.dimension})")

    # 2. Embedding generation (batch of 8 texts)
    texts = [
        "Udyam registration requirements",
        "GST registration threshold",
        "MSME subsidy scheme eligibility",
        "Aadhaar PAN documents",
        "business registration certificate",
        "address proof utility bill",
        "bank statement KYC",
        "Udyam MSME classification investment turnover",
    ] * 2
    _, emb_ms = elapsed(lambda: embedder.generate_embeddings(texts))
    print(f"2. Embedding generation (16 texts): {emb_ms:.0f} ms (~{emb_ms/16:.0f} ms/text)")

    # Single query embedding
    _, q_emb_ms = elapsed(lambda: embedder.generate_query_embedding("Udyam registration requirements"))
    print(f"   Single query embedding: {q_emb_ms:.0f} ms")

    # 3. PDF extraction time
    raw = Path(settings.rag_raw_dir)
    pdfs = list(raw.glob("*.pdf"))
    if pdfs:
        p = pdfs[0]
        _, ext_ms = elapsed(lambda: extract_pdf(p))
        print(f"3. PDF extraction ({p.name}): {ext_ms:.0f} ms")
    else:
        print("3. PDF extraction: no PDFs in raw dir (skipped)")

    # 4. OCR processing time (only if Tesseract available)
    if ocr_available() and pdfs:
        _, ocr_ms = elapsed(lambda: ocr_pdf(pdfs[0]))
        print(f"4. OCR processing ({pdfs[0].name}): {ocr_ms:.0f} ms (ocr_available=True)")
    else:
        print(f"4. OCR processing: skipped (ocr_available={ocr_available()})")

    # 5. FAISS index load time
    index = FaissIndex()
    idx_path = settings.faiss_index_path
    if idx_path.exists():
        _, load_idx_ms = elapsed(lambda: index.load(idx_path))
        print(
            f"5. FAISS index load time: {load_idx_ms:.0f} ms "
            f"(vectors={index.count}, dimension={index.dimension})"
        )
    else:
        print("5. FAISS index load: no index file (skipped)")

    # 6. Retrieval latency (warm index, model loaded)
    engine = RetrievalEngine()
    queries = [
        "What is required for Udyam registration?",
        "GST registration threshold for goods suppliers",
        "MSME classification investment turnover",
    ]
    for q in queries:
        _, ret_ms = elapsed(lambda q=q: engine.retrieve_guidance(q, top_k=5))
        print(f"6. Retrieval latency ('{q[:35]}...'): {ret_ms:.0f} ms")

    # 7. Index persistence / metadata consistency
    print("\n7. Index persistence & metadata consistency:")
    print(f"   FAISS index file: {idx_path.exists()} ({index.count} vectors)")
    print(f"   Metadata store: {settings.metadata_store_path.exists()}")
    print(f"   Source registry: {settings.source_registry_path.exists()}")
    print(f"   Index on-disk size: {idx_path.stat().st_size / 1024:.0f} KB" if idx_path.exists() else "   n/a")

    # 8. Env var handling
    print("\n8. Environment variable handling:")
    for key in [
        "RAG_EMBEDDING_MODEL",
        "RAG_CHUNK_TARGET_TOKENS",
        "RAG_DEFAULT_TOP_K",
        "RAG_MAX_FILE_SIZE_MB",
        "RAG_TESSERACT_CMD",
    ]:
        print(f"   {key} = {os.environ.get(key, settings.__dict__.get(key.lower(), '<default>'))}")


if __name__ == "__main__":
    main()
