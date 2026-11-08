# Document Upload Contract

## Status: INTEGRATION BLOCKER

Person 2's RAG subsystem exposes `process_document(file_path, business_context, service_type)` in
`rag/agents/document_agent.py` and `match_documents_to_requirements(...)` in
`rag/document_matching/matcher.py`. However, **the backend has no HTTP router exposing these functions.**

There is **no endpoint** for:
- uploading a PDF
- checking document processing status
- retrieving extracted fields
- retrieving document-to-requirement matching results

`backend/app/schemas/document.py` defines `UploadedDocument` schemas (create/update/response) with fields
`original_filename`, `storage_key`, `content_type`, `file_size`, `processing_status`
(`pending`/`processing`/`completed`/`failed`), `document_type`, `extracted_data`, but these are not
wired to any route.

## Required endpoints (to be added by Person 1)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/documents/upload` | POST | Upload a PDF; returns document id + processing status |
| `/api/v1/documents/{document_id}` | GET | Get document record + extracted fields |
| `/api/v1/documents/{document_id}/matching` | GET | Document-to-requirement matching for a service |

## Expected upload response (proposed, to be confirmed with Person 1)

```json
{
  "document_id": "550e8400-...",
  "original_filename": "udyam_certificate.pdf",
  "content_type": "application/pdf",
  "file_size": 245760,
  "processing_status": "processing",
  "document_type": null,
  "extracted_data": null
}
```

## Expected extraction response (proposed)

```json
{
  "document_id": "...",
  "document_type": "gst",
  "classification_confidence": 0.9,
  "extracted_fields": {
    "gstin": { "value": "22*********Z5", "confidence": 0.9, "method": "regex" },
    "business_name": { "value": "Example Biz", "confidence": 0.6, "method": "regex" },
    "pan_identifier": { "value": null, "confidence": 0.0, "method": "regex" }
  },
  "extraction_method": "pdf_text",
  "validation_status": "needs_review",
  "page_count": 1,
  "extraction_errors": [],
  "warnings": []
}
```
Sensitive identifiers (PAN, GSTIN, Aadhaar) are **masked** in the response per Person 2's
`mask_sensitive()` logic.

## Expected matching response (proposed)

```json
{
  "service": "gst_registration",
  "available_documents": [...],
  "missing_documents": [ { "name": "Bank statement", "category": "bank_statement", "mandatory": false } ],
  "needs_review": [],
  "incomplete_extraction": [],
  "overall_status": "incomplete",
  "checklist_coverage": 0.67
}
```

## Frontend responsibilities (once endpoint exists)

1. Validate file type (`.pdf`) and size (<= 50 MB per backend `RAG_MAX_FILE_SIZE_MB`) **before** upload.
2. Upload via `multipart/form-data`.
3. Poll `/api/v1/documents/{id}` until `processing_status` is `completed` or `failed`.
4. Render extracted fields; mask sensitive values; never store personal data in browser storage.
5. Render the matching checklist (available / missing / needs review).
6. Show retry on failure; handle unsupported/corrupt/OCR-failure cases.
7. Never display a document as "verified" merely because text was extracted.
