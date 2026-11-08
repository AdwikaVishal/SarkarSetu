# Citation Display Contract

Source of truth: `backend/app/schemas/orchestrator.py` (`RetrievalSourceResponse`) and
`backend/app/api/knowledge.py` (`POST /api/v1/knowledge/search`).

## Response shape (per citation)

Each item in `results` of a knowledge-search response is a `RetrievalSourceResponse`:

| Field | Type | Notes |
|-------|------|-------|
| `document_id` | string\|null | Chunk/source identifier |
| `source_title` | string\|null | Title of the source document |
| `issuing_authority` | string\|null | Government authority (e.g. "Ministry of MSME, Government of India") |
| `source_url` | string\|null | Official source URL |
| `publication_date` | string\|null | Publication/effective date (often null) |
| `relevant_excerpt` | string\|null | Relevant passage from the document |
| `page_or_section` | string\|null | Page or section reference |
| `retrieval_score` | float\|null | 0.0–1.0 relevance score |
| `document_version` | string\|null | Document version (often null) |

## CitationCard component contract

Suggested location: `frontend/src/components/chat/CitationCard.tsx`

**Props:**
```ts
interface CitationCardProps {
  citation: RetrievalSourceResponse;
}
```

**Required rendering (values must come from the backend):**
1. **Document title** — `citation.source_title` (fallback: "Untitled source")
2. **Authority** — `citation.issuing_authority` (fallback: "Authority not recorded")
3. **Page / section** — `citation.page_or_section` (render only if present)
4. **Official source** — `citation.source_url` as a clickable link (render only if present)
5. **Relevant passage** — `citation.relevant_excerpt` (truncate with "Show more")
6. **Verification status** — **NOT included** in `RetrievalSourceResponse`. Display a neutral "Verification: pending" badge. **Never** show a "verified" badge for these results.

**Verification rule:** All knowledge-search results must be treated as pending verification. Do not fabricate a verified state.

**Empty state:** If `results` is empty, render no citation cards and (optionally) a "No sources found" message. Never fabricate citations.

**Multiple citations:** Render one `CitationCard` per result in `results`.

## Where citations appear

- **Knowledge search** (`POST /api/v1/knowledge/search`): explicit citations in `results`.
- **Chat** (`POST /api/v1/chat/message`): `ChatMessageResponse` has **no citations field**. The assistant response text may reference sources, but structured citations are not attached. To show citations alongside a chat answer, call `/knowledge/search` with the same query and render `CitationCard`s beneath the response.

## Example citation UI

```
Source: Udyam Registration Guidelines
Authority: Ministry of MSME, Government of India
Page: 2
Verification: Pending
Official source: https://udyamregistration.gov.in/  [Open website]

Relevant passage:
"Udyam Registration is the online registration process for Micro, Small and
Medium Enterprises..."
```

## Important limitations

- `verification_status` is **not** part of `RetrievalSourceResponse`; the frontend cannot display a verified/pending distinction from this endpoint alone.
- All sources from `/knowledge/search` currently come from `FixtureKnowledgeProvider` (development fixture), not the RAG backend. Treat as illustrative.
