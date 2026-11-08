# RAG Architecture

SarkarSetu AI RAG subsystem — document ingestion, embedding, vector
storage, semantic retrieval, citations, and source freshness tracking.

## Ingestion pipeline

```
source collection
  -> file validation (type, size, readability, encrypted PDFs)
  -> PDF extraction (PyMuPDF primary; pdfplumber fallback)
  -> OCR fallback (Tesseract) when text is insufficient/scanned
  -> text cleaning (whitespace, repeated headers/footers)
  -> metadata extraction (title, page count, authority, URL)
  -> heading-aware chunking (~500-800 tokens, 80-120 overlap)
  -> embedding generation (all-MiniLM-L6-v2, batched, normalized)
  -> FAISS indexing (IndexFlatIP, cosine via normalized vectors)
  -> source registry update (SHA-256 content hash)
```

Every chunk retains page-level traceability:

```json
{
  "chunk_id": "chunk_UDYAM_0001",
  "source_id": "UDYAM_001",
  "document_title": "Udyam Registration Guidelines",
  "authority": "Ministry of MSME",
  "page_number": 3,
  "section": "Requirements",
  "text": "...",
  "source_url": "https://udyamregistration.gov.in/",
  "retrieved_at": "2026-11-08T...",
  "extraction_method": "pdf_text",
  "verification_status": "verified"
}
```

### PDF validation (`rag/ingestion/pdf_extractor.py`)

- Rejects missing files, unsupported extensions, and files over
  `RAG_MAX_FILE_SIZE_MB`.
- Detects encrypted PDFs and requires a password; unsafe to open
  without one.
- Corrupted PDFs raise `PDFExtractionError`.

### OCR fallback (`rag/ingestion/ocr_processor.py`)

- When a page has fewer than `RAG_OCR_MIN_TEXT_CHARS` extractable
  characters, the page is rendered to an image (PyMuPDF pixmap at 200
  DPI) and sent to Tesseract.
- Records `extraction_method="ocr"` and flags low-quality pages
  (low char count or low Tesseract confidence).
- If the Tesseract binary is unavailable, OCR is reported as
  unavailable rather than treating the document as empty.

### Text cleaning (`rag/ingestion/text_cleaner.py`)

- Normalizes line breaks, collapses horizontal whitespace, collapses
  3+ blank lines.
- Removes repeated headers/footers (lines appearing on most pages).
- Preserves numbering, section headings, eligibility conditions, and
  tables where possible.

### Chunking (`rag/ingestion/chunker.py`)

- Heading-aware / paragraph-aware chunking.
- Configurable `chunk_target_tokens` (default 600) and
  `chunk_overlap_tokens` (default 100).
- Large paragraphs fall back to sentence, then word, splitting.
- Never splits a page boundary: each chunk carries `page_number`.

## Embedding architecture (`rag/embeddings/embedder.py`)

- Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- Loaded once as a module-level singleton (`_Embedder`).
- `generate_embedding(text)`, `generate_embeddings(texts)` (batched),
  `generate_query_embedding(query)`.
- All embeddings L2-normalized (cosine similarity via FAISS IndexFlatIP).
- Empty text returns a zero vector of the correct dimension.
- Dimension validated on every batch; model-loading failures surface
  as `EmbeddingError`.

## FAISS index (`rag/storage/faiss_index.py`)

- `faiss.IndexFlatIP` over normalized vectors = cosine similarity.
- Chunk ids stored in a parallel `_id_map` so every vector maps to its
  source chunk metadata.
- `add(embeddings, ids)`, `search(query, top_k)`, `rebuild()`,
  `save(path)`, `load(path)`.
- Persisted to `rag/data/indexes/knowledge_base.index` plus a `.ids`
  sidecar file.
- Supports incremental additions and full rebuilds (used when a source
  changes).

## Metadata store (`rag/storage/metadata_store.py`)

- Append-only JSONL store at `rag/data/metadata/chunks.jsonl`.
- One record per chunk, keyed by `chunk_id`, retaining all source and
  page metadata. Vectors are never stored without the id-to-source
  mapping.

## Retrieval workflow (`rag/retrieval/engine.py`)

`retrieve_guidance(query, business_context, top_k=5)`:

1. Validate query (non-empty).
2. Ensure FAISS index loaded (persistent load from disk).
3. Generate normalized query embedding.
4. Search FAISS top-k.
5. Fetch chunk metadata from the metadata store.
6. Build result records with `similarity_score`, page number, source
   URL, authority, verification status.
7. Build citations and source-version records.
8. Run evidence validation (sufficient/missing/unverified/low-conf).
9. Run conflict detection (contradictory thresholds across sources).
10. Return `retrieval_status` ∈ {success, conflicting_evidence,
    insufficient_evidence, error}.

Insufficient evidence returns:

```json
{
  "retrieval_status": "insufficient_evidence",
  "results": [],
  "citations": [],
  "message": "Insufficient verified information is available to answer this question."
}
```

## Citation generation (`rag/retrieval/citations.py`)

- One citation per retrieved chunk.
- Fields: citation_id, source_id, document_title, authority,
  page_number, section, source_url, retrieved_at,
  verification_status, similarity_score, excerpt.
- Only cites chunks actually retrieved; never fabricates URLs or page
  numbers.

## Evidence validation (`rag/validation/evidence_validator.py`)

Flags:
- Claims with no supporting retrieved passage (`missing_citations`).
- Unverified sources (`verification_status` pending/unverified).
- Low-confidence retrieval results (score < 0.4).

Does **not** treat LLM output as verification of government rules.

## Conflict detection (`rag/validation/conflict_detector.py`)

- Detects contradictory numeric threshold claims (turnover, GST
  threshold, exemption) across different sources on the same topic.
- Returns conflict descriptions with source page references.

## Source freshness & version tracking (`rag/sources/source_versioning.py`)

- `SourceMetadata`: source_id, title, authority, source_url,
  retrieved_at, published_at, version, verification_status, topic,
  content_hash, file_path, page_count, extraction_method, notes.
- `SourceRegistry`: persistent JSONL registry, lookup by source_id and
  source_url.
- `SourceVersioning.check_changes(source_id, new_file_path)`: computes
  SHA-256 of the new file, compares to stored `content_hash`,
  reports `changed`, `first_seen`, and a suggested `action`
  (ingest / reingest / none). Age alone never marks a source outdated.
- `freshness_report()`: aggregate counts across all sources.
- Re-ingestion preserves previous `retrieved_at` and updates hash +
  file info; affected chunks/embeddings are rebuilt when required.

## Source registry (`rag/sources/source_metadata.py`)

- Unique `source_id` per source (e.g. `UDYAM_001`).
- Full provenance: title, authority, URL, document type, retrieved
  timestamp, publication date, version, verification status, topic,
  content hash, file path, page count, extraction method, notes.
- No fabricated dates or versions; unknown values remain `null`.
