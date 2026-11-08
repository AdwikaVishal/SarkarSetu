# Integration Proposal — RAG `GovernmentKnowledgeProvider` -> Backend Agent Registry

## Current state (Person 1 backend)

- `backend/app/services/retrieval.py` defines the `GovernmentKnowledgeProvider` protocol:
  `retrieve(query, *, user_id, conversation_id, filters, limit) -> list[RetrievalSource]`.
- `backend/app/services/knowledge/provider.py` provides `FixtureKnowledgeProvider`
  (development-only fixture dataset, explicitly marked "must be replaced by
  Saatvika's RAG implementation before production deployment").
- `backend/app/api/chat.py:get_agent_registry()` calls
  `get_fixture_provider(enabled=settings.knowledge_retrieval_enabled)` and passes
  it as `retrieval_provider` to `AgentRegistry`. Agents (DocumentAgent,
  DiscoveryAgent, ComplianceAgent, workflows) call
  `retrieval_provider.retrieve(...)` and receive `list[RetrievalSource]`.

## Person 2 RAG provider

- `rag/integration/knowledge_provider.py:RagKnowledgeProvider` implements the
  same protocol. It wraps `rag.retrieval.engine.RetrievalEngine.retrieve_guidance`,
  maps results to `RetrievalSource` (when the backend schema is importable) or
  plain dicts, never raises on retrieval failure, and returns `[]` for
  `insufficient_evidence`.
- Signature: `retrieve(query, *, user_id, conversation_id, filters, limit)` —
  matches the protocol.

## Contract comparison

| Aspect | Protocol (`retrieval.py`) | `RagKnowledgeProvider` | Status |
|---|---|---|---|
| method name | `retrieve` | `retrieve` | match |
| params | query, user_id, conversation_id, filters, limit | same | match |
| async | yes | yes | match |
| return | `list[RetrievalSource]` | `list[RetrievalSource]` or `list[dict]` | match (graceful fallback) |
| on failure | return `[]`, never raise | returns `[]`, logs | match |
| insufficient evidence | return `[]` | returns `[]` | match |

No method/parameter/return/exception mismatches. The provider is a drop-in
replacement for `FixtureKnowledgeProvider`.

## Wiring point

`backend/app/api/chat.py:get_agent_registry()` (line 76-95) and
`backend/app/api/workflows.py` (lines 88-89, 120-121) call
`get_fixture_provider(...)`. Replace with `RagKnowledgeProvider()`.

## Proposed change (minimal, backward-compatible)

In `backend/app/api/chat.py:get_agent_registry()`:

```python
from rag.integration.knowledge_provider import RagKnowledgeProvider

...
knowledge_provider = RagKnowledgeProvider()
return AgentRegistry(
    ai_service=ai_service,
    retrieval_provider=knowledge_provider,
    eligibility_evaluator=engine,
)
```

Guard with a try/ImportError fallback to `get_fixture_provider` so the
backend still starts if the `rag/` package is not on the path or its
dependencies are missing:

```python
try:
    from rag.integration.knowledge_provider import RagKnowledgeProvider
    knowledge_provider = RagKnowledgeProvider()
except Exception:  # pragma: no cover - fallback for dev without RAG deps
    knowledge_provider = get_fixture_provider(
        enabled=settings.knowledge_retrieval_enabled
    )
```

## Behavior after wiring

- User asks an Udyam/GST/MSME question -> agent calls
  `retrieval_provider.retrieve(query, ...)` -> `RagKnowledgeProvider` ->
  `RagKnowledgeProvider.retrieve_guidance` -> FAISS semantic search over
  authentic government sources -> ranked chunks with source metadata.
- Evidence (`RetrievalSource` with document_id, source_title,
  issuing_authority, source_url, relevant_excerpt, page_or_section,
  retrieval_score) reaches the orchestrator and is included in the response
  as citations.
- `insufficient_evidence` -> `[]` -> agent returns NEEDS_RETRIEVAL with a
  user-safe message; no fabricated citations.
- No change to agent code; uses the existing `retrieval_provider` injection
  point.

## Risks / mitigations

- `rag/` imports `sentence-transformers`, `faiss-cpu`, `PyMuPDF` — heavy deps.
  Mitigation: lazy import inside the try/fallback above; backend starts
  without them.
- First retrieval loads the embedding model (~100 MB download, one-time).
  Mitigation: acceptable for prototype; pre-warm in production.
- Sources currently `verification_status=pending` (not auto-verified).
  Mitigation: citations carry the flag; agents/orchestrator should not present
  pending sources as verified legal guidance.

## Deliverables

1. This proposal (`rag/docs/INTEGRATION_PROPOSAL.md`).
2. Wired `chat.py:get_agent_registry()` to use `RagKnowledgeProvider` with
   fallback.
3. End-to-end test: user question -> provider -> RAG -> citations.
