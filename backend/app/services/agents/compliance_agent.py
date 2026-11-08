"""Compliance Agent for SarkarSetu AI.

Provides structured, evidence-backed guidance on business registration
and compliance questions.

Supported intents:
- COMPLIANCE_GUIDANCE
- TAX_GUIDANCE
- DEADLINE_QUERY
- GST_REGISTRATION
- BUSINESS_REGISTRATION
- UDYAM_REGISTRATION

Critical restrictions:
- Never independently determine legal or tax obligations.
- Never invent filing deadlines, penalties, fees, or statutory thresholds.
- Never treat outdated information as current.
- Never claim official approval.
- Never present general guidance as personalized legal advice.
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


class ComplianceAgent(BaseAgent):
    """Provides evidence-backed compliance guidance.

    Understands compliance questions, identifies relevant registration
    or regulatory topics, collects business details, requests official
    evidence, and explains verified information in accessible language.
    """

    SUPPORTED_INTENTS = {
        "compliance_guidance",
        "tax_guidance",
        "deadline_query",
        "gst_registration",
        "business_registration",
        "udyam_registration",
    }

    def __init__(
        self,
        ai_service: AIService,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
        eligibility_evaluator: EligibilityEvaluator | None = None,
    ) -> None:
        super().__init__(
            name="ComplianceAgent",
            ai_service=ai_service,
            retrieval_provider=retrieval_provider,
            eligibility_evaluator=eligibility_evaluator,
        )

    async def _execute(self, context: AgentContext) -> AgentResult:
        """Execute compliance agent logic.

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

        # Identify the compliance topic
        topic = self._identify_compliance_topic(intent)

        # Attempt to retrieve official evidence
        evidence = await self.retrieve_evidence(
            query=self._build_compliance_query(intent, topic, business_attributes),
            context=context,
            filters=None,
            limit=5,
        )

        if not evidence:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.NEEDS_RETRIEVAL,
                response=self._build_no_evidence_response(intent, topic),
                structured_data={
                    "compliance_topic": topic,
                    "intent": intent,
                    "business_attributes": business_attributes,
                },
                missing_information=[],
                clarification_question=None,
                evidence_references=[],
                warnings=[
                    "Official compliance guidance is not available. "
                    "Please consult a qualified professional or the "
                    "relevant government department.",
                ],
            )

        # Build compliance response from evidence
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            response=self._build_compliance_response(evidence, topic, intent),
            structured_data={
                "compliance_topic": topic,
                "intent": intent,
                "business_attributes": business_attributes,
                "retrieved_guidance": [
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
                "This is general guidance, not personalized legal or tax advice. "
                "Consult a qualified professional for your specific situation.",
                "Verify all deadlines, fees, and requirements on official "
                "government websites.",
            ],
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
                "registration_type": "registration_type",
                "registration_number": "registration_number",
            }
            if entity_type in mapping:
                attributes[mapping[entity_type]] = value

        return attributes

    def _identify_compliance_topic(self, intent: str) -> str:
        """Identify the compliance topic from intent."""
        mapping = {
            "compliance_guidance": "General compliance guidance",
            "tax_guidance": "Tax compliance guidance",
            "deadline_query": "Filing deadline inquiry",
            "gst_registration": "GST registration",
            "business_registration": "Business registration",
            "udyam_registration": "Udyam registration",
        }
        return mapping.get(intent, "Compliance guidance")

    def _build_compliance_query(
        self,
        intent: str,
        topic: str,
        business_attributes: dict[str, Any],
    ) -> str:
        """Build a compliance guidance retrieval query."""
        parts = [
            f"Intent: {intent}",
            f"Topic: {topic}",
        ]
        if business_attributes:
            parts.append("Business context:")
            for key, value in business_attributes.items():
                parts.append(f"  - {key}: {value}")
        parts.append(
            "Official compliance requirements, deadlines, fees, and procedures"
        )
        return "\n".join(parts)

    def _build_no_evidence_response(
        self, intent: str, topic: str
    ) -> str:
        """Build response when compliance evidence is unavailable."""
        intent_label = intent.replace("_", " ").title()
        return (
            f"I understand you need {intent_label.lower()} for "
            f"{topic.lower()}. However, I cannot retrieve official "
            "compliance guidance at this time. Please consult a "
            "qualified professional (chartered accountant, company "
            "secretary, or lawyer) or the relevant government "
            "department for accurate compliance information."
        )

    def _build_compliance_response(
        self,
        evidence: list[RetrievalSource],
        topic: str,
        intent: str,
    ) -> str:
        """Build user-facing compliance response."""
        lines = [
            f"Compliance guidance for {topic}:\n",
        ]
        for i, source in enumerate(evidence, 1):
            lines.append(f"{i}. {source.source_title or 'Untitled source'}")
            if source.issuing_authority:
                lines.append(f"   Authority: {source.issuing_authority}")
            if source.relevant_excerpt:
                lines.append(f"   Guidance: {source.relevant_excerpt[:300]}...")
            if source.page_or_section:
                lines.append(f"   Reference: {source.page_or_section}")
            lines.append("")
        lines.append(
            "Important: This is general guidance, not personalized "
            "legal or tax advice. Filing deadlines, fees, penalties, "
            "and statutory thresholds may vary by state, business type, "
            "and other factors. Consult a qualified professional and "
            "verify all requirements on official government websites "
            "before taking action."
        )
        return "\n".join(lines)
