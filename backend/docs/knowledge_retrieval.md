# Government Knowledge Retrieval

SarkarSetu AI includes a knowledge retrieval subsystem that enables agents to ground
their responses in official government documents and schemes. This document describes
the retrieval architecture, protocol, and integration points.

## Architecture Overview

The knowledge retrieval system consists of:

```
app/services/knowledge/
├── __init__.py          — Package exports
├── provider.py          — FixtureKnowledgeProvider (protocol implementation)
├── retriever.py         — Retrieval logic (normalize, filter, rank, deduplicate)
├── source_validator.py  — Source validation rules
├── citation_builder.py  — Citation construction
└── fallback_provider.py — Fallback provider for when retrieval is unavailable
```

## Retrieval Protocol

All knowledge providers implement the `GovernmentKnowledgeProvider` protocol
defined in `app/services/retrieval.py`:

```python
@runtime_checkable
class GovernmentKnowledgeProvider(Protocol):
    async def retrieve(
        self,
        query: str,
        *,
        user_id: UUID,
        conversation_id: UUID,
        filters: dict[str, object] | None = None,
        limit: int = 5,
    ) -> list[RetrievalSource]:
        ...
```

### RetrievalSource Schema

Each retrieved source is represented as a `RetrievalSource` Pydantic model
(defined in `app/schemas/agents.py`):

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | str \| None | Unique identifier of the source document |
| `source_title` | str \| None | Title of the source document |
| `issuing_authority` | str \| None | Government authority that issued the document |
| `source_url` | str \| None | URL where the source document can be accessed |
| `publication_date` | str \| None | Publication or effective date |
| `relevant_excerpt` | str \| None | Relevant excerpt from the document |
| `page_or_section` | str \| None | Page or section reference |
| `retrieval_score` | float \| None | Retrieval relevance score (0.0–1.0) |
| `document_version` | str \| None | Document version, if known |

All fields are optional to support graceful degradation when retrieval is
unavailable or partial.

## Retrieval Pipeline

The retrieval pipeline processes user queries through the following stages:

### 1. Query Normalization

The `Retriever.normalize_query()` method strips whitespace and normalizes
the query string for matching.

### 2. Filter Building

The `Retriever.build_filters()` method extracts scheme/service keywords
from the query and combines them with explicit filter parameters. Supported
filter keys include `scheme_or_scheme` for filtering by government scheme.

### 3. Candidate Retrieval

The `Retriever.retrieve_candidates()` method searches the fixture index
using keyword matching against document titles, excerpts, and scheme names.
Results are scored based on keyword overlap and fixture relevance scores.

### 4. Source Validation

The `SourceValidator.validate_sources()` method applies validation rules:

- Checks issuing authority against known government bodies
- Checks source URL domain against official government domains
- Validates effective date vs publication date
- Flags expired documents
- Checks for missing critical fields (title, authority, URL, excerpt)

### 5. Reranking

The `Retriever.rerank()` method boosts scores for:
- Authoritative government sources (ministry, CBIC, DPIIT, etc.)
- Recently published documents (within 365 days)

### 6. Deduplication

The `Retriever.deduplicate()` method removes documents with duplicate
`document_id` values, keeping the highest-scored version.

### 7. Citation Building

The `CitationBuilder.build_sources()` method converts candidate dicts
into `RetrievalSource` objects, preserving all metadata including
validation warnings and timestamps.

## Fixture Provider

The `FixtureKnowledgeProvider` (`app/services/knowledge/provider.py`)
is a development-only implementation backed by a static fixture dataset
containing 6 government documents:

| Document | Authority | Scheme |
|----------|-----------|--------|
| Udyam Registration Guidelines 2024 | Ministry of MSME | udyam_registration |
| GST Registration Threshold Limits | CBIC | gst_registration |
| PM-SYM Scheme | Ministry of Labour | pmsym |
| MSME Scheme Benefits | Ministry of MSME | msme_schemes |
| GeM Registration | DGS&D | gem_registration |
| Startup India Registration | DPIIT | startup_india |

**IMPORTANT**: These are synthetic example documents for development
and testing only. They must NOT be treated as real government rules
or citations. Saatvika's RAG implementation should replace this
provider before production deployment.

## Provider Selection

The knowledge provider is configured via `KNOWLEDGE_RETRIEVAL_ENABLED`
in `.env`:

- `KNOWLEDGE_RETRIEVAL_ENABLED=true` — Use the fixture provider
- `KNOWLEDGE_RETRIEVAL_ENABLED=false` — Return empty results
  (equivalent to no provider connected)

When disabled, agents receive empty results and return
`NEEDS_RETRIEVAL` status with an appropriate message.

## Agent Integration

All four agents (`DiscoveryAgent`, `EligibilityAgent`, `DocumentAgent`,
`ComplianceAgent`) use the knowledge provider through the shared
`BaseAgent.retrieve_evidence()` method:

```python
evidence = await self.retrieve_evidence(
    query=query,
    context=context,
    filters=filters,
    limit=5,
)
```

### DiscoveryAgent

Uses retrieved evidence to support scheme and service recommendations.
Returns grounded results with source citations. Never fabricates scheme
names or benefits.

### EligibilityAgent

Retrieves supporting official documents but delegates all eligibility
decisions to the deterministic `EligibilityEngine`. Never makes
independent eligibility decisions.

### DocumentAgent

Retrieves document requirements from retrieval and generates structured
checklists. Never invents mandatory document requirements.

### ComplianceAgent

Retrieves relevant official obligations and procedural guidance.
Never independently determines legal or tax obligations.

## Failure Handling

If retrieval is unavailable:

- The provider returns an empty list
- Agents receive `NEEDS_RETRIEVAL` status
- The response explains that official-source verification is required
- No government rules or citations are fabricated

If retrieval returns no relevant results:

- Distinguishes this from provider failure
- Explains that supporting information could not be found
- Asks for clarification or recommends official verification

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `KNOWLEDGE_RETRIEVAL_ENABLED` | `true` | Enable/disable knowledge retrieval |
| `KNOWLEDGE_RETRIEVAL_TOP_K` | `5` | Maximum results per query |
| `KNOWLEDGE_RETRIEVAL_MIN_SCORE` | `0.3` | Minimum relevance score |
| `KNOWLEDGE_RETRIEVAL_RERANK` | `true` | Enable reranking |
| `KNOWLEDGE_RETRIEVAL_TIMEOUT_SECONDS` | `10` | Provider timeout |
| `KNOWLEDGE_RETRIEVAL_DEV_FIXTURE` | `true` | Use fixture-backed provider |

## Security Considerations

- Government rules must come from official evidence
- Eligibility decisions come from deterministic rules, not retrieval
- LLMs may explain validated results but cannot create them
- Missing data triggers clarification, not fabrication
- Retrieved content is treated as untrusted data
- Citations must refer to actual retrieved sources
- Never claim application submission or registration completion

## Handoff Requirements for Saatvika

Saatvika's RAG implementation should:

1. Implement the `GovernmentKnowledgeProvider` protocol
2. Return `RetrievalSource` objects with complete metadata
3. Use official government sources only
4. Preserve source URLs, issuing authorities, and section references
5. Not fabricate missing metadata (leave fields as None when unknown)
6. Handle pagination and large result sets gracefully
7. Support filtering by scheme, jurisdiction, and document type

## API Endpoint

`POST /api/v1/knowledge/search`

Authenticated endpoint for searching the knowledge base. Returns structured
citations with source provenance. Requires JWT authentication.

## Testing

Run knowledge provider tests:

```bash
pytest tests/test_knowledge.py -v
```

All tests run without external dependencies or real Gemini credentials.
Database integration tests require `TEST_DATABASE_URL`.
