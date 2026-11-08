# Roadmap & Task Integration Guide

## Status: ⚠️ Routers now wired in `main.py`

The `roadmaps.py` and `workflows.py` routers existed but were **not registered** in
`backend/app/main.py`. They have now been added:

```python
application.include_router(roadmaps_router, prefix=settings.api_prefix)
application.include_router(workflows_router, prefix=settings.api_prefix)
```

This is wiring only — no business logic changed.

## Roadmap endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/v1/roadmaps/generate` | Yes | Generate personalized roadmap |
| GET | `/api/v1/roadmaps` | Yes | List roadmaps (query: business_profile_id, status) |
| GET | `/api/v1/roadmaps/{roadmap_id}` | Yes | Get roadmap with tasks + progress |
| POST | `/api/v1/roadmaps/{roadmap_id}/regenerate` | Yes | Regenerate roadmap |
| GET | `/api/v1/roadmaps/{roadmap_id}/progress` | Yes | Progress summary |
| PATCH | `/api/v1/roadmaps/{roadmap_id}/tasks/{task_id}` | Yes | Update a task |
| POST | `/api/v1/roadmaps/{roadmap_id}/tasks/{task_id}/complete` | Yes | Mark task complete |
| POST | `/api/v1/roadmaps/{roadmap_id}/tasks/{task_id}/skip` | Yes | Mark task skipped |

## Roadmap response (summary)

```json
{
  "id": "...",
  "user_id": "...",
  "business_profile_id": "...",
  "service_type": "udyam_registration",
  "title": "Udyam Registration Roadmap",
  "description": "...",
  "status": "active",
  "total_tasks": 5,
  "completed_tasks": 1,
  "pending_tasks": 3,
  "blocked_tasks": 1,
  "progress_percentage": 20,
  "created_at": "...",
  "updated_at": "..."
}
```

## Task response

```json
{
  "id": "...",
  "roadmap_id": "...",
  "title": "Prepare Aadhaar and PAN documents",
  "description": "...",
  "category": "documentation",
  "priority": "high",
  "status": "pending",
  "sequence_number": 1,
  "dependencies": [],
  "evidence_references": [],
  "document_ids": [],
  "official_portal_url": "https://udyamregistration.gov.in/",
  "due_date": null,
  "completed_at": null,
  "created_at": "...",
  "updated_at": "..."
}
```

## Task completion flow

1. Frontend renders task checklist from `GET /roadmaps/{id}`.
2. User marks a task complete → `POST /roadmaps/{id}/tasks/{task_id}/complete`.
3. Backend validates prerequisites; returns updated task.
4. On browser refresh, refetch `GET /roadmaps/{id}` — status persists in DB.

## Task status values

`pending`, `in_progress`, `completed`, `blocked`.

## Workflow endpoints (clarification-driven journeys)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/workflows` | Start a workflow (udyam/gst/msme) |
| GET | `/api/v1/workflows/{id}` | Get execution status + step results |
| POST | `/api/v1/workflows/{id}/respond` | Answer a clarification question |
| POST | `/api/v1/workflows/{id}/resume` | Resume paused workflow |
| POST | `/api/v1/workflows/{id}/cancel` | Cancel workflow |
| GET | `/api/v1/workflows` | List supported service types |
| GET | `/api/v1/workflows/history` | User's workflow executions |

Workflow responses include `clarification_question`, `missing_information`, `evidence_references`, `next_actions`, `eligibility_assessment_id`. When `status` is `needs_information`/`needs_retrieval`/`needs_verification`, the frontend must render the clarification question and let the user respond via `/respond`.

## Frontend rendering notes

- Roadmap progress = `completed_tasks / total_tasks * 100` (or use `progress_percentage`).
- Show `official_portal_url` as a link to the government portal.
- Show `evidence_references` as source citations where present.
- Distinguish `potentially_eligible` / `needs_information` / `ineligible` / `unverified` eligibility states — do not calculate eligibility in the frontend.
