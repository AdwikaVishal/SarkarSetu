"""Agent registry for SarkarSetu AI.

Manages registration, retrieval, and intent-based resolution of
specialized agents. Provides dependency injection support and
avoids hardcoded agent instantiation inside the orchestrator.
"""

import logging

from app.services.agents.base import BaseAgent
from app.services.agents.compliance_agent import ComplianceAgent
from app.services.agents.discovery_agent import DiscoveryAgent
from app.services.agents.document_agent import DocumentAgent
from app.services.agents.eligibility_agent import EligibilityAgent
from app.services.ai.ai_service import AIService
from app.services.eligibility import EligibilityEvaluator
from app.services.retrieval import GovernmentKnowledgeProvider

logger = logging.getLogger(__name__)

# Mapping of intent values to agent class names
INTENT_TO_AGENT: dict[str, str] = {
    # Discovery agents
    "government_scheme_discovery": "DiscoveryAgent",
    "subsidy_discovery": "DiscoveryAgent",
    "loan_discovery": "DiscoveryAgent",
    "registration_discovery": "DiscoveryAgent",
    # Eligibility agents
    "scheme_eligibility": "EligibilityAgent",
    "udyam_eligibility": "EligibilityAgent",
    "gst_applicability": "EligibilityAgent",
    # Document agents
    "document_guidance": "DocumentAgent",
    "document_validation": "DocumentAgent",
    "document_upload": "DocumentAgent",
    "application_guidance": "DocumentAgent",
    # Compliance agents
    "compliance_guidance": "ComplianceAgent",
    "tax_guidance": "ComplianceAgent",
    "deadline_query": "ComplianceAgent",
    "gst_registration": "ComplianceAgent",
    "business_registration": "ComplianceAgent",
    "udyam_registration": "ComplianceAgent",
}


class AgentRegistry:
    """Registry for specialized agents.

    Provides:
    - Agent registration and retrieval by name
    - Intent-to-agent resolution
    - Safe rejection of unsupported mappings
    - Dependency injection support
    """

    def __init__(
        self,
        ai_service: AIService,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
        eligibility_evaluator: EligibilityEvaluator | None = None,
    ) -> None:
        self.ai_service = ai_service
        self.retrieval_provider = retrieval_provider
        self.eligibility_evaluator = eligibility_evaluator
        self._agents: dict[str, BaseAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        """Register all built-in agents with shared dependencies."""
        self.register(
            "DiscoveryAgent",
            DiscoveryAgent(
                ai_service=self.ai_service,
                retrieval_provider=self.retrieval_provider,
                eligibility_evaluator=self.eligibility_evaluator,
            ),
        )
        self.register(
            "EligibilityAgent",
            EligibilityAgent(
                ai_service=self.ai_service,
                retrieval_provider=self.retrieval_provider,
                eligibility_evaluator=self.eligibility_evaluator,
            ),
        )
        self.register(
            "DocumentAgent",
            DocumentAgent(
                ai_service=self.ai_service,
                retrieval_provider=self.retrieval_provider,
                eligibility_evaluator=self.eligibility_evaluator,
            ),
        )
        self.register(
            "ComplianceAgent",
            ComplianceAgent(
                ai_service=self.ai_service,
                retrieval_provider=self.retrieval_provider,
                eligibility_evaluator=self.eligibility_evaluator,
            ),
        )

    def register(self, name: str, agent: BaseAgent) -> None:
        """Register an agent by name.

        Args:
            name: Unique agent name.
            agent: Agent instance to register.
        """
        self._agents[name] = agent
        logger.info("Agent registered", extra={"agent_name": name})

    def get(self, name: str) -> BaseAgent | None:
        """Retrieve an agent by name.

        Args:
            name: Agent name.

        Returns:
            Agent instance, or None if not found.
        """
        return self._agents.get(name)

    def resolve_from_intent(self, intent: str | None) -> BaseAgent | None:
        """Resolve an agent from an intent value.

        Args:
            intent: Intent classification result string.

        Returns:
            Matching agent instance, or None if no agent supports
            the intent or intent is None.
        """
        if not intent:
            return None

        agent_name = INTENT_TO_AGENT.get(intent)
        if not agent_name:
            return None

        return self.get(agent_name)

    def get_supported_intents(self) -> dict[str, str]:
        """Get the full intent-to-agent mapping.

        Returns:
            Dictionary mapping intent values to agent names.
        """
        return dict(INTENT_TO_AGENT)

    def is_intent_supported(self, intent: str | None) -> bool:
        """Check if an intent is supported by any registered agent.

        Args:
            intent: Intent classification result string.

        Returns:
            True if an agent supports the intent, False otherwise.
        """
        return self.resolve_from_intent(intent) is not None

    def list_agents(self) -> list[str]:
        """List all registered agent names.

        Returns:
            List of agent names.
        """
        return list(self._agents.keys())
