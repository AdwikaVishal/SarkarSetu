# SarkarSetu AI — RAG & Document Intelligence Subsystem (Person 2)

AI-powered retrieval-augmented generation (RAG), document processing, and
document intelligence for Indian government services guidance.

This is **Person 2's** subsystem. It integrates with Person 1's FastAPI
backend (`backend/`) through clean, dependency-free Python interfaces.

## Responsibilities

1. Official government source research & registry
2. Government document collection & metadata
3. PDF text extraction (PyMuPDF primary, pdfplumber fallback)
4. OCR for scanned PDFs (Tesseract, graceful degradation)
5. Text cleaning & normalization
6. Intelligent text chunking with page-level traceability
7. Embedding generation (sentence-transformers/all-MiniLM-L6-v2)
8. FAISS vector indexing & persistence
9. Semantic retrieval
10. Source metadata & citation generation
11. Source version & freshness tracking (SHA-256)
12. Document classification
13. Document field extraction
14. Document-to-requirement matching
15. Reusable Document Agent

## Module structure

```
rag/
├── __init__.py
├── config/
│   ├── settings.py          # Pydantic settings (env-driven)
│   └── logging_config.py    # Structured logging
├── sources/
│   ├── source_metadata.py   # SourceMetadata model + SourceRegistry
│   ├── source_versioning.py # SHA-256 change detection + freshness report
│   └── research_report.py   # Source research report
├── ingestion/
│   ├── pdf_extractor.py     # PyMuPDF + pdfplumber extraction
│   ├── ocr_processor.py     # Tesseract OCR fallback
│   ├── text_cleaner.py      # Text cleaning / header-footer removal
│   ├── chunker.py           # Heading-aware chunking
│   └── pipeline.py          # Full ingestion pipeline
├── embeddings/
│   └── embedder.py          # Singleton sentence-transformers embedder
├── storage/
│   ├── faiss_index.py       # FAISS CPU index + persistence
│   └── metadata_store.py    # JSONL chunk metadata store
├── retrieval/
│   ├── engine.py            # retrieve_guidance()
│   ├── ranking.py           # Result ranking / filtering
│   └── citations.py         # Citation generation
├── validation/
│   ├── evidence_validator.py
│   └── conflict_detector.py
├── documents/
│   ├── upload_validator.py  # Safe upload validation
│   ├── classifier.py        # Rule-based document classification
│   ├── field_extractor.py   # Field extraction (PAN/GSTIN/etc.)
│   └── schemas.py           # Pydantic schemas
├── document_matching/
│   └── matcher.py           # match_documents_to_requirements()
├── agents/
│   └── document_agent.py    # process_document()
├── integration/
│   └── knowledge_provider.py # GovernmentKnowledgeProvider bridge
├── scripts/
│   ├── ingest_sources.py
│   ├── build_index.py
│   └── test_retrieval.py
├── data/
│   ├── raw/                 # Source PDFs
│   ├── processed/
│   ├── metadata/            # Registry + chunk metadata
│   └── indexes/             # FAISS index
└── tests/                   # 50 unit tests
```

## Installation

```bash
# From the repository root
cd rag

# Create a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Environment setup

Copy a `.env` into `rag/` (or set environment variables):

```ini
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_CHUNK_TARGET_TOKENS=600
RAG_CHUNK_OVERLAP_TOKENS=100
RAG_DEFAULT_TOP_K=5
RAG_MIN_SIMILARITY_SCORE=0.30
RAG_MAX_FILE_SIZE_MB=50
RAG_ALLOWED_EXTENSIONS=.pdf
RAG_LOG_LEVEL=INFO
# Only needed if Tesseract is not on PATH:
# RAG_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

> Tesseract OCR binary must be installed separately for OCR fallback to
> work. The subsystem degrades gracefully (scanned PDFs are flagged)
> when Tesseract is unavailable.

## Running ingestion

Build the knowledge base index from PDFs in `rag/data/raw/`:

```bash
# Create illustrative placeholders + build index (first run downloads ~100 MB model)
python -m rag.scripts.build_index --raw-dir rag/data/raw

# Rebuild from scratch
python -m rag.scripts.build_index --raw-dir rag/data/raw --rebuild

# Ingest a directory of government PDFs
python -m rag.scripts.ingest_sources --raw-dir rag/data/raw
```

## Running retrieval

```bash
python -m rag.scripts.test_retrieval \
  --query "What is required for Udyam registration?" \
  --top-k 5
```

## Processing user documents (Document Agent)

```python
from rag.agents.document_agent import process_document

result = process_document(
    file_path="/tmp/uploaded.pdf",
    business_context={"business_type": "manufacturing"},
    service_type="gst_registration",
)
print(result)
```

## Running tests

```bash
# From the repository root
python -m pytest rag/tests/ -v

# With coverage
python -m pytest rag/tests/ --cov=rag --cov-report=term-missing
```

## Integration with Person 1's backend

Import the stable interfaces:

```python
from rag.retrieval.engine import retrieve_guidance
from rag.agents.document_agent import process_document
from rag.document_matching.matcher import match_documents_to_requirements
```

To wire the RAG layer into Person 1's agents as a
`GovernmentKnowledgeProvider`:

```python
from rag.integration.knowledge_provider import RagKnowledgeProvider

provider = RagKnowledgeProvider()
# Pass `retrieval_provider=provider` when constructing DocumentAgent,
# DiscoveryAgent, ComplianceAgent in backend/app/services/agents/agent_registry.py
```

See `docs/INTEGRATION_GUIDE.md` for the full contract, schemas, and an
example wiring into `agent_registry.py`.

## Security & privacy

- File size and extension validation on upload
- Safe (sanitized) filenames; unique document IDs
- Sensitive identifiers (PAN, GSTIN, Aadhaar) masked in logs/demo output
- No document contents logged
- No automatic submission to government portals
- Uploaded documents and retrieved content treated as untrusted input

## Known limitations

- The initial knowledge base uses illustrative placeholder documents
  (verification_status `unverified`). Real government PDFs must be placed
  in `rag/data/raw/` and re-ingested before production use.
- Tesseract OCR binary is required for scanned-PDF OCR; absent Tesseract
  degrades gracefully.
- Document classification and field extraction are rule-based/regex; an
  LLM may be added later for ambiguous cases but must not fabricate
  fields.

## License

Proprietary - All rights reserved.
