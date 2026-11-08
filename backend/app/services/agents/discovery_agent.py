"""Discovery Agent for SarkarSetu AI.

Understands an entrepreneur's business requirements and prepares a
grounded government-scheme discovery request.

Supported intents:
- SCHEME_DISCOVERY
- SUBSIDY_DISCOVERY
- LOAN_DISCOVERY
- REGISTRATION_DISCOVERY

Critical restriction: Never fabricate scheme names, funding amounts,
deadlines, benefits, or eligibility requirements. If RAG is
unavailable, return NEEDS_RETRIEVAL.
"""

import logging
from typing import Any

from app.schemas.agents import (
    AgentContext,
    AgentResult,
    AgentStatus,
    RetrievalSource,
)
from app.services.agents.base import BaseAgent
from app.services.ai.ai_service import AIService
from app.services.eligibility import EligibilityEvaluator
from app.services.retrieval import GovernmentKnowledgeProvider

logger = logging.getLogger(__name__)


class DiscoveryAgent(BaseAgent):
    """Prepares grounded government-scheme discovery requests.

    Understands business objectives, extracts relevant business
    information, identifies missing information, and prepares a
    structured discovery query. Requests official-source retrieval
    when available and returns grounded results with citations.
    """

    SUPPORTED_INTENTS = {
        "government_scheme_discovery",
        "subsidy_discovery",
        "loan_discovery",
        "registration_discovery",
    }

    # Business attributes needed for useful discovery
    REQUIRED_ATTRIBUTES = [
        "business_type",
        "industry",
        "state",
        "district",
        "annual_turnover",
        "employee_count",
        "business_stage",
    ]

    def __init__(
        self,
        ai_service: AIService,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
        eligibility_evaluator: EligibilityEvaluator | None = None,
    ) -> None:
        super().__init__(
            name="DiscoveryAgent",
            ai_service=ai_service,
            retrieval_provider=retrieval_provider,
            eligibility_evaluator=eligibility_evaluator,
        )

    async def _execute(self, context: AgentContext) -> AgentResult:
        """Execute discovery agent logic.

        Args:
            context: Validated agent context.

        Returns:
            Typed agent result.
        """
        intent = context.primary_intent or ""
        if intent not in self.SUPPORTED_INTENTS:
            return self.build_safe_error_response(
                message="This agent does not support the requested intent.",
                status=AgentStatus.NOT_SUPPORTED,
            )

        # Extract business attributes from entities
        business_attributes = self._extract_business_attributes(
            context.extracted_entities
        )

        # Identify missing required attributes
        missing = self._identify_missing_attributes(business_attributes)

        # Prepare discovery query
        discovery_query = self._build_discovery_query(
            message=context.message,
            business_attributes=business_attributes,
            intent=intent,
        )

        # Attempt retrieval if we have enough context
        evidence: list[RetrievalSource] = []
        retrieval_available = False

        if not missing:
            # We have enough context to search
            evidence = await self.retrieve_evidence(
                query=discovery_query,
                context=context,
                filters=None,
                limit=5,
            )
            retrieval_available = len(evidence) > 0

        # Build result
        if missing:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.NEEDS_INFORMATION,
                response=self._build_missing_info_response(missing, intent),
                structured_data={
                    "discovery_query": discovery_query,
                    "business_attributes": business_attributes,
                    "missing_attributes": missing,
                    "intent": intent,
                },
                missing_information=missing,
                clarification_question=self._build_clarification_question(missing),
                evidence_references=evidence,
                warnings=[
                    "Official-source verification is required before scheme-specific claims."
                ],
            )

        if not retrieval_available:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.NEEDS_RETRIEVAL,
                response=self._build_no_evidence_response(intent),
                structured_data={
                    "discovery_query": discovery_query,
                    "business_attributes": business_attributes,
                    "intent": intent,
                },
                missing_information=[],
                clarification_question=None,
                evidence_references=[],
                warnings=[
                    "Government document retrieval is not available. "
                    "Official-source verification is required before "
                    "scheme-specific claims.",
                ],
            )

        # We have evidence - build grounded response
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            response=self._build_grounded_response(evidence, intent),
            structured_data={
                "discovery_query": discovery_query,
                "business_attributes": business_attributes,
                "intent": intent,
                "retrieved_schemes": [
                    {
                        "source_title": s.source_title,
                        "issuing_authority": s.issuing_authority,
                        "relevant_excerpt": s.relevant_excerpt,
                        "page_or_section": s.page_or_section,
                    }
                    for s in evidence
                ],
            },
            missing_information=[],
            clarification_question=None,
            evidence_references=evidence,
            warnings=[
                "Verify scheme details on official government websites "
                "before applying.",
            ],
            handoff_required=False,
        )

    def _extract_business_attributes(
        self, entities: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Extract business attributes from extracted entities."""
        attributes: dict[str, Any] = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "")
            value = entity.get("value", "")
            if not value:
                continue

            mapping = {
                "business_name": "business_name",
                "business_type": "business_type",
                "industry": "industry",
                "business_stage": "business_stage",
                "state": "state",
                "district": "district",
                "city": "city",
                "pin_code": "pin_code",
                "employee_count": "employee_count",
                "annual_turnover": "annual_turnover",
                "establishment_date": "establishment_date",
                "products_services": "products_services",
                "operating_mode": "operating_mode",
            }
            if entity_type in mapping:
                attributes[mapping[entity_type]] = value

        return attributes

    def _identify_missing_attributes(
        self, attributes: dict[str, Any]
    ) -> list[str]:
        """Identify which required attributes are missing."""
        missing = []
        for attr in self.REQUIRED_ATTRIBUTES:
            if attr not in attributes or not attributes[attr]:
                missing.append(attr)
        return missing

    def _build_discovery_query(
        self,
        message: str,
        business_attributes: dict[str, Any],
        intent: str,
    ) -> str:
        """Build a structured discovery query for retrieval."""
        parts = [f"User request: {message}"]
        parts.append(f"Intent: {intent}")
        if business_attributes:
            parts.append("Business context:")
            for key, value in business_attributes.items():
                parts.append(f"  - {key}: {value}")
        return "\n".join(parts)

    def _build_missing_info_response(
        self, missing: list[str], intent: str
    ) -> str:
        """Build response when business information is missing."""
        intent_label = intent.replace("_", " ").title()
        missing_list = "\n".join(f"- {m.replace('_', ' ')}" for m in missing)
        return (
            f"To help you find relevant {intent_label.lower()}, I need a "
            f"few more details about your business:\n{missing_list}\n\n"
            "Please provide this information so I can search for "
            "appropriate government schemes and programs."
        )

    def _build_clarification_question(self, missing: list[str]) -> str:
        """Build a clarification question for missing attributes."""
        if len(missing) == 1:
            return f"What is your business {missing[0].replace('_', ' ')}?"
        missing_list = ", ".join(m.replace("_", " ") for m in missing[:-1])
        return (
            f"Could you provide your business {missing_list} and "
            f"{missing[-1].replace('_', ' ')}?"
        )

    def _build_no_evidence_response(self, intent: str) -> str:
        """Build response when retrieval is unavailable."""
        intent_label = intent.replace("_", " ").title()
        return (
            f"I understand you're looking for {intent_label.lower()}. "
            "However, I cannot search official government sources at "
            "this time. Once document retrieval is available, I'll be "
            "able to search for relevant schemes and programs based on "
            "your business details. Please try again later or consult "
            "official government websites directly."
        )

    def _build_grounded_response(
        self, evidence: list[RetrievalSource], intent: str
    ) -> str:
        """Build a grounded response using retrieved evidence."""
        intent_label = intent.replace("_", " ").title()
        lines = [
            f"Based on available government sources, here's information "
            f"related to {intent_label.lower()}:\n",
        ]
        for i, source in enumerate(evidence, 1):
            lines.append(f"{i}. {source.source_title or 'Untitled source'}")
            if source.issuing_authority:
                lines.append(f"   Authority: {source.issuing_authority}")
            if source.relevant_excerpt:
                lines.append(f"   Excerpt: {source.relevant_excerpt[:200]}...")
            if source.page_or_section:
                lines.append(f"   Reference: {source.page_or_section}")
            lines.append("")
        lines.append(
            "Please verify scheme details on official government websites "
            "before applying. This information is for guidance only and "
            "does not constitute official approval."
        )
        return "\n".join(lines)
