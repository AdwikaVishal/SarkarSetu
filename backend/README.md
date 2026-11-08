# SarkarSetu AI - Backend

AI-powered government services guidance platform for Indian entrepreneurs.

## Project Purpose

SarkarSetu AI helps Indian entrepreneurs navigate government services including:
- Udyam registration
- GST registration requirements
- MSME scheme discovery
- Eligibility verification
- Document preparation
- Personalized business action plans

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI 0.115
- **Validation**: Pydantic v2
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Server**: Uvicorn
- **Testing**: pytest + pytest-asyncio
- **Configuration**: Pydantic Settings
- **Migrations**: Alembic

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+
- pip (or uv)

## Virtual Environment Setup

```bash
# Using venv (built-in)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Using uv (faster)
uv venv
source .venv/bin/activate
```

## Dependency Installation

```bash
# Install production dependencies
pip install -r requirements.txt

# Or install with dev dependencies
pip install -e ".[dev]"

# Using uv
uv pip install -r requirements.txt
uv pip install -e ".[dev]"
```

## Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   - Set `DATABASE_URL` to your PostgreSQL connection string
   - Set `GEMINI_API_KEY` for AI features
   - Set `JWT_SECRET` to a secure random string
   - Adjust other settings as needed

## Running the Development Server

```bash
# Start the development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the Makefile (if created)
make dev
```

The server will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_health.py -v
```

## API Documentation

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/api/v1/openapi.json`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication endpoints (register, login, refresh, logout, me)
│   │   ├── businesses.py    # Business profile CRUD endpoints
│   │   ├── chat.py          # Chat orchestration endpoints (POST /message, GET /status)
│   │   ├── conversation.py  # Conversation and message management endpoints
│   │   ├── health.py        # Health check endpoints
│   │   └── intent.py        # Intent classification and entity extraction endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Pydantic Settings configuration
│   │   └── logging.py       # Structured logging setup
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py    # Async engine, session management
│   │   └── base.py          # SQLAlchemy declarative base
│   ├── models/
│   │   ├── __init__.py      # Database models registry
│   │   ├── business.py      # BusinessProfile model
│   │   ├── conversation.py  # Conversation model (with clarification fields)
│   │   ├── document.py      # UploadedDocument model
│   │   ├── eligibility.py   # EligibilityResult model
│   │   ├── message.py       # Message model
│   │   ├── recommendation.py # Recommendation model
│   │   ├── refresh_token.py # RefreshToken model
│   │   ├── roadmap.py       # Roadmap model
│   │   ├── task.py          # RoadmapTask model
│   │   └── user.py          # User model
│   ├── schemas/
│   │   ├── __init__.py      # Pydantic schemas registry
│   │   ├── ai.py            # AI request/response schemas
│   │   ├── auth.py          # Authentication schemas
│   │   ├── business.py      # Business profile schemas
│   │   ├── conversation.py  # Conversation and message schemas
│   │   ├── document.py      # Document schemas
│   │   ├── eligibility.py   # Eligibility schemas
│   │   ├── entities.py      # ExtractedEntity schema
│   │   ├── intent.py        # Intent detection schemas
│   │   ├── intent_enums.py  # Shared intent/entity enums
│   │   ├── message.py       # Message schemas
│   │   ├── orchestrator.py  # Orchestrator request/response schemas
│   │   ├── recommendation.py # Recommendation schemas
│   │   ├── roadmap.py       # Roadmap schemas
│   │   ├── task.py          # RoadmapTask schemas
│   │   └── user.py          # User schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py     # High-level AI operations (text, JSON, structured output)
│   │   │   ├── exceptions.py     # AI service exceptions
│   │   │   ├── gemini_client.py  # Gemini async client wrapper
│   │   │   └── prompts.py        # Versioned prompt templates
│   │   ├── auth_service.py       # Authentication business logic
│   │   ├── business_service.py   # Business profile business logic
│   │   ├── conversation/
│   │   │   ├── __init__.py
│   │   │   ├── conversation_service.py  # Conversation/Message CRUD
│   │   │   ├── clarification_service.py # Clarification state management
│   │   │   └── context_manager.py       # Conversation context building
│   │   ├── intent/
│   │   │   ├── __init__.py
│   │   │   ├── context_builder.py   # Conversation context string building
│   │   │   ├── entity_extractor.py  # Entity extraction service
│   │   │   ├── intent_classifier.py # Intent classification service
│   │   │   └── intent_taxonomy.py   # Intent/entity enums and constants
│   │   ├── orchestrator/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py    # SarkarSetuOrchestrator - central pipeline
│   │   │   ├── pipeline.py        # Pipeline stages and context
│   │   │   └── response_builder.py # Response type routing and prompt construction
│   │   └── ownership.py     # Resource ownership validation
│   └── agents/
│       └── __init__.py      # AI agents (planned for Prompt 08)
├── tests/
│   ├── __init__.py
│   ├── test_ai.py           # AI service tests
│   ├── test_auth.py         # Authentication tests
│   ├── test_business.py     # Business profile tests
│   ├── test_chat.py         # (planned) Chat API tests
│   ├── test_conversation.py # Conversation model tests
│   ├── test_database.py     # Database integration tests (requires TEST_DATABASE_URL)
│   ├── test_health.py       # Health endpoint tests
│   ├── test_intent.py       # Intent detection tests
│   ├── test_orchestrator.py # Orchestrator pipeline tests
│   └── test_models_import.py # Model import and metadata tests
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Production dependencies
├── pyproject.toml           # Project metadata and tool config
└── README.md                # This file
```

## Orchestrator Architecture

SarkarSetu AI uses a centralized orchestrator (`SarkarSetuOrchestrator`) that coordinates all existing backend services into a single end-to-end conversational workflow. The orchestrator does not duplicate service logic — it delegates to existing services at each pipeline stage.

### Orchestration Package

- `app/services/orchestrator/orchestrator.py` — `SarkarSetuOrchestrator` service with `process_message()`
- `app/services/orchestrator/pipeline.py` — Pipeline stages (`PipelineContext`, `PipelineResult`, `StageTimer`)
- `app/services/orchestrator/response_builder.py` — Response type routing (`ResponseBuilder`) and prompt construction
- `app/schemas/orchestrator.py` — Request/response schemas and `ResponseType` enum

### Message Processing Pipeline

`POST /api/v1/chat/message` processes a user message through 10 sequential stages:

1. **Validate Request** — Message length (1–5000 chars), content non-empty, authenticated user ID present
2. **Load/Create Conversation** — Retrieve existing conversation (verify ownership) or create new one (verify business profile ownership)
3. **Persist User Message** — Store user message via `persist_user_message()` (role always `user`)
4. **Retrieve Context** — Get recent conversation history via `ConversationContextManager` (bounded to 10 messages)
5. **Handle Clarification** — Check for pending clarification via `ClarificationService`; resolve or preserve
6. **Classify & Extract** — Intent classification + entity extraction via `IntentClassifier` / `EntityExtractor`
7. **Route Response** — Determine `ResponseType` based on intent, clarification state, and confidence
8. **Generate Response** — AI-powered response via `AIService` with structured output validation
9. **Persist Assistant Message** — Store assistant response via `persist_assistant_message()` with metadata
10. **Return Response** — Typed `ChatMessageResponse` with intent, entities, clarification, warnings

### Response Types (`ResponseType`)

| Value | Description |
|-------|-------------|
| `greeting` | Greeting response (no AI call needed) |
| `general_guidance` | General entrepreneurship guidance via AI |
| `clarification` | Clarification question needed |
| `intent_uncertain` | Intent could not be confidently classified |
| `workflow_not_available` | Requested workflow not yet implemented |
| `out_of_scope` | Request outside platform scope |
| `error` | Error state with safe user message |

### Intent Routing

The orchestrator routes intents as follows:

- **GREETING** → Standard greeting response (no AI call)
- **GENERAL_QUESTION** → AI-generated general guidance
- **SCHEME_DISCOVERY / SUBSIDY_DISCOVERY / LOAN_DISCOVERY** → Explain that official-source verification is required; collect business context
- **UDYAM_REGISTRATION / GST_REGISTRATION** → Safe introductory guidance; identify next required information; no binding determinations
- **SCHEME_ELIGIBILITY / UDYAM_ELIGIBILITY / GST_APPLICABILITY** → Explain that evidence-backed rules and sufficient information are required
- **DOCUMENT_GUIDANCE** → Ask which registration/service is being referenced when unclear
- **CREATE_ROADMAP / VIEW_ROADMAP / TASK_PROGRESS** → Workflow not yet available
- **COMPLIANCE_GUIDANCE / TAX_GUIDANCE / DEADLINE_QUERY** → Workflow not yet available
- **APPLICATION_STATUS / DOCUMENT_VALIDATION** → Workflow not yet available
- **OUT_OF_SCOPE** → Polite scope explanation
- **UNKNOWN** → Ask clarifying question

### Clarification Continuity

The orchestrator supports multi-turn clarification:

- When a clarification is pending, the user's next message is interpreted as an answer to the pending question
- The clarification is resolved via `ClarificationService.resolve_clarification()`
- If the answer is incomplete, the clarification is preserved
- Short responses ("Yes", "No") are treated as clarification answers, not new intents

Example flow:
1. User: "Which government schemes can help my business?"
2. Assistant: "What kind of business do you operate?" (clarification set)
3. User: "A small clothing manufacturing business."
4. Assistant: Incorporates the business type into scheme-discovery context

### Failure Handling

Failures at any pipeline stage are handled gracefully:

- **AI service unavailable** → Returns safe error response; user message is preserved
- **Intent classification error** → Pipeline degrades; response type set to `ERROR`
- **Structured output validation error** → Returns safe error; suggests rephrasing
- **Database persistence failure** → Warning recorded; pipeline continues where possible
- **Conversation archived during processing** → Error returned; no partial state

The user message is always persisted before AI processing. If AI processing fails, the original user message is not lost.

### Chat API Endpoints

#### POST /api/v1/chat/message

Send a message through the orchestrator pipeline.

**Request:**
```json
{
  "conversation_id": "optional-uuid",
  "business_profile_id": "optional-uuid",
  "message": "How do I register for GST?",
  "idempotency_key": "optional-idempotency-key"
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "user_message_id": "uuid",
  "assistant_message_id": "uuid",
  "assistant_response": "Here is general guidance about GST registration...",
  "intent": {
    "primary_intent": "gst_registration",
    "secondary_intents": [],
    "confidence": 0.95,
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
  "created_at": "2026-11-07T..."
}
```

#### GET /api/v1/chat/conversations/{conversation_id}/status

Get conversation status and clarification state.

**Response:**
```json
{
  "conversation_id": "uuid",
  "status": "active",
  "clarification_pending": false,
  "clarification_question": null,
  "business_profile_id": null,
  "last_message_at": "2026-11-07T..."
}
```

### Security Model

- JWT authentication required on all chat endpoints
- User ID is extracted from JWT token, never from client input
- Conversation ownership verified at every stage
- Business profile ownership verified before association
- Archived business profiles and conversations are rejected
- Client-created messages are restricted to `role: "user"` only
- Assistant/system messages are created only through trusted internal service methods (`persist_assistant_message`, `persist_system_message`)
- No secrets, JWTs, or sensitive identifiers in logs or AI context
- Input length limited to 5000 characters

### Testing

```bash
# Run all tests (unit tests pass without database)
pytest

# Database integration tests require PostgreSQL:
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/testdb"
pytest tests/test_database.py -v

# Run linting
ruff check app/

# Run type checking
mypy app/
```

### Current Limitations

- Conversation summarization is not yet implemented
- Specialized agents and eligibility engine are implemented (Prompt 09)
- Database integration tests require `TEST_DATABASE_URL` (98 tests skipped without it)

## Agent Architecture

SarkarSetu AI uses a specialized agent pattern for domain-specific government
service tasks. Agents are coordinated through the central orchestrator and
delegate to existing services rather than duplicating logic.

### Agent Package

- `app/services/agents/__init__.py` — Package exports
- `app/services/agents/base.py` — `BaseAgent` abstract base class
- `app/services/agents/agent_registry.py` — `AgentRegistry` with intent routing
- `app/services/agents/discovery_agent.py` — `DiscoveryAgent`
- `app/services/agents/eligibility_agent.py` — `EligibilityAgent`
- `app/services/agents/document_agent.py` — `DocumentAgent`
- `app/services/agents/compliance_agent.py` — `ComplianceAgent`
- `app/schemas/agents.py` — `AgentContext`, `AgentResult`, `AgentStatus`, `RetrievalSource`
- `app/services/retrieval.py` — `GovernmentKnowledgeProvider` protocol
- `app/services/eligibility.py` — `EligibilityEvaluator` protocol

### Agent Context and Result

**`AgentContext`** — Shared context passed to every agent:
- `user_id` — Authenticated user ID (from JWT, never from client)
- `conversation_id` — Conversation ID
- `business_profile_id` — Optional associated business profile ID
- `message` — Current user message text
- `primary_intent` / `secondary_intents` — Intent classification results
- `extracted_entities` — Extracted entities from the message
- `conversation_history` — Recent conversation history
- `clarification_state` — Pending clarification state, if any
- `retrieved_evidence` — Retrieved government document evidence
- `request_id` — Unique request correlation ID

**`AgentResult`** — Typed result returned by every agent:
- `agent_name` — Name of the agent
- `status` — `AgentStatus` enum (`completed`, `needs_information`, `needs_retrieval`, `needs_verification`, `not_supported`, `failed`)
- `response` — User-facing response text
- `structured_data` — Structured data produced by the agent
- `missing_information` — Information needed from the user
- `clarification_question` — Question to ask the user, if required
- `warnings` — Non-fatal warnings
- `evidence_references` — Source references for claims
- `execution_duration_ms` — Execution duration
- `handoff_required` / `handoff_target` — Handoff information

### Intent-to-Agent Mapping

| Intent | Agent |
|--------|-------|
| `government_scheme_discovery` | DiscoveryAgent |
| `subsidy_discovery` | DiscoveryAgent |
| `loan_discovery` | DiscoveryAgent |
| `registration_discovery` | DiscoveryAgent |
| `scheme_eligibility` | EligibilityAgent |
| `udyam_eligibility` | EligibilityAgent |
| `gst_applicability` | EligibilityAgent |
| `document_guidance` | DocumentAgent |
| `document_validation` | DocumentAgent |
| `document_upload` | DocumentAgent |
| `application_guidance` | DocumentAgent |
| `compliance_guidance` | ComplianceAgent |
| `tax_guidance` | ComplianceAgent |
| `deadline_query` | ComplianceAgent |
| `gst_registration` | ComplianceAgent |
| `business_registration` | ComplianceAgent |
| `udyam_registration` | ComplianceAgent |

Intents not in this mapping (greeting, general_question, out_of_scope, unknown,
roadmap, task_progress) continue to be handled by the orchestrator's existing
response strategies.

### Agent Responsibilities

#### DiscoveryAgent

Understands business requirements and prepares grounded government-scheme
discovery requests. Supports scheme, subsidy, loan, and registration discovery.

- Extracts business attributes from extracted entities
- Identifies missing business information (type, industry, state, district,
  turnover, employee count, stage)
- Prepares structured discovery queries
- Requests official-source retrieval through `GovernmentKnowledgeProvider`
- Returns grounded results with source citations
- **Never** fabricates scheme names, funding amounts, deadlines, or benefits

#### EligibilityAgent

Collects information for scheme eligibility assessment and coordinates with
the deterministic eligibility engine. Supports scheme, Udyam, and GST
eligibility.

- Identifies the scheme/registration being assessed
- Collects business profile information
- Identifies missing eligibility fields
- Asks targeted clarification questions
- Delegates to `EligibilityEvaluator` for deterministic assessment
- **Never** independently decides eligibility — the engine is the sole authority

#### DocumentAgent

Guides users through government document requirements. Supports document
guidance, validation, upload, and application guidance.

- Identifies relevant registration/scheme/application
- Requests document requirements from retrieval interface
- Generates structured checklists from verified evidence
- Explains document purpose in simple language
- **Never** invents mandatory document requirements
- **Never** claims documents are officially verified merely because uploaded
- **Never** exposes storage keys or logs document contents

#### ComplianceAgent

Provides evidence-backed guidance on registration and compliance. Supports
compliance, tax, deadline, GST, business, and Udyam registration.

- Understands compliance questions and identifies regulatory topics
- Collects business details
- Requests official evidence from retrieval system
- Explains verified information in accessible language
- **Never** independently determines legal or tax obligations
- **Never** invents filing deadlines, penalties, fees, or thresholds
- **Never** presents general guidance as personalized legal advice

### Retrieval Interface Contract (`GovernmentKnowledgeProvider`)

Saatvika's RAG layer must implement this protocol:

```python
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

`RetrievalSource` contains: document_id, source_title, issuing_authority,
source_url, publication_date, relevant_excerpt, page_or_section,
retrieval_score, document_version.

An `UnavailableGovernmentKnowledgeProvider` is used when no provider is
connected — agents gracefully return `NEEDS_RETRIEVAL` status.

### Eligibility Engine (Prompt 10)

The deterministic eligibility engine evaluates business information against
explicitly defined, versioned government rules. It is the sole authority for
eligibility decisions — Gemini is never used to determine eligibility.

#### Engine Package

- `app/services/eligibility_engine/__init__.py` — Package exports
- `app/services/eligibility_engine/engine.py` — `EligibilityEngine` — core engine
- `app/services/eligibility_engine/rule_evaluator.py` — `RuleEvaluator` — condition evaluation
- `app/services/eligibility_engine/rule_registry.py` — `RuleRegistry` — versioned rule storage
- `app/services/eligibility_engine/rule_loader.py` — `RuleLoader` — rule definition loading
- `app/services/eligibility_engine/assessment_service.py` — `EligibilityAssessmentService` — assessment lifecycle
- `app/models/eligibility_rule.py` — `EligibilityRuleSet`, `EligibilityRule`, `EligibilityAssessment` — database models
- `app/schemas/eligibility_rule.py` — Rule schemas (RuleCondition, RuleSetDefinition, ConditionResult, AssessmentResult)
- `app/schemas/eligibility.py` — `EligibilityAssessmentRequest`, `EligibilityAssessmentResult` — protocol schemas
- `app/services/eligibility.py` — `EligibilityEvaluator` protocol, `EligibilityEvaluatorUnavailable` fallback

#### Rule Definition Model

Each rule set contains:

| Field | Type | Description |
|-------|------|-------------|
| `rule_set_id` | string | Stable identifier (e.g., `"udyam_classification"`) |
| `version` | string | Semantic version (e.g., `"1.0.0"`) |
| `scheme_id` | string \| null | Government scheme identifier |
| `scheme_name` | string \| null | Human-readable scheme name |
| `effective_from` | datetime | Date from which rules are effective |
| `effective_until` | datetime \| null | Date until which rules are effective |
| `approval_status` | string | `draft`, `pending_review`, `approved`, `retired` |
| `issuing_authority` | string \| null | Government authority |
| `source_title` / `source_url` | string \| null | Official source document |
| `rules` | list[RuleCondition] | Individual rule conditions |

Each rule condition contains:

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Stable rule identifier |
| `description` | string | Human-readable condition description |
| `field` | string | Business attribute field (e.g., `"annual_turnover"`) |
| `operator` | RuleOperator | Comparison operator |
| `expected_value` | any | Expected value for comparison |
| `mandatory` | boolean | Whether failure makes the user ineligible |
| `priority` | int | Evaluation order (lower = first) |
| `source_reference` | string \| null | Source document reference |
| `failure_message` | string \| null | User-facing failure message |

#### Supported Operators

| Operator | Description |
|----------|-------------|
| `EQUALS` | Value equals expected |
| `NOT_EQUALS` | Value does not equal expected |
| `GREATER_THAN` | Value > expected |
| `GREATER_THAN_OR_EQUAL` | Value >= expected |
| `LESS_THAN` | Value < expected |
| `LESS_THAN_OR_EQUAL` | Value <= expected |
| `IN` | Value in expected list |
| `NOT_IN` | Value not in expected list |
| `CONTAINS` | Value contains expected substring |
| `IS_TRUE` | Value is True |
| `IS_FALSE` | Value is False |
| `IS_PRESENT` | Value is not None |
| `IS_MISSING` | Value is None |

No arbitrary code execution or expression evaluation is supported.

#### Rule Approval Lifecycle

Rule sets follow this lifecycle:

1. `DRAFT` — Initial creation, not usable for assessments
2. `PENDING_REVIEW` — Submitted for review
3. `APPROVED` — Active, can be used in production assessments
4. `RETIRED` — No longer active, retained for historical reference

Only `APPROVED` rule sets may be used in production assessments. Rule sets are immutable once approved — a new version must be created for changes.

#### Eligibility Aggregation Policy

Condition outcomes are `PASS`, `FAIL`, `UNKNOWN`, or `NOT_APPLICABLE`. The overall assessment status is determined by:

| Overall Status | Condition |
|----------------|-----------|
| `eligible` | All mandatory conditions pass, no mandatory unknowns or failures |
| `ineligible` | At least one mandatory condition definitively fails |
| `needs_information` | At least one mandatory condition is unknown (missing input) |
| `potentially_eligible` | All mandatory pass, but optional conditions are unknown or failed |
| `unverified` | No approved rule set available, or evidence insufficient |

Key rules:
- A missing mandatory field **never** results in `INELIGIBLE` — it results in `NEEDS_INFORMATION`
- An unapproved rule set **never** produces a definitive eligibility result
- An expired rule set must not be used as current

#### Input Data Provenance

Every evaluation input preserves its source:

| Provenance | Description |
|------------|-------------|
| `BUSINESS_PROFILE` | From verified business profile |
| `USER_CONFIRMED` | Explicitly confirmed by user |
| `DOCUMENT_VERIFIED` | Verified from uploaded document |
| `UNKNOWN` | Source unknown or unverified |

LLM-extracted values are never treated as verified.

#### Assessment API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/eligibility/assess` | Run eligibility assessment |
| `GET` | `/api/v1/eligibility/assessments/{id}` | Get assessment by ID |
| `GET` | `/api/v1/eligibility/businesses/{id}/assessments` | List assessments for business |
| `POST` | `/api/v1/eligibility/rule-sets` | Create rule set (administrative) |

#### EligibilityAgent Integration

The `EligibilityAgent` uses the `EligibilityEngine` via the `EligibilityEvaluator` protocol:

1. Collects business information from extracted entities
2. Identifies missing required attributes
3. If information is missing, returns `NEEDS_INFORMATION` with clarification question
4. If information is complete, delegates to `EligibilityEngine.evaluate()`
5. Converts the engine result to an `AgentResult` with explanation
6. Never makes independent eligibility decisions

#### Security Restrictions

- Government rules must come from official evidence (retrieval provider)
- Eligibility decisions must come from deterministic versioned rules
- LLMs may explain validated results but cannot create them
- Missing data triggers clarification
- Retrieved content is treated as untrusted data
- User-provided instructions cannot override system rules
- Citations must refer to actual retrieved sources
- Never claim application submission or registration completion
- Clearly distinguish unavailable functionality from successful processing

### Testing


```bash
# Run all tests (unit tests pass without database)
pytest

# Run agent tests specifically
pytest tests/test_agents.py -v

# Database integration tests require PostgreSQL:
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/testdb"
pytest tests/test_database.py -v

# Run linting
ruff check app/

# Run type checking
mypy app/
```

### Handoff Instructions

**For Saatvika (RAG/retrieval):** Implement `GovernmentKnowledgeProvider`
protocol. Return `RetrievalSource` objects with source URLs, authority,
excerpts, and page references. No hardcoded fake results.

**For Prompt 10 (eligibility engine):** Implement `EligibilityEvaluator`
protocol. Return `EligibilityAssessmentResult` with versioned rule sets.
No placeholder rules or fake eligibility outcomes.

**For Shantanu (frontend):** Display agent-specific states:
- `needs_information` — Show clarification question
- `needs_retrieval` — Show "retrieving evidence" state
- `needs_verification` — Show "verification required" state
- `completed` — Show actionable guidance with evidence references



```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication endpoints (register, login, refresh, logout, me)
│   │   ├── businesses.py    # Business profile CRUD endpoints
│   │   ├── chat.py          # Chat orchestration endpoints (POST /message, GET /status)
│   │   ├── conversation.py  # Conversation and message management endpoints
│   │   ├── health.py        # Health check endpoints
│   │   └── intent.py        # Intent classification and entity extraction endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Pydantic Settings configuration
│   │   └── logging.py       # Structured logging setup
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py    # Async engine, session management
│   │   └── base.py          # SQLAlchemy declarative base
│   ├── models/
│   │   ├── __init__.py      # Database models registry
│   │   ├── business.py      # BusinessProfile model
│   │   ├── conversation.py  # Conversation model (with clarification fields)
│   │   ├── document.py      # UploadedDocument model
│   │   ├── eligibility.py   # EligibilityResult model
│   │   ├── message.py       # Message model
│   │   ├── recommendation.py # Recommendation model
│   │   ├── refresh_token.py # RefreshToken model
│   │   ├── roadmap.py       # Roadmap model
│   │   ├── task.py          # RoadmapTask model
│   │   └── user.py          # User model
│   ├── schemas/
│   │   ├── __init__.py      # Pydantic schemas registry
│   │   ├── ai.py            # AI request/response schemas
│   │   ├── auth.py          # Authentication schemas
│   │   ├── business.py      # Business profile schemas
│   │   ├── conversation.py  # Conversation and message schemas
│   │   ├── document.py      # Document schemas
│   │   ├── eligibility.py   # Eligibility schemas
│   │   ├── entities.py      # ExtractedEntity schema
│   │   ├── intent.py        # Intent detection schemas
│   │   ├── intent_enums.py  # Shared intent/entity enums
│   │   ├── message.py       # Message schemas
│   │   ├── orchestrator.py  # Orchestrator request/response schemas
│   │   ├── recommendation.py # Recommendation schemas
│   │   ├── roadmap.py       # Roadmap schemas
│   │   ├── task.py          # RoadmapTask schemas
│   │   └── user.py          # User schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py     # High-level AI operations (text, JSON, structured output)
│   │   │   ├── exceptions.py     # AI service exceptions
│   │   │   ├── gemini_client.py  # Gemini async client wrapper
│   │   │   └── prompts.py        # Versioned prompt templates
│   │   ├── auth_service.py       # Authentication business logic
│   │   ├── business_service.py   # Business profile business logic
│   │   ├── conversation/
│   │   │   ├── __init__.py
│   │   │   ├── conversation_service.py  # Conversation/Message CRUD
│   │   │   ├── clarification_service.py # Clarification state management
│   │   │   └── context_manager.py       # Conversation context building
│   │   ├── intent/
│   │   │   ├── __init__.py
│   │   │   ├── context_builder.py   # Conversation context string building
│   │   │   ├── entity_extractor.py  # Entity extraction service
│   │   │   ├── intent_classifier.py # Intent classification service
│   │   │   └── intent_taxonomy.py   # Intent/entity enums and constants
│   │   ├── orchestrator/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py    # SarkarSetuOrchestrator - central pipeline
│   │   │   ├── pipeline.py        # Pipeline stages and context
│   │   │   └── response_builder.py # Response type routing and prompt construction
│   │   └── ownership.py     # Resource ownership validation
│   └── agents/
│       └── __init__.py      # AI agents (planned for Prompt 08)
├── tests/
│   ├── __init__.py
│   ├── test_ai.py           # AI service tests
│   ├── test_auth.py         # Authentication tests
│   ├── test_business.py     # Business profile tests
│   ├── test_chat.py         # (planned) Chat API tests
│   ├── test_conversation.py # Conversation model tests
│   ├── test_database.py     # Database integration tests (requires TEST_DATABASE_URL)
│   ├── test_health.py       # Health endpoint tests
│   ├── test_intent.py       # Intent detection tests
│   ├── test_orchestrator.py # Orchestrator pipeline tests
│   └── test_models_import.py # Model import and metadata tests
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Production dependencies
├── pyproject.toml           # Project metadata and tool config
└── README.md                # This file
```

## Next Steps

This is the foundation. Future work includes:
1. Database models and migrations (Alembic)
2. Authentication and authorization
3. Business logic services
4. AI agent integration
5. API endpoints for core features

## License

Proprietary - All rights reserved.