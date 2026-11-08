# Document Intelligence

Document processing for files uploaded by users. This is **separate from**
government document ingestion: it handles user-uploaded PDFs through
validation, classification, field extraction, and requirement matching.

## Upload pipeline (`rag/documents/upload_validator.py`)

```
uploaded file
  -> validate file type (.pdf only)
  -> validate file size (<= RAG_MAX_FILE_SIZE_MB)
  -> reject empty / corrupted / unreadable PDFs (PyMuPDF integrity check)
  -> generate unique document id (DOC_<hex>)
  -> safe filename (sanitize, neutralize traversal)
  -> content hash (SHA-256)
  -> return ValidatedUpload (never log document contents)
```

## PDF extraction & OCR

Uses the same `rag/ingestion/pdf_extractor.py` and
`rag/ingestion/ocr_processor.py` as the government ingestion pipeline,
with OCR fallback for scanned uploads and graceful degradation when
Tesseract is unavailable.

## Classification (`rag/documents/classifier.py`)

Hybrid rule-based classification over extracted text:

| Category | Keyword signals |
|---|---|
| aadhaar | aadhaar, uidai, enrolment, virtual id |
| pan | permanent account number, pan, income tax |
| gst | gstin, goods and services tax, gst registration |
| udyam | udyam, msme, udyam registration |
| business_registration | certificate of incorporation, partnership deed, roc, llp |
| address_proof | utility/electricity/water/telephone bill, rent agreement |
| bank_statement | bank statement, passbook, ifsc, account number |

- Weights per category; best match wins.
- Confidence capped at 1.0; below threshold → `other/unknown` with
  confidence 0.0.
- Never assumes every PDF is a known category; `other/unknown` is a
  valid outcome.
- Optional LLM-assisted classification can be added later for ambiguous
  documents.

## Field extraction (`rag/documents/field_extractor.py`)

Extracts, where present:

- document_type, name, business_name, address, pan_identifier, gstin,
  registration_number, issue_date, expiry_date.

Each field returns `{value, confidence, method}`. Missing fields return
`value: null, confidence: 0.0` — **never invented**. Sensitive values
(PAN, GSTIN, Aadhaar, long account numbers) are masked in ordinary
outputs via `mask_sensitive()`.

## Requirement matching (`rag/document_matching/matcher.py`)

`match_documents_to_requirements(extracted_documents, required_documents, service)`:

- Indexes extracted documents by category.
- For each required document, picks the highest-confidence matching
  uploaded document.
- Classifies as: available / missing / needs_review /
  incomplete_extraction.
- `overall_status` ∈ {complete, incomplete, needs_review}.
- `checklist_coverage` = available / total.

This is a **preparation and completeness check only** — not official
verification, and never claims a document is legally accepted by a
government portal.

## Document Agent (`rag/agents/document_agent.py`)

`process_document(file_path, business_context, service_type) -> dict`:

1. Upload validation (`validate_upload`).
2. Classification (`classify_document`).
3. Field extraction (`extract_fields`).
4. Returns a `ProcessDocumentResult` dict:
   - document_id, document_type, classification_confidence,
     classification_method, extracted_fields (masked), extraction_method,
     validation_status, page_count, char_count, extraction_errors,
     warnings.

Also exposes `match_documents_to_requirements(...)` for checklist
evaluation.

## Example output

```json
{
  "document_id": "DOC_a1b2c3d4e5f6",
  "document_type": "gst",
  "classification_confidence": 0.9,
  "classification_method": "rule_based",
  "extracted_fields": {
    "gstin": {"value": "22*******Z5", "confidence": 0.9, "method": "regex"},
    "business_name": {"value": "Example Business", "confidence": 0.6, "method": "regex"},
    "pan_identifier": {"value": null, "confidence": 0.0, "method": "regex"}
  },
  "extraction_method": "pdf_text",
  "validation_status": "needs_review",
  "page_count": 1,
  "extraction_errors": [],
  "warnings": []
}
```

## Security & privacy

- Sensitive identifiers masked in demo responses and logs.
- Document contents never logged.
- Unique, non-guessable document IDs; safe filenames.
- No storage of unnecessary personal data beyond extraction.
- No execution of uploaded document contents.
