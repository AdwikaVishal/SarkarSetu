# SarkarSetu AI — Frontend Integration Checklist

Status key:
- ✅ Ready (backend implemented & registered)
- ⚠️ Partially ready (exists but needs wiring/config)
- ❌ Blocked (no backend endpoint — cannot integrate yet)
- 🔲 Frontend not yet started

## A. Authentication

| Item | Status | Notes |
|------|--------|-------|
| Register screen | ✅ | POST /api/v1/auth/register |
| Login screen | ✅ | POST /api/v1/auth/login |
| Logout | ✅ | POST /api/v1/auth/logout |
| Current user (/me) | ✅ | GET /api/v1/auth/me |
| Token refresh | ✅ | POST /api/v1/auth/refresh |
| Bearer token on requests | ✅ | Authorization header |
| Session expiry / 401 handling | ✅ | React on 401 → refresh → retry |
| Protected routes reject unauthenticated | ✅ | Backend returns 401 |
| Password policy validation (min 12, upper/lower/digit/special) | ✅ | Matches backend rules |

## B. Business profile onboarding

| Item | Status | Notes |
|------|--------|-------|
| Create business profile | ✅ | POST /api/v1/businesses/ |
| List business profiles | ✅ | GET /api/v1/businesses/ |
| Get single profile | ✅ | GET /api/v1/businesses/{id} |
| Edit/update profile | ✅ | PATCH /api/v1/businesses/{id} |
| Archive / restore | ✅ | DELETE / POST restore |
| Set default profile | ✅ | PATCH .../default |
| Form validation (pincode 6 digits, GSTIN 15 chars, operating_mode enum) | ✅ | Backend enforces |

## C. AI chat

| Item | Status | Notes |
|------|--------|-------|
| Send message | ✅ | POST /api/v1/chat/message |
| Assistant response | ✅ | assistant_response |
| Intent + confidence | ✅ | intent.primary_intent / confidence |
| Clarification question | ✅ | clarification_required + clarification_question |
| Follow-up / conversation continue | ✅ | pass conversation_id |
| Conversation history | ✅ | GET /conversations/{id}/messages |
| Loading indicators | 🔲 frontend |
| Error states | 🔲 frontend |
| AI requires GEMINI_ENABLED | ⚠️ | 503 if not configured |

## D. Citations

| Item | Status | Notes |
|------|--------|-------|
| Knowledge search | ⚠️ | Uses FixtureKnowledgeProvider, not RAG |
| CitationCard component | 🔲 frontend | source_title, authority, page, url, excerpt |
| Verification status shown as pending | ⚠️ | Not in schema — never show "verified" |
| No fake citations | 🔲 frontend | Empty results → no cards |

## E. Recommendations

| Item | Status | Notes |
|------|--------|-------|
| Recommendation screens | ❌ | **No backend router** — blocked |

## F. Document upload

| Item | Status | Notes |
|------|--------|-------|
| PDF upload | ❌ | **No backend router** — blocked |
| Processing status | ❌ | Blocked |
| Extracted fields | ❌ | Blocked |
| Extraction confidence | ❌ | Blocked |
| Missing-document checklist | ❌ | Blocked |
| Sensitive-value masking | ⚠️ | Backend masks when endpoint exists |

## G. Roadmap & tasks

| Item | Status | Notes |
|------|--------|-------|
| Roadmap list | ✅ | GET /api/v1/roadmaps |
| Roadmap detail + tasks | ✅ | GET /api/v1/roadmaps/{id} |
| Generate roadmap | ✅ | POST /api/v1/roadmaps/generate |
| Task complete | ✅ | POST .../tasks/{id}/complete |
| Task update | ✅ | PATCH .../tasks/{id} |
| Task skip | ✅ | POST .../tasks/{id}/skip |
| Progress persists after refresh | ✅ | DB-backed |
| Workflow clarification respond | ✅ | POST /api/v1/workflows/{id}/respond |

## H. Error handling

| Scenario | Status | Notes |
|----------|--------|-------|
| Backend unavailable | 🔲 frontend | Show friendly error |
| Invalid auth / expired session | ✅ | 401 → refresh → login |
| Missing business profile | ✅ | 404 |
| Invalid input | ✅ | 400 |
| Empty chat response | 🔲 frontend | Handle gracefully |
| Insufficient evidence | ✅ | Safe message / empty results |
| Missing citations | 🔲 frontend | No cards |
| PDF upload failure | ❌ | No endpoint |
| OCR unavailable | ❌ | No endpoint |
| Roadmap generation failure | ✅ | 500 safe message |
| Task update failure | ✅ | 500 safe message |

## I. UX / responsiveness

| Item | Status | Notes |
|------|--------|-------|
| Loading skeletons | 🔲 frontend |
| Empty states | 🔲 frontend |
| Error states | 🔲 frontend |
| Success feedback | 🔲 frontend |
| Retry controls | 🔲 frontend |
| Disabled states | 🔲 frontend |
| Form validation | 🔲 frontend |
| Accessible labels | 🔲 frontend |
| Desktop / tablet / mobile | 🔲 frontend |
| Navy + teal design direction | 🔲 frontend |

## J. End-to-end journey

| Step | Status | Notes |
|------|--------|-------|
| Register account | ✅ |
| Log in | ✅ |
| Create business profile | ✅ |
| Open AI assistant | ✅ |
| Ask about clothing business in Karnataka | ✅ |
| Answer clarification questions | ✅ |
| Receive Udyam/GST/MSME guidance | ✅ |
| Open citations / verify source links | ⚠️ | Fixture provider |
| Open recommendations | ❌ | No endpoint |
| Upload synthetic document | ❌ | No endpoint |
| View extracted info | ❌ | No endpoint |
| View missing-doc checklist | ❌ | No endpoint |
| Generate roadmap | ✅ |
| Mark task complete | ✅ |
| Refresh + verify persistence | ✅ |

## K. Integration readiness summary

- Backend can communicate with frontend: ✅ (CORS allows localhost:3000/8080)
- Authentication works: ✅
- Business profile persists: ✅
- AI chat uses actual backend responses: ✅
- Citations display correctly: ⚠️ (fixture data, pending verification only)
- Recommendation screens show actual results: ❌ (no endpoint)
- Document upload works: ❌ (no endpoint)
- Extracted fields display: ❌ (no endpoint)
- Document matching works: ❌ (no endpoint)
- Roadmaps display: ✅
- Tasks update successfully: ✅
- Progress persists: ✅
- Errors handled correctly: ✅ (backend); frontend UI pending
- No fake AI responses: ✅
- No exposed secrets: ✅ (NEXT_PUBLIC_API_URL only)
- Complete user journey: ⚠️ (document/recommendation steps blocked)
- Handoff documentation complete: ✅
