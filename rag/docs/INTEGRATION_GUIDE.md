# Integration Guide (Person 1 -> Person 2 RAG subsystem)

The RAG subsystem (`rag/`) is designed to be imported and used by
Person 1's FastAPI backend (`backend/`) without modifying internal
implementation. It has **no dependency on the backend's database or
application state**.

## Exact Python imports

```python
from rag.retrieval.engine import retrieve_guidance
from rag.agents.document_agent import process_document
from rag.document_matching.matcher import match_documents_to_requirements
```

`retrieve_guidance`, `process_document`, and `match_documents_to_requirements`
are plain synchronous Python functions (not FastAPI routes). Person 1
can call them directly from route handlers or services.

## A. Government information retrieval

```python
from rag.retrieval.engine import retrieve_guidance

result = retrieve_guidance(
    query="What is required for Udyam registration?",
    business_context={"business_type": "manufacturing", "state": "Karnataka"},
    top_k=5,
)
```

Returns a dict:

```json
{
  "query": "...",
  "results": [
    {
      "chunk_id": "...",
      "text": "...",
      "source_id": "...",
      "document_title": "...",
      "authority": "...",
      "page_number": 3,
      "section": "...",
      "source_url": "...",
      "similarity_score": 0.82,
      "verification_status": "verified",
      "retrieved_at": "...",
      "extraction_method": "pdf_text"
    }
  ],
  "citations": [ {...} ],
  "source_versions": [ {...} ],
  "retrieval_status": "success",
  "message": null
}
```

`retrieval_status` is one of: `success`, `conflicting_evidence`,
`insufficient_evidence`, `error`. On `insufficient_evidence`, `results`
and `citations` are empty and `message` explains why.

## B. Document processing

```python
from rag.agents.document_agent import process_document

result = process_document(
    file_path="/tmp/uploads/user.pdf",
    business_context={"business_name": "Example Biz"},
    service_type="gst_registration",
)
```

Returns a `ProcessDocumentResult` dict:

```json
{
  "document_id": "DOC_...",
  "document_type": "gst",
  "classification_confidence": 0.9,
  "classification_method": "rule_based",
  "extracted_fields": {
    "gstin": {"value": "22*******Z5", "confidence": 0.9, "method": "regex"},
    "pan_identifier": {"value": null, "confidence": 0.0, "method": "regex"}
  },
  "extraction_method": "pdf_text",
  "validation_status": "needs_review",
  "page_count": 1,
  "char_count": 1200,
  "extraction_errors": [],
  "warnings": []
}
```

Sensitive identifiers are masked in returned values.

## C. Document matching

```python
from rag.document_matching.matcher import match_documents_to_requirements

result = match_documents_to_requirements(
    extracted_documents=[{...}, {...}],
    required_documents=[
        {"name": "PAN card", "category": "pan", "mandatory": true},
        {"name": "Aadhaar card", "category": "aadhaar", "mandatory": true},
    ],
    service="gst_registration",
)
```

Returns a dict with `available_documents`, `missing_documents`,
`needs_review`, `incomplete_extraction`, `inconsistencies`,
`overall_status`, `checklist_coverage`.

## D. Source ingestion

```python
from rag.ingestion.pipeline import IngestionPipeline

pipeline = IngestionPipeline()
result = pipeline.ingest_document(
    file_path="/tmp/gov_source.pdf",
    source_id="UDYAM_001",
    title="Udyam Registration Guidelines",
    authority="Ministry of MSME",
    source_url="https://udyamregistration.gov.in/",
    topic="udyam_registration",
    verification_status="pending",
)
```

Returns an `IngestResult` dict with `status`, `chunks_created`,
`chunks_indexed`, `errors`, `warnings`.

## E. Source freshness / change detection

```python
from rag.sources.source_versioning import SourceVersioning
from rag.sources.source_metadata import SourceRegistry

versioning = SourceVersioning(SourceRegistry())
report = versioning.check_changes("UDYAM_001", "/tmp/updated_source.pdf")
# report.changed -> bool; report.action -> "reingest" | "none" | "ingest"
```

## Wiring into Person 1's agents as GovernmentKnowledgeProvider

Person 1's backend defines `GovernmentKnowledgeProvider` in
`backend/app/services/retrieval.py` and injects it into agents via
`backend/app/services/agents/agent_registry.py`.

The RAG subsystem provides a bridge:

```python
from rag.integration.knowledge_provider import RagKnowledgeProvider

provider = RagKnowledgeProvider()
```

`RagKnowledgeProvider.retrieve(query, *, user_id, conversation_id,
filters, limit)` returns `list[RetrievalSource]` (backend schema) when
the backend schema is importable, otherwise plain dicts. It never raises
on retrieval failure, so agents degrade gracefully.

Example wiring in `agent_registry.py`:

```python
from rag.integration.knowledge_provider import RagKnowledgeProvider

rag_provider = RagKnowledgeProvider()

registry = AgentRegistry(
    ai_service=ai_service,
    retrieval_provider=rag_provider,
    eligibility_evaluator=eligibility_evaluator,
)
```

## Dependencies

The `rag/` subsystem requires its own `requirements.txt` (see
`rag/requirements.txt`). Key additions beyond the backend:
`sentence-transformers`, `faiss-cpu`, `PyMuPDF`, `pdfplumber`,
`pytesseract`, `Pillow`. Tesseract OCR binary must be installed
separately for OCR fallback.

The backend stack (FastAPI, Pydantic, pydantic-settings, python-dotenv)
is reused; no duplication.

## Error handling

- All public functions return structured dicts; none raise on expected
  operational failure (missing file, empty index, OCR unavailable,
  insufficient evidence).
- Callers should inspect `status` / `retrieval_status` /
  `validation_status` fields and surface user-safe messages.
- The Document Agent wraps processing in try/except and returns a
  rejected/needs_review result rather than raising.

## How Person 1 integrates

1. Install `rag/requirements.txt` in the backend environment (or a
   shared environment).
2. Ensure `rag/` is on the Python path (repo root works).
3. Place real government PDFs in `rag/data/raw/` and run
   `python -m rag.scripts.build_index` to build the FAISS index.
4. Instantiate `RagKnowledgeProvider` and inject into
   `AgentRegistry` as `retrieval_provider`.
5. Call `retrieve_guidance`, `process_document`, and
   `match_documents_to_requirements` from route handlers as needed.
6. Run `python -m pytest rag/tests/` to verify.

## Initial knowledge base

The first build creates **illustrative placeholder** documents
(verification_status `unverified`) covering Udyam, GST, and MSME
schemes so retrieval can be demonstrated. These are **not verified
government content**. Replace `rag/data/raw/*.pdf` with authentic
government documents and re-run `build_index --rebuild` before relying
on retrieval output.
