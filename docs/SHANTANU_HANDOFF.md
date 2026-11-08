# SarkarSetu AI — Handoff Package for Shantanu (Person 3: Frontend)

This document gives you everything you need to connect the frontend to the
completed backend. It distinguishes between **what is ready**, **what you must
build**, and **what is blocked on the backend**.

---

## 1. Current project architecture

```
SarkarSetu/                       (repo root)
├── backend/                      Person 1 — FastAPI backend
│   ├── app/main.py               FastAPI app, CORS, routers
│   ├── app/api/                  API routers (auth, businesses, chat, ...)
│   ├── app/schemas/              Pydantic request/response schemas
│   ├── app/services/             auth, orchestrator, agents, roadmap, workflow, eligibility
│   ├── app/models/               SQLAlchemy DB models
│   └── alembic.ini               DB migrations
├── rag/                          Person 2 — RAG & Document Intelligence
│   ├── agents/document_agent.py  process_document(), match_documents_to_requirements()
│   ├── retrieval/engine.py       retrieve_guidance()
│   ├── integration/knowledge_provider.py  GovernmentKnowledgeProvider bridge
│   └── data/indexes/             FAISS index (ingested gov sources)
└── docs/                         Integration docs (this package)
```

## 2. Frontend technology stack (recommended)

No `frontend/` folder exists in the repo yet — you will create it. A
sensible stack consistent with the backend:

- **Framework:** Next.js (App Router) or React + Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State:** React Query / SWR (recommended for server state) or Zustand
- **Forms:** React Hook Form + Zod (validation matching backend rules)
- **HTTP:** native `fetch` (see `frontend/src/lib/api.ts` reference)

Colors (design direction): navy + teal primary, clean typography,
responsive cards/buttons, accessible labels.

## 3. Backend startup command

From `backend/`:

```bash
# 1. Create venv
python -m venv .venv
.venv\Scripts\activate      # Windows

# 2. Install deps
pip install -r requirements.txt

# 3. Copy env and edit
cp .env.example .env
# set DATABASE_URL (PostgreSQL), JWT_SECRET, GEMINI_API_KEY (optional for AI features)

# 4. Run migrations (if alembic is configured)
# alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API base: `http://localhost:8000` → all routes under `/api/v1`.
Interactive docs: `http://localhost:8000/docs`.

Required env (`backend/.env.example`): `DATABASE_URL`, `JWT_SECRET`,
`GEMINI_API_KEY` (AI features disabled if unset — `GEMINI_ENABLED=false`).

## 4. Frontend startup command

Once you create `frontend/`:

```bash
# copy env
cp .env.example .env.local
# set NEXT_PUBLIC_API_URL=http://localhost:8000

# install
npm install   # or pnpm/yarn

# run
npm run dev   # http://localhost:3000
```

CORS on the backend allows `http://localhost:3000` and `http://localhost:8080` by default.

## 5. Environment variables

Frontend (`frontend/.env`):
- `NEXT_PUBLIC_API_URL` — backend base URL (required). Never put secrets here.

Backend (`backend/.env`): managed by Person 1.

## 6. Authentication flow

Tokens are **JWT bearer tokens returned in the JSON body** (NOT httpOnly cookies).

1. `POST /api/v1/auth/register` or `/login` → returns
   `{ access_token, refresh_token, user }`.
2. Store `access_token` + `refresh_token` (frontend decides storage; in-memory
   + refresh-token restore is simplest).
3. Send `Authorization: Bearer <access_token>` on all protected requests.
4. Access token = 30 min. On `401`, call `POST /api/v1/auth/refresh` with the
   refresh token to rotate tokens, then retry. If refresh fails → clear tokens
   + redirect to login.
5. `POST /api/v1/auth/logout` (body: refresh token) → revoke; clear tokens.

See `docs/AUTH_INTEGRATION.md` and `frontend/src/lib/api.ts` (reference client
that implements this).

**Registration password policy:** min 12 chars, uppercase + lowercase + digit +
special char. Validate on the frontend before submitting.

## 7. API endpoint inventory

Full contract: `docs/API_CONTRACT.md`.

| Category | Endpoints | Status |
|----------|-----------|--------|
| Auth | register, login, refresh, logout, me | ✅ Ready |
| Business profiles | create, list, get, update, archive, restore, set-default | ✅ Ready |
| Chat | send message, conversation status | ✅ Ready |
| Conversations | CRUD + messages | ✅ Ready |
| Eligibility | assess, get, list, rule-sets | ✅ Ready |
| Knowledge search (citations) | search | ⚠️ Ready but uses **fixture provider** (not RAG) |
| AI | generate, json, structured, health | ✅ Ready (needs GEMINI) |
| Intent | classify, extract, analyze | ✅ Ready (needs GEMINI) |
| Health | health, health/db | ✅ Ready |
| Roadmaps | generate, list, get, regenerate, progress, tasks complete/skip | ✅ Ready (routers now wired) |
| Workflows | start, get, respond, resume, cancel, list types | ✅ Ready (routers now wired) |
| Document upload | — | ❌ **No router** (blocker) |
| Recommendations | — | ❌ **No router** (blocker) |

## 8. Exact request/response examples

See `docs/API_CONTRACT.md` for full examples per endpoint.

Key ones:

**Chat message:**
```http
POST /api/v1/chat/message
Authorization: Bearer <token>
Body: { "message": "I want to start a clothing business in Karnataka.", "business_profile_id": "..." }
```
Response includes `assistant_response`, `intent`, `clarification_required`,
`clarification_question`, `response_type`.

**Citations:**
```http
POST /api/v1/knowledge/search
Body: { "query": "Udyam registration requirements", "limit": 5 }
```
Response `results[]` = `RetrievalSourceResponse` with `source_title`,
`issuing_authority`, `page_or_section`, `source_url`, `relevant_excerpt`,
`retrieval_score`.

**Roadmap:**
```http
POST /api/v1/roadmaps/generate
Body: { "business_profile_id": "...", "service_type": "udyam_registration" }
```
Returns roadmap with `tasks[]`, each task has `status`,
`official_portal_url`, `evidence_references`.

**Task complete:**
```http
POST /api/v1/roadmaps/{roadmap_id}/tasks/{task_id}/complete
```

## 9. Citation response structure

`RetrievalSourceResponse` (see `docs/CITATION_CONTRACT.md`):
- `source_title`, `issuing_authority`, `page_or_section`, `source_url`,
  `relevant_excerpt`, `retrieval_score`.

**Verification status is NOT included** in this schema. Treat all
knowledge-search results as **pending verification** — never show a "verified"
badge. A separate `CitationCard` component should render these fields.

**Chat responses do NOT include citations** — call `/knowledge/search`
separately to show citations alongside a chat answer.

## 10. Document upload response structure

**No endpoint exists yet** (`docs/DOCUMENT_UPLOAD_CONTRACT.md`). Person 2's
`process_document()` exists in `rag/` but is not exposed over HTTP. Person 1
needs to add:

- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{id}`
- `GET /api/v1/documents/{id}/matching`

Until then, document upload/extraction/matching cannot be connected.

## 11. Roadmap response structure

See `docs/ROADMAP_INTEGRATION.md`. Roadmap includes `total_tasks`,
`completed_tasks`, `progress_percentage`, `tasks[]` with `status`,
`official_portal_url`, `evidence_references`. Task complete persists in DB
(survives browser refresh).

## 12. Error handling requirements

All errors return:
```json
{ "detail": "User-safe message" }
```
Common statuses: `400`, `401`, `403`, `404`, `409`, `500`. Never expose stack
traces or internals.

Distinguish genuine errors from valid `insufficient_evidence` (chat returns a
safe message; knowledge search returns empty `results`).

Handle: backend unavailable, invalid/expired auth, missing business profile,
invalid input, empty chat response, insufficient evidence, missing citations,
PDF upload failure, OCR unavailable, unsupported document, roadmap failure,
task update failure.

## 13. Recommended frontend components

- `AuthLayout` / `LoginForm` / `RegisterForm`
- `BusinessProfileForm` (create/edit)
- `ChatInterface` (message list, input, loading, clarification)
- `CitationCard` (render knowledge-search results)
- `RecommendationCard` / `RecommendationList`
- `DocumentUpload` + `DocumentProcessingStatus` + `ExtractedFields` + `DocumentChecklist` (blocked until upload endpoint exists)
- `RoadmapList` / `RoadmapDetail` / `TaskChecklist`
- `ProgressIndicator`, `EmptyState`, `ErrorState`, `RetryButton`, `Skeleton`

## 14. Required screens

1. Login / Register
2. Dashboard (business profiles list + create)
3. Business profile create/edit
4. AI chat (with clarification + citations)
5. Recommendations
6. Document upload + extracted fields + checklist
7. Roadmap list + detail + task checklist
8. Settings / logout

## 15. API integration sequence (new-user journey)

1. Register → login → store tokens
2. Create business profile (`POST /businesses/`)
3. Create conversation (`POST /conversations/`)
4. Send chat message (`POST /chat/message`) → handle clarification
5. Optionally search knowledge (`POST /knowledge/search`) → render citations
6. View recommendations (blocked — no endpoint)
7. Upload document (blocked — no endpoint)
8. Generate roadmap (`POST /roadmaps/generate`) → view tasks
9. Mark task complete (`POST .../complete`) → refresh to confirm persistence

## 16. Known backend limitations

- `/knowledge/search` uses `FixtureKnowledgeProvider` (development fixture), not the RAG backend.
- Chat `ChatMessageResponse` has no citations field.
- No document upload router (Person 2's `process_document` not exposed over HTTP).
- No recommendation router.
- AI features (intent classification, entity extraction, AI generate) require
  `GEMINI_ENABLED=true` + `GEMINI_API_KEY`; otherwise they return `503`.
- Document classification/field extraction (Person 2) are rule-based; ambiguous
  docs → `other/unknown`.
- All ingested government sources are `verification_status=pending` — not yet
  human-verified.

## 17. Testing instructions

- Start backend on port 8000, frontend on port 3000.
- Register a user, log in, create a business profile.
- Send a chat message; verify response + intent + clarification handling.
- Search knowledge; verify `results[]` have `source_url`/`issuing_authority`.
- Generate a roadmap; mark a task complete; refresh browser; confirm status persists.
- Open browser dev tools → Network tab: confirm no failed requests, correct
  `Authorization` headers, no CORS errors.
- Confirm no stack traces or internal paths in error responses.

## 18. Deployment instructions

- Backend: run `uvicorn app.main:app` behind a production ASGI server
  (uvicorn/gunicorn). Set `ENVIRONMENT=production`, `GEMINI_ENABLED` as needed,
  restrict `CORS_ORIGINS` to your frontend domain.
- Frontend: build (`npm run build`) and serve; set `NEXT_PUBLIC_API_URL` to the
  production backend URL.

---

## What is ready vs. what you must build

**Ready (backend implemented & registered):**
Auth, business profiles, chat, conversations, eligibility, knowledge search
(fixture), AI (if GEMINI), intent, health, roadmaps, workflows.

**You must build (frontend):**
All UI screens, the API client (`frontend/src/lib/api.ts` reference provided),
auth token management, citation rendering, document checklist rendering, roadmap
task UI, error/loading/empty states.

**Blocked on backend (Person 1):**
Document upload/extraction/matching endpoint; recommendation endpoint; switch
`/knowledge/search` to RAG provider (optional).

## Contact

- Person 1 (Adwika): backend, database, auth, agents, orchestrator
- Person 2 (Saatvika): RAG, document intelligence, OCR, retrieval, citations
- Person 3 (Shantanu): frontend, dashboard, chat, document upload UI
