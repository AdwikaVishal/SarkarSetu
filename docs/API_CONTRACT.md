# SarkarSetu AI — Frontend-Backend API Contract

Source of truth: the actual FastAPI backend implementation under `backend/app/`.
Base path: all API routes are mounted under `settings.api_prefix` = `/api/v1`.

**Important integration status notes:**

| Area | Status |
|------|--------|
| Auth (register/login/logout/me/refresh) | ✅ Registered & implemented |
| Business profiles (CRUD) | ✅ Registered & implemented |
| Chat / message | ✅ Registered & implemented (uses RAG-backed provider) |
| Conversations + messages | ✅ Registered & implemented |
| Eligibility assessment | ✅ Registered & implemented |
| Knowledge search | ✅ Registered (uses **FixtureKnowledgeProvider**, not RAG) |
| Health | ✅ Registered |
| AI generate / json / structured | ✅ Registered (requires GEMINI) |
| Intent classify / extract / analyze | ✅ Registered (requires GEMINI) |
| Roadmaps (generate/list/get/update/complete/skip) | ⚠️ Router exists but was **not registered** — now wired in `main.py` |
| Workflows (start/get/respond/resume/cancel/list) | ⚠️ Router exists but was **not registered** — now wired in `main.py` |
| Document upload / extraction | ❌ **No router exists** — integration blocker |
| Recommendations | ❌ Schema exists, **no router** — integration blocker |

Authentication: JWT **bearer** tokens returned in the JSON response body (access + refresh). Access token expires in 30 minutes; refresh token in 30 days. Tokens are NOT httpOnly cookies — the frontend must store them and send `Authorization: Bearer <access_token>` on protected requests.

CORS: default `http://localhost:3000` and `http://localhost:8080`.

---

## 1. Authentication

### POST /api/v1/auth/register
Register a new user account and return access/refresh tokens + user info.

**Auth required:** No  
**Content-Type:** application/json

**Request body:**
```json
{
  "email": "user@example.com",
  "full_name": "Ramesh Kumar",
  "password": "Str0ng!Pass123"
}
```
- `email`: required, valid email, must be unique
- `full_name`: optional, max 255 chars
- `password`: required, min 12 chars, must contain uppercase, lowercase, digit, special char

**Success (201):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "Ramesh Kumar",
    "is_active": true,
    "is_verified": false,
    "created_at": "2026-11-08T10:00:00Z"
  }
}
```

**Errors:**
- `409` — email already registered (`detail`: message)
- `400` — authentication error (`detail`: message)

---

### POST /api/v1/auth/login
Authenticate with email/password and return tokens.

**Auth required:** No

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "Str0ng!Pass123"
}
```

**Success (200):** same shape as register (`TokenResponse`).

**Errors:**
- `401` — invalid email or password
- `401` — account deactivated

---

### POST /api/v1/auth/refresh
Rotate access + refresh tokens.

**Auth required:** No (but requires a valid refresh token in body)

**Request body:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Success (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401` — token reuse detected / invalid refresh token

---

### POST /api/v1/auth/logout
Revoke the current refresh token.

**Auth required:** No (body contains refresh token)

**Request body:** `{"refresh_token": "..."}`

**Success (200):** `{"message": "Successfully logged out"}`

---

### GET /api/v1/auth/me
Get current authenticated user.

**Auth required:** Yes (`Authorization: Bearer <access_token>`)

**Success (200):**
```json
{
  "id": "550e8400-...",
  "email": "user@example.com",
  "full_name": "Ramesh Kumar",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-11-08T10:00:00Z"
}
```

**Errors:**
- `401` — missing/invalid/expired access token

---

## 2. Business Profiles

All business endpoints require authentication.

### POST /api/v1/businesses/
Create a business profile.

**Request body:**
```json
{
  "business_name": "Clothing Creations",
  "business_type": "Manufacturing",
  "industry": "Apparel",
  "state": "Karnataka",
  "district": "Bengaluru Urban",
  "annual_turnover": 1200000,
  "employee_count": 5,
  "sales_channels": ["online", "offline"],
  "business_structure": "Proprietorship",
  "business_stage": "Startup",
  "description": "Handmade clothing business",
  "city": "Bengaluru",
  "pincode": "560001",
  "woman_owned": false,
  "operating_mode": "both",
  "products_services": ["shirts", "trousers"]
}
```
Required: `business_name`, `business_type`, `industry`, `state`, `district`, `business_structure`, `business_stage`.  
`pincode` must be exactly 6 digits. `gstin` (optional) must start with 2-digit state code and be 15 chars. `operating_mode` must be `online`, `offline`, or `both`.

**Success (201):** `BusinessProfileResponse` (includes `id`, `user_id`, `is_deleted`, `is_default`, `created_at`, `updated_at`).

### GET /api/v1/businesses/
List active (non-archived) business profiles for the user.

**Success (200):**
```json
{
  "items": [ {...BusinessProfileResponse...} ],
  "total": 1
}
```

### GET /api/v1/businesses/archived
List archived business profiles.

### GET /api/v1/businesses/{business_id}
Get a specific business profile (must be owned by user).

**Errors:** `400` invalid UUID, `404` not found/not owned.

### PATCH /api/v1/businesses/{business_id}
Partially update a business profile.

### DELETE /api/v1/businesses/{business_id}
Archive (soft-delete) a business profile. Returns `204`.

### POST /api/v1/businesses/{business_id}/restore
Restore an archived business profile.

### PATCH /api/v1/businesses/{business_id}/default
Set a business profile as the user's default.

---

## 3. AI Chat

### POST /api/v1/chat/message
Send a user message through the orchestrator pipeline. Returns the assistant response plus intent, entities, clarification state, and citations-relevant metadata.

**Auth required:** Yes  
**Request body:**
```json
{
  "conversation_id": null,
  "business_profile_id": null,
  "message": "I want to start a clothing business in Karnataka.",
  "idempotency_key": null
}
```
- `conversation_id`: optional UUID of existing conversation
- `business_profile_id`: optional UUID to associate context
- `message`: required, 1–5000 chars
- `idempotency_key`: optional, max 255 chars

**Success (200):**
```json
{
  "conversation_id": "550e8400-...",
  "user_message_id": "...",
  "assistant_message_id": "...",
  "assistant_response": "To start a clothing business in Karnataka, you may need...",
  "intent": {
    "primary_intent": "udyam_registration",
    "secondary_intents": [],
    "confidence": 0.92,
    "confidence_level": "high",
    "requires_clarification": false,
    "clarification_question": null
  },
  "extracted_entities": [],
  "clarification_required": false,
  "clarification_question": null,
  "warnings": [],
  "response_type": "general_guidance",
  "conversation_status": "active",
  "ai_model": "gemini",
  "created_at": "2026-11-08T10:00:00Z"
}
```

**Clarification flow:** When `clarification_required` is `true`, `clarification_question` contains the question. The user replies with a new `/chat/message` (same `conversation_id`) to continue.

**Response types:** `greeting`, `general_guidance`, `clarification`, `intent_uncertain`, `workflow_not_available`, `out_of_scope`, `error`.

**Note:** `ChatMessageResponse` does **not** include citations. Citations are fetched separately via `POST /api/v1/knowledge/search` (see section 6). The RAG-backed provider is wired into the chat agent registry, so clarification/guidance is grounded in retrieved government sources.

**Errors:** `500` — unexpected processing error (safe message, no internals leaked).

---

### GET /api/v1/chat/conversations/{conversation_id}/status
Get conversation status including whether a clarification is pending.

**Auth required:** Yes

**Success (200):**
```json
{
  "conversation_id": "...",
  "status": "active",
  "clarification_pending": false,
  "clarification_question": null,
  "business_profile_id": null,
  "last_message_at": "2026-11-08T10:00:00Z"
}
```

**Errors:** `404` — conversation not found or not owned by user.

---

## 4. Conversations

### POST /api/v1/conversations
Create a conversation.
**Body:** `{ "business_profile_id": null, "title": "My chat" }`

### GET /api/v1/conversations
List active conversations. Query params: `skip`, `limit` (default 50).

### GET /api/v1/conversations/{conversation_id}
Get a conversation.

### PATCH /api/v1/conversations/{conversation_id}
Update title/status.

### DELETE /api/v1/conversations/{conversation_id}
Archive (soft-delete). Returns `204`.

### POST /api/v1/conversations/{conversation_id}/restore
Restore archived conversation.

### POST /api/v1/conversations/{conversation_id}/messages
Create a user message in a conversation.
**Body:** `{ "conversation_id": "...", "role": "user", "content": "...", "intent": null, "message_metadata": null }`

### GET /api/v1/conversations/{conversation_id}/messages
List messages. Query params: `skip`, `limit`.

---

## 5. Eligibility Assessment

### POST /api/v1/eligibility/assess
Run a deterministic eligibility assessment against approved rules.

**Auth required:** Yes  
**Body:**
```json
{
  "user_id": "...",
  "business_profile_id": "...",
  "scheme_name": "Udyam",
  "registration_type": "udyam_registration",
  "business_attributes": { "annual_turnover": 1200000, "employee_count": 5 },
  "missing_information": [],
  "context": {}
}
```
`user_id` is overridden from the JWT (never trust client input).

**Success (200):** `EligibilityAssessmentResponse` with `assessment_status` (`eligible`/`ineligible`/`needs_information`/`potentially_eligible`/`unverified`), `condition_results`, `missing_information`, `evidence_references`, `warnings`.

### GET /api/v1/eligibility/assessments/{assessment_id}
Get a persisted assessment.

### GET /api/v1/eligibility/businesses/{business_id}/assessments
List assessments for a business.

### POST /api/v1/eligibility/rule-sets
(Administrative) Create a rule set.

---

## 6. Knowledge Search (Citations)

### POST /api/v1/knowledge/search
Search the government knowledge base. Returns structured citations with source provenance.

**Auth required:** Yes  
**Body:**
```json
{
  "query": "Udyam registration requirements Aadhaar PAN",
  "conversation_id": null,
  "filters": null,
  "limit": 5
}
```

**Success (200):**
```json
{
  "query": "Udyam registration requirements Aadhaar PAN",
  "results": [
    {
      "document_id": "chunk_UDYAM_0001",
      "source_title": "Udyam Registration : Zero cost...",
      "issuing_authority": "Ministry of MSME, Government of India",
      "source_url": "https://udyamregistration.gov.in/",
      "publication_date": null,
      "relevant_excerpt": "Udyam Registration is the online registration process...",
      "page_or_section": "2",
      "retrieval_score": 0.65,
      "document_version": null
    }
  ],
  "total_count": 1,
  "provider_enabled": true
}
```

**Important:** This endpoint currently uses `FixtureKnowledgeProvider` (development fixture dataset), **not** the RAG backend. The RAG-backed provider is wired into the chat agent registry, so chat-grounded guidance uses RAG, but explicit knowledge search returns fixture data until `knowledge.py` is switched to `RagKnowledgeProvider`. Citation `verification_status` is not included in `RetrievalSourceResponse` — the frontend should treat all knowledge-search results as pending verification unless confirmed otherwise.

---

## 7. Roadmaps (⚠️ now wired in main.py)

### POST /api/v1/roadmaps/generate
Generate a personalized roadmap.
**Body:** `{ "business_profile_id": "...", "workflow_execution_id": null, "service_type": "udyam_registration", "eligibility_assessment_id": null, "regenerate": false }`

### GET /api/v1/roadmaps
List roadmaps. Query: `business_profile_id`, `status`.

### GET /api/v1/roadmaps/{roadmap_id}
Get roadmap with tasks + progress + dependency graph.

### POST /api/v1/roadmaps/{roadmap_id}/regenerate
Regenerate roadmap.

### GET /api/v1/roadmaps/{roadmap_id}/progress
Get progress summary.

### PATCH /api/v1/roadmaps/{roadmap_id}/tasks/{task_id}
Update a task (title, description, status, priority, etc.).

### POST /api/v1/roadmaps/{roadmap_id}/tasks/{task_id}/complete
Mark a task complete (with prerequisite validation).

### POST /api/v1/roadmaps/{roadmap_id}/tasks/{task_id}/skip
Mark a task skipped.

**Task status values:** `pending`, `in_progress`, `completed`, `blocked`.

---

## 8. Workflows (⚠️ now wired in main.py)

### POST /api/v1/workflows
Start a workflow execution.
**Body:** `{ "conversation_id": null, "service_type": "udyam_registration", "message": "...", "business_profile_id": null }`

### GET /api/v1/workflows/{workflow_id}
Get workflow execution status + step results.

### POST /api/v1/workflows/{workflow_id}/respond
Respond to a clarification question.
**Body:** `{ "response": "..." }`

### POST /api/v1/workflows/{workflow_id}/resume
Resume a paused workflow.

### POST /api/v1/workflows/{workflow_id}/cancel
Cancel a workflow.

### GET /api/v1/workflows
List supported workflow service types.

### GET /api/v1/workflows/history
List user's workflow executions.

---

## 9. AI (requires GEMINI_ENABLED=true)

### POST /api/v1/ai/generate
Generate text from a prompt.

### POST /api/v1/ai/json
Generate JSON from a prompt.

### POST /api/v1/ai/structured
Generate structured output validated against a JSON schema.

### GET /api/v1/ai/health
Check AI availability (no auth). Returns `{ enabled, model, available }`.

### POST /api/v1/ai/test
Dev-only test (requires `AI_TEST_ENABLED=true` and development env).

---

## 10. Intent

### POST /api/v1/intent/classify
Classify user message intent.

### POST /api/v1/intent/extract
Extract entities.

### POST /api/v1/intent/analyze
Combined intent + entity analysis.

---

## 11. Health

### GET /api/v1/health
Basic health check: `{ status, application, version }`.

### GET /api/v1/health/db
Database connectivity: `{ status, database: connected|disconnected }`.

---

## 12. Integration Blockers (frontend cannot use these yet)

### Document upload / extraction
Person 2's `process_document(file_path, business_context, service_type)` exists in `rag/agents/document_agent.py`, but **there is no HTTP router exposing it**. No endpoint to upload a PDF, check processing status, or retrieve extracted fields/matching.  
**Required:** Person 1 must add a document router (e.g. `POST /api/v1/documents/upload`, `GET /api/v1/documents/{id}`, `GET /api/v1/documents/{id}/matching`) backed by `process_document` / `match_documents_to_requirements`.

### Recommendations
`schemas/recommendation.py` exists but there is **no recommendation router**. No endpoint to create/list recommendations.  
**Required:** add recommendation CRUD endpoints.

### Knowledge search provider
`/api/v1/knowledge/search` uses `FixtureKnowledgeProvider`, not the RAG backend. If the frontend needs real government-source citations from the ingested knowledge base, switch `knowledge.py` to use `RagKnowledgeProvider` (same protocol as chat).

---

## 13. Error Response Shape

All endpoints return safe, non-leaky errors:
```json
{
  "detail": "User-safe error message."
}
```
Common statuses: `400` (validation), `401` (auth), `403` (forbidden), `404` (not found), `409` (conflict), `500` (unexpected, safe message). Stack traces and internal paths are never returned to the client.

---

## 14. Headers Summary

| Header | Value | When |
|--------|-------|------|
| `Authorization` | `Bearer <access_token>` | All protected endpoints |
| `Content-Type` | `application/json` | JSON request bodies |
| `Content-Type` | `multipart/form-data` | Future document upload |
