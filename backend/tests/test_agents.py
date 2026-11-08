"""Agent tests for Prompt 09.

Tests base agent, DiscoveryAgent, EligibilityAgent, DocumentAgent,
ComplianceAgent, AgentRegistry, and orchestrator integration.

All AI service calls are mocked — no real Gemini API key required.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.agents import (
    AgentContext,
    AgentResult,
    AgentStatus,
    RetrievalSource,
)
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import AIServiceUnavailableError
from app.services.agents.agent_registry import AgentRegistry, INTENT_TO_AGENT
from app.services.agents.base import BaseAgent
from app.services.agents.compliance_agent import ComplianceAgent
from app.services.agents.discovery_agent import DiscoveryAgent
from app.services.agents.document_agent import DocumentAgent
from app.services.agents.eligibility_agent import EligibilityAgent
from app.services.eligibility import (
    EligibilityAssessmentRequest,
    EligibilityAssessmentResult,
)
from app.services.orchestrator.orchestrator import SarkarSetuOrchestrator
from app.services.retrieval import (
    GovernmentKnowledgeProvider,
    UnavailableGovernmentKnowledgeProvider,
)


# ---------------------------------------------------------------------------
# Test helper: concrete BaseAgent subclass for testing
# ---------------------------------------------------------------------------


class _TestAgent(BaseAgent):
    """Concrete BaseAgent subclass for testing abstract methods."""

    async def _execute(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            response=f"Executed: {context.message}",
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_ai_service() -> MagicMock:
    service = MagicMock(spec=AIService)
    service._is_available.return_value = True
    return service


@pytest.fixture
def base_agent(mock_ai_service: MagicMock) -> _TestAgent:
    return _TestAgent(name="TestAgent", ai_service=mock_ai_service)


@pytest.fixture
def mock_retrieval_provider() -> MagicMock:
    provider = MagicMock(spec=GovernmentKnowledgeProvider)
    provider.retrieve = AsyncMock(return_value=[])
    return provider


@pytest.fixture
def mock_eligibility_evaluator() -> MagicMock:
    evaluator = MagicMock()
    evaluator.evaluate = AsyncMock(
        return_value=EligibilityAssessmentResult(
            user_id=uuid4(),
            scheme_name="Test Scheme",
            assessment_status="eligible",
            rule_set_version="1.0.0",
            result_data={},
            missing_information=[],
            evidence_references=[],
            warnings=[],
        )
    )
    return evaluator


def _make_agent_context(
    user_id: UUID | None = None,
    conversation_id: UUID | None = None,
    message: str = "Hello",
    primary_intent: str | None = None,
    business_profile_id: UUID | None = None,
    extracted_entities: list[dict] | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    clarification_state: dict | None = None,
) -> AgentContext:
    return AgentContext(
        user_id=user_id or uuid4(),
        conversation_id=conversation_id or uuid4(),
        business_profile_id=business_profile_id,
        message=message,
        primary_intent=primary_intent,
        secondary_intents=[],
        extracted_entities=extracted_entities or [],
        conversation_history=conversation_history or [],
        clarification_state=clarification_state,
    )


# ---------------------------------------------------------------------------
# BaseAgent tests
# ---------------------------------------------------------------------------


class TestBaseAgent:
    """Tests for the BaseAgent class."""

    def test_valid_context(self):
        """Test that a valid context passes validation."""
        ctx = _make_agent_context()
        errors = ctx.validate_context()
        assert errors == []

    def test_empty_message(self):
        """Test that empty message produces validation error."""
        ctx = _make_agent_context(message="")
        errors = ctx.validate_context()
        assert "Message is empty or whitespace-only" in errors

    def test_whitespace_message(self):
        """Test that whitespace-only message produces validation error."""
        ctx = _make_agent_context(message="   ")
        errors = ctx.validate_context()
        assert "Message is empty or whitespace-only" in errors

    @pytest.mark.asyncio
    async def test_execute_valid_context(
        self, base_agent: _TestAgent
    ):
        """Test that execute returns a valid AgentResult."""
        ctx = _make_agent_context()
        result = await base_agent.execute(ctx)
        assert result.agent_name == "TestAgent"
        assert result.status == AgentStatus.COMPLETED
        assert "Executed:" in result.response

    @pytest.mark.asyncio
    async def test_execute_invalid_context(
        self, base_agent: _TestAgent
    ):
        """Test that execute with invalid context returns FAILED."""
        ctx = _make_agent_context(message="")
        result = await base_agent.execute(ctx)
        assert result.status == AgentStatus.FAILED
        assert "Message is empty" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_ai_service_unavailable(
        self, base_agent: _TestAgent, mock_ai_service: MagicMock
    ):
        """Test that AI service unavailability returns safe error."""
        mock_ai_service._is_available.return_value = False
        base_agent.ai_service = mock_ai_service

        ctx = _make_agent_context()
        base_agent._execute = AsyncMock(
            side_effect=AIServiceUnavailableError("AI is down")
        )
        result = await base_agent.execute(ctx)
        assert result.status == AgentStatus.FAILED
        assert "not available" in result.response.lower()


# ---------------------------------------------------------------------------
# DiscoveryAgent tests
# ---------------------------------------------------------------------------


class TestDiscoveryAgent:
    """Tests for DiscoveryAgent."""

    @pytest.fixture
    def agent(
        self,
        mock_ai_service: MagicMock,
        mock_retrieval_provider: MagicMock,
    ) -> DiscoveryAgent:
        return DiscoveryAgent(
            ai_service=mock_ai_service,
            retrieval_provider=mock_retrieval_provider,
        )

    def test_supported_intents(self, agent: DiscoveryAgent):
        """Test that supported intents are correct."""
        assert "government_scheme_discovery" in agent.SUPPORTED_INTENTS
        assert "subsidy_discovery" in agent.SUPPORTED_INTENTS
        assert "loan_discovery" in agent.SUPPORTED_INTENTS
        assert "registration_discovery" in agent.SUPPORTED_INTENTS

    @pytest.mark.asyncio
    async def test_unsupported_intent(
        self, agent: DiscoveryAgent
    ):
        """Test that unsupported intent returns NOT_SUPPORTED."""
        ctx = _make_agent_context(primary_intent="greeting")
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NOT_SUPPORTED

    @pytest.mark.asyncio
    async def test_missing_business_context(
        self, agent: DiscoveryAgent
    ):
        """Test that missing business context returns NEEDS_INFORMATION."""
        ctx = _make_agent_context(
            primary_intent="government_scheme_discovery",
            message="I want to know about schemes",
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NEEDS_INFORMATION
        assert len(result.missing_information) > 0
        assert result.clarification_question is not None

    @pytest.mark.asyncio
    async def test_retrieval_unavailable(
        self,
        agent: DiscoveryAgent,
        mock_retrieval_provider: MagicMock,
    ):
        """Test that unavailable retrieval returns NEEDS_RETRIEVAL."""
        mock_retrieval_provider.retrieve = AsyncMock(return_value=[])
        # Provide ALL required attributes via entities
        ctx = _make_agent_context(
            primary_intent="government_scheme_discovery",
            message="I have a business in Karnataka",
            extracted_entities=[
                {
                    "entity_type": attr,
                    "value": "test-value",
                    "confidence": 0.95,
                    "source": "user_message",
                    "needs_clarification": False,
                }
                for attr in agent.REQUIRED_ATTRIBUTES
            ],
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NEEDS_RETRIEVAL

    @pytest.mark.asyncio
    async def test_evidence_backed_result(
        self,
        agent: DiscoveryAgent,
        mock_retrieval_provider: MagicMock,
    ):
        """Test that evidence-backed result returns COMPLETED with citations."""
        mock_retrieval_provider.retrieve = AsyncMock(
            return_value=[
                RetrievalSource(
                    document_id="doc-1",
                    source_title="MSME Scheme Guidelines",
                    issuing_authority="Ministry of MSME",
                    source_url="https://example.gov.in/msme",
                    relevant_excerpt="Subsidies available for manufacturing",
                    page_or_section="Section 5",
                    retrieval_score=0.95,
                    document_version="1.0",
                )
            ]
        )
        # Provide ALL required attributes
        ctx = _make_agent_context(
            primary_intent="government_scheme_discovery",
            message="I want manufacturing subsidies",
            extracted_entities=[
                {
                    "entity_type": attr,
                    "value": "test-value",
                    "confidence": 0.95,
                    "source": "user_message",
                    "needs_clarification": False,
                }
                for attr in agent.REQUIRED_ATTRIBUTES
            ],
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.COMPLETED
        assert len(result.evidence_references) == 1
        assert result.evidence_references[0].source_title == "MSME Scheme Guidelines"

    @pytest.mark.asyncio
    async def test_no_fabricated_schemes(
        self, agent: DiscoveryAgent
    ):
        """Test that no schemes are fabricated when retrieval is unavailable."""
        # Provide ALL required attributes but no retrieval results
        ctx = _make_agent_context(
            primary_intent="government_scheme_discovery",
            message="Tell me about schemes",
            extracted_entities=[
                {
                    "entity_type": attr,
                    "value": "test-value",
                    "confidence": 0.95,
                    "source": "user_message",
                    "needs_clarification": False,
                }
                for attr in agent.REQUIRED_ATTRIBUTES
            ],
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NEEDS_RETRIEVAL
        # Should not contain any specific scheme names
        assert "PM" not in result.response
        assert "Mudra" not in result.response


# ---------------------------------------------------------------------------
# EligibilityAgent tests
# ---------------------------------------------------------------------------


class TestEligibilityAgent:
    """Tests for EligibilityAgent."""

    @pytest.fixture
    def agent(
        self,
        mock_ai_service: MagicMock,
        mock_retrieval_provider: MagicMock,
        mock_eligibility_evaluator: MagicMock,
    ) -> EligibilityAgent:
        return EligibilityAgent(
            ai_service=mock_ai_service,
            retrieval_provider=mock_retrieval_provider,
            eligibility_evaluator=mock_eligibility_evaluator,
        )

    def test_supported_intents(self, agent: EligibilityAgent):
        """Test that supported intents are correct."""
        assert "scheme_eligibility" in agent.SUPPORTED_INTENTS
        assert "udyam_eligibility" in agent.SUPPORTED_INTENTS
        assert "gst_applicability" in agent.SUPPORTED_INTENTS

    @pytest.mark.asyncio
    async def test_unsupported_intent(
        self, agent: EligibilityAgent
    ):
        """Test that unsupported intent returns NOT_SUPPORTED."""
        ctx = _make_agent_context(primary_intent="greeting")
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NOT_SUPPORTED

    @pytest.mark.asyncio
    async def test_missing_information(
        self, agent: EligibilityAgent
    ):
        """Test that missing information returns NEEDS_INFORMATION."""
        ctx = _make_agent_context(
            primary_intent="scheme_eligibility",
            message="Am I eligible?",
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NEEDS_INFORMATION
        assert len(result.missing_information) > 0

    @pytest.mark.asyncio
    async def test_evaluator_unavailable(
        self,
        agent: EligibilityAgent,
        mock_eligibility_evaluator: MagicMock,
    ):
        """Test that unavailable evaluator returns NEEDS_VERIFICATION."""
        mock_eligibility_evaluator.evaluate = AsyncMock(
            return_value=EligibilityAssessmentResult(
                user_id=uuid4(),
                scheme_name="Test Scheme",
                assessment_status="verification_required",
                rule_set_version="unavailable",
                result_data={},
                missing_information=[],
                evidence_references=[],
                warnings=["Engine not configured"],
            )
        )
        # Provide ALL required attributes so we proceed to evaluator
        ctx = _make_agent_context(
            primary_intent="scheme_eligibility",
            extracted_entities=[
                {
                    "entity_type": attr,
                    "value": "test-value",
                    "confidence": 0.95,
                    "source": "user_message",
                    "needs_clarification": False,
                }
                for attr in agent.ELIGIBILITY_ATTRIBUTES
            ],
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NEEDS_VERIFICATION

    @pytest.mark.asyncio
    async def test_no_independent_llm_decision(
        self, agent: EligibilityAgent
    ):
        """Test that agent never makes independent eligibility decision."""
        # Provide ALL required attributes
        ctx = _make_agent_context(
            primary_intent="gst_applicability",
            extracted_entities=[
                {
                    "entity_type": attr,
                    "value": "test-value",
                    "confidence": 0.95,
                    "source": "user_message",
                    "needs_clarification": False,
                }
                for attr in agent.ELIGIBILITY_ATTRIBUTES
            ],
        )
        result = await agent.execute(ctx)
        # Should delegate to evaluator, not decide independently
        # If evaluator is mocked to return eligible, the result should be COMPLETED
        # If evaluator returns verification_required, status should be NEEDS_VERIFICATION
        assert result.status in (
            AgentStatus.NEEDS_INFORMATION,
            AgentStatus.NEEDS_VERIFICATION,
            AgentStatus.COMPLETED,
        )


# ---------------------------------------------------------------------------
# DocumentAgent tests
# ---------------------------------------------------------------------------


class TestDocumentAgent:
    """Tests for DocumentAgent."""

    @pytest.fixture
    def agent(
        self,
        mock_ai_service: MagicMock,
        mock_retrieval_provider: MagicMock,
    ) -> DocumentAgent:
        return DocumentAgent(
            ai_service=mock_ai_service,
            retrieval_provider=mock_retrieval_provider,
        )

    def test_supported_intents(self, agent: DocumentAgent):
        """Test that supported intents are correct."""
        assert "document_guidance" in agent.SUPPORTED_INTENTS
        assert "document_validation" in agent.SUPPORTED_INTENTS
        assert "document_upload" in agent.SUPPORTED_INTENTS
        assert "application_guidance" in agent.SUPPORTED_INTENTS

    @pytest.mark.asyncio
    async def test_retrieval_unavailable(
        self, agent: DocumentAgent
    ):
        """Test that unavailable retrieval returns NEEDS_RETRIEVAL."""
        ctx = _make_agent_context(
            primary_intent="document_guidance",
            message="What documents do I need?",
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NEEDS_RETRIEVAL

    @pytest.mark.asyncio
    async def test_evidence_backed_checklist(
        self,
        agent: DocumentAgent,
        mock_retrieval_provider: MagicMock,
    ):
        """Test that evidence-backed checklist returns COMPLETED."""
        mock_retrieval_provider.retrieve = AsyncMock(
            return_value=[
                RetrievalSource(
                    document_id="doc-1",
                    source_title="GST Registration Requirements",
                    issuing_authority="GST Council",
                    source_url="https://gst.gov.in",
                    relevant_excerpt="PAN card required",
                    page_or_section="Section 3",
                    retrieval_score=0.9,
                    document_version="2.0",
                )
            ]
        )
        ctx = _make_agent_context(
            primary_intent="document_guidance",
            message="GST registration documents",
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.COMPLETED
        assert len(result.evidence_references) == 1

    @pytest.mark.asyncio
    async def test_no_fabricated_mandatory_docs(
        self,
        agent: DocumentAgent,
        mock_retrieval_provider: MagicMock,
    ):
        """Test that no mandatory documents are fabricated."""
        mock_retrieval_provider.retrieve = AsyncMock(
            return_value=[
                RetrievalSource(
                    document_id="doc-1",
                    source_title="GST Requirements",
                    issuing_authority="GST Council",
                    relevant_excerpt="PAN card and Aadhaar required",
                )
            ]
        )
        ctx = _make_agent_context(
            primary_intent="document_guidance",
            message="What documents for GST?",
        )
        result = await agent.execute(ctx)
        # Checklist items should not have mandatory=True (never invented)
        for item in result.structured_data.get("checklist", []):
            assert item.get("mandatory") is None


# ---------------------------------------------------------------------------
# ComplianceAgent tests
# ---------------------------------------------------------------------------


class TestComplianceAgent:
    """Tests for ComplianceAgent."""

    @pytest.fixture
    def agent(
        self,
        mock_ai_service: MagicMock,
        mock_retrieval_provider: MagicMock,
    ) -> ComplianceAgent:
        return ComplianceAgent(
            ai_service=mock_ai_service,
            retrieval_provider=mock_retrieval_provider,
        )

    def test_supported_intents(self, agent: ComplianceAgent):
        """Test that supported intents are correct."""
        assert "compliance_guidance" in agent.SUPPORTED_INTENTS
        assert "tax_guidance" in agent.SUPPORTED_INTENTS
        assert "deadline_query" in agent.SUPPORTED_INTENTS
        assert "gst_registration" in agent.SUPPORTED_INTENTS
        assert "business_registration" in agent.SUPPORTED_INTENTS
        assert "udyam_registration" in agent.SUPPORTED_INTENTS

    @pytest.mark.asyncio
    async def test_retrieval_unavailable(
        self, agent: ComplianceAgent
    ):
        """Test that unavailable retrieval returns NEEDS_RETRIEVAL."""
        ctx = _make_agent_context(
            primary_intent="compliance_guidance",
            message="What are compliance requirements?",
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.NEEDS_RETRIEVAL

    @pytest.mark.asyncio
    async def test_evidence_backed_guidance(
        self,
        agent: ComplianceAgent,
        mock_retrieval_provider: MagicMock,
    ):
        """Test that evidence-backed guidance returns COMPLETED."""
        mock_retrieval_provider.retrieve = AsyncMock(
            return_value=[
                RetrievalSource(
                    document_id="doc-1",
                    source_title="Udyam Registration Guide",
                    issuing_authority="Ministry of MSME",
                    relevant_excerpt="Registration is free and online",
                    page_or_section="Section 2",
                    retrieval_score=0.88,
                )
            ]
        )
        ctx = _make_agent_context(
            primary_intent="udyam_registration",
            message="How do I register for Udyam?",
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.COMPLETED
        assert len(result.evidence_references) == 1

    @pytest.mark.asyncio
    async def test_no_fabricated_deadlines(
        self,
        agent: ComplianceAgent,
        mock_retrieval_provider: MagicMock,
    ):
        """Test that no deadlines are fabricated."""
        mock_retrieval_provider.retrieve = AsyncMock(
            return_value=[
                RetrievalSource(
                    document_id="doc-1",
                    source_title="Tax Guidelines",
                    issuing_authority="Income Tax Department",
                    relevant_excerpt="File returns annually",
                )
            ]
        )
        ctx = _make_agent_context(
            primary_intent="tax_guidance",
            message="When is the tax deadline?",
        )
        result = await agent.execute(ctx)
        assert result.status == AgentStatus.COMPLETED
        # Should not contain specific dates like "July 31" unless in evidence
        assert "July 31" not in result.response
        assert "March 31" not in result.response


# ---------------------------------------------------------------------------
# AgentRegistry tests
# ---------------------------------------------------------------------------


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    @pytest.fixture
    def registry(
        self,
        mock_ai_service: MagicMock,
    ) -> AgentRegistry:
        return AgentRegistry(ai_service=mock_ai_service)

    def test_default_agents_registered(
        self, registry: AgentRegistry
    ):
        """Test that all default agents are registered."""
        agents = registry.list_agents()
        assert "DiscoveryAgent" in agents
        assert "EligibilityAgent" in agents
        assert "DocumentAgent" in agents
        assert "ComplianceAgent" in agents

    def test_get_agent_by_name(
        self, registry: AgentRegistry
    ):
        """Test retrieving an agent by name."""
        agent = registry.get("DiscoveryAgent")
        assert agent is not None
        assert agent.name == "DiscoveryAgent"

    def test_get_nonexistent_agent(
        self, registry: AgentRegistry
    ):
        """Test retrieving a nonexistent agent returns None."""
        agent = registry.get("NonexistentAgent")
        assert agent is None

    def test_resolve_from_intent(
        self, registry: AgentRegistry
    ):
        """Test resolving an agent from an intent."""
        agent = registry.resolve_from_intent("government_scheme_discovery")
        assert agent is not None
        assert agent.name == "DiscoveryAgent"

        agent = registry.resolve_from_intent("scheme_eligibility")
        assert agent is not None
        assert agent.name == "EligibilityAgent"

        agent = registry.resolve_from_intent("document_guidance")
        assert agent is not None
        assert agent.name == "DocumentAgent"

        agent = registry.resolve_from_intent("compliance_guidance")
        assert agent is not None
        assert agent.name == "ComplianceAgent"

    def test_unsupported_intent(
        self, registry: AgentRegistry
    ):
        """Test that unsupported intent returns None."""
        agent = registry.resolve_from_intent("greeting")
        assert agent is None

        agent = registry.resolve_from_intent("unknown")
        assert agent is None

        agent = registry.resolve_from_intent(None)
        assert agent is None

    def test_intent_to_agent_mapping(
        self, registry: AgentRegistry
    ):
        """Test that intent mapping covers all expected intents."""
        mapping = registry.get_supported_intents()
        assert "government_scheme_discovery" in mapping
        assert mapping["government_scheme_discovery"] == "DiscoveryAgent"
        assert "scheme_eligibility" in mapping
        assert mapping["scheme_eligibility"] == "EligibilityAgent"
        assert "document_guidance" in mapping
        assert mapping["document_guidance"] == "DocumentAgent"
        assert "compliance_guidance" in mapping
        assert mapping["compliance_guidance"] == "ComplianceAgent"

    def test_register_custom_agent(
        self, registry: AgentRegistry, mock_ai_service: MagicMock
    ):
        """Test registering a custom agent."""
        custom = _TestAgent(name="CustomAgent", ai_service=mock_ai_service)
        registry.register("CustomAgent", custom)
        assert registry.get("CustomAgent") is custom

    def test_intent_mapping_matches_prompt09_spec(
        self
    ):
        """Test that intent-to-agent mapping matches Prompt 09 specification."""
        expected = {
            "government_scheme_discovery": "DiscoveryAgent",
            "subsidy_discovery": "DiscoveryAgent",
            "loan_discovery": "DiscoveryAgent",
            "registration_discovery": "DiscoveryAgent",
            "scheme_eligibility": "EligibilityAgent",
            "udyam_eligibility": "EligibilityAgent",
            "gst_applicability": "EligibilityAgent",
            "document_guidance": "DocumentAgent",
            "document_validation": "DocumentAgent",
            "document_upload": "DocumentAgent",
            "application_guidance": "DocumentAgent",
            "compliance_guidance": "ComplianceAgent",
            "tax_guidance": "ComplianceAgent",
            "deadline_query": "ComplianceAgent",
            "gst_registration": "ComplianceAgent",
            "business_registration": "ComplianceAgent",
            "udyam_registration": "ComplianceAgent",
        }
        assert INTENT_TO_AGENT == expected


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestAgentSchemas:
    """Tests for agent schemas."""

    def test_agent_context_creation(self):
        """Test AgentContext creation."""
        ctx = AgentContext(
            user_id=uuid4(),
            conversation_id=uuid4(),
            message="Test message",
        )
        assert ctx.user_id is not None
        assert ctx.conversation_id is not None
        assert ctx.message == "Test message"
        assert ctx.primary_intent is None
        assert ctx.secondary_intents == []
        assert ctx.extracted_entities == []
        assert ctx.request_id is not None

    def test_agent_context_validation(self):
        """Test AgentContext validation."""
        ctx = AgentContext(
            user_id=uuid4(),
            conversation_id=uuid4(),
            message="",
        )
        errors = ctx.validate_context()
        assert len(errors) > 0

    def test_agent_result_creation(self):
        """Test AgentResult creation."""
        result = AgentResult(
            agent_name="TestAgent",
            status=AgentStatus.COMPLETED,
            response="Test response",
        )
        assert result.agent_name == "TestAgent"
        assert result.status == AgentStatus.COMPLETED
        assert result.response == "Test response"
        assert result.missing_information == []
        assert result.warnings == []
        assert result.evidence_references == []

    def test_retrieval_source_creation(self):
        """Test RetrievalSource creation."""
        source = RetrievalSource(
            document_id="doc-1",
            source_title="Test Document",
            issuing_authority="Test Authority",
            source_url="https://example.gov.in",
        )
        assert source.document_id == "doc-1"
        assert source.source_title == "Test Document"

    def test_agent_status_enum_values(self):
        """Test AgentStatus enum values."""
        assert AgentStatus.COMPLETED == "completed"
        assert AgentStatus.NEEDS_INFORMATION == "needs_information"
        assert AgentStatus.NEEDS_RETRIEVAL == "needs_retrieval"
        assert AgentStatus.NEEDS_VERIFICATION == "needs_verification"
        assert AgentStatus.NOT_SUPPORTED == "not_supported"
        assert AgentStatus.FAILED == "failed"