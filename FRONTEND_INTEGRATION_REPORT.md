# SarkarSetu AI — Frontend Integration Implementation Report (Person 3 Handoff)

## Status: Integration package complete

The backend has been inspected, the API contract documented, frontend API
helpers provided, routers wired, and a complete handoff package prepared for
Shantanu (Person 3).

---

## What was inspected

All backend API routers, schemas, models, services, config, and main.py:
- `auth.py`, `businesses.py`, `chat.py`, `conversation.py`, `eligibility.py`,
  `knowledge.py`, `health.py`, `intent.py`, `ai.py`
- `roadmaps.py`, `workflows.py` (existed but unregistered)
- `schemas/{auth,business,conversation,orchestrator,document,roadmap,task,
  recommendation,eligibility,eligibility_rule,intent,message,user,workflow}.py`
- `core/config.py`, `main.py`, `services/retrieval.py`, `services/agents/*`

## Changes made

### 1. `backend/app/main.py` — router wiring (wiring only, no business logic)
Registered two routers that existed as code but were not mounted:
```python
application.include_router(roadmaps_router, prefix=settings.api_prefix)
application.include_router(workflows_router, prefix=settings.api_prefix)
```
This enables roadmap generation, task complete/skip, and workflow
start/respond/resume/cancel for the frontend. Verified `main.py` compiles.

### 2. `docs/API_CONTRACT.md` (new)
Complete endpoint reference: method, URL, auth, request/body, response,
validation rules, error responses, examples for auth, business, chat,
conversations, eligibility, knowledge, roadmaps, workflows, AI, intent,
health. Includes an "Integration Blockers" section.

### 3. `docs/CITATION_CONTRACT.md` (new)
`RetrievalSourceResponse` shape and `CitationCard` component contract.
Documents that `verification_status` is NOT in the schema → treat all results
as pending verification; never show a "verified" badge. Chat has no citations
field — use `/knowledge/search` separately.

### 4. `docs/DOCUMENT_UPLOAD_CONTRACT.md` (new)
Documents the blocker: Person 2's `process_document()` exists in `rag/` but no
HTTP router exposes it. Lists the three required endpoints and proposed
request/response shapes.

### 5. `docs/AUTH_INTEGRATION.md` (new)
JWT bearer flow, token storage, 401→refresh→retry, password policy, protected
routes.

### 6. `docs/ROADMAP_INTEGRATION.md` (new)
Roadmap/task/workflow endpoints, response shapes, completion flow, status
values, clarification-driven journeys.

### 7. `frontend/src/types/api.ts` (new)
TypeScript types mirroring all FastAPI schemas for the frontend.

### 8. `frontend/src/lib/api.ts` (new)
Centralized fetch-based API client: base URL from `NEXT_PUBLIC_API_URL`,
auth headers, JSON + multipart support, automatic 401→refresh→retry, timeouts,
consistent error handling (`ApiError`), and typed methods for every endpoint.
Reference implementation — place in the frontend project.

### 9. `frontend/.env.example` (new)
`NEXT_PUBLIC_API_URL=http://localhost:8000`.

### 10. `docs/SHANTANU_HANDOFF.md` (new)
Architecture, stack recommendation, backend/frontend startup commands, env
vars, auth flow, endpoint inventory, examples, citation/document/roadmap
structures, error handling, components, screens, integration sequence,
limitations, testing, deployment, ready-vs-blocked split.

### 11. `docs/FRONTEND_INTEGRATION_CHECKLIST.md` (new)
Per-item readiness checklist across auth, business, chat, citations,
recommendations, documents, roadmap, errors, UX, and the full end-to-end
journey.

---

## Integration readiness summary

| Area | Status |
|------|--------|
| Auth | ✅ Ready |
| Business profiles | ✅ Ready |
| Chat / conversations | ✅ Ready |
| Eligibility | ✅ Ready |
| Knowledge search (citations) | ⚠️ Ready but uses FixtureKnowledgeProvider |
| AI / Intent | ✅ Ready (requires GEMINI) |
| Health | ✅ Ready |
| Roadmaps / tasks | ✅ Ready (routers now wired) |
| Workflows | ✅ Ready (routers now wired) |
| Document upload / extraction / matching | ❌ Blocked — no router |
| Recommendations | ❌ Blocked — no router |

## Known limitations for Shantanu

- `/api/v1/knowledge/search` returns fixture data, not the RAG backend. Switch
  `backend/app/api/knowledge.py` to `RagKnowledgeProvider` for real gov sources.
- `ChatMessageResponse` has no citations field — call `/knowledge/search`
  separately to render citations.
- All ingested government sources are `verification_status=pending`.
- AI endpoints return `503` unless `GEMINI_ENABLED=true` + `GEMINI_API_KEY`.
- Document upload/extraction/matching and recommendations have no backend
  endpoints — Person 1 must add them before those screens can be built.
- No `frontend/` folder exists yet — the frontend must be created by Shantanu;
  the API client and types above are provided as a reference.

## Deliverables

- `docs/API_CONTRACT.md`
- `docs/CITATION_CONTRACT.md`
- `docs/DOCUMENT_UPLOAD_CONTRACT.md`
- `docs/AUTH_INTEGRATION.md`
- `docs/ROADMAP_INTEGRATION.md`
- `docs/SHANTANU_HANDOFF.md`
- `docs/FRONTEND_INTEGRATION_CHECKLIST.md`
- `frontend/src/types/api.ts`
- `frontend/src/lib/api.ts`
- `frontend/.env.example`
- `backend/app/main.py` (router wiring)
