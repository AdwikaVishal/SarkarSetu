"""Document Agent for SarkarSetu AI.

Guides users through government-service document requirements and
document preparation.

Supported intents:
- DOCUMENT_GUIDANCE
- DOCUMENT_VALIDATION
- DOCUMENT_UPLOAD
- APPLICATION_GUIDANCE

Critical restrictions:
- Never invent mandatory document requirements.
- Never claim a document has been officially verified merely because
  it was uploaded.
- Never expose uploaded document storage keys.
- Never log document contents.
- Never treat OCR output as verified official information.
- Never claim that an application was submitted.
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


class DocumentAgent(BaseAgent):
    """Guides users through government document requirements.

    Identifies relevant registration/scheme/application, requests
    document requirements from retrieval, generates structured
    checklists from verified evidence, and identifies missing
    documents.
    """

    SUPPORTED_INTENTS = {
        "document_guidance",
        "document_validation",
        "document_upload",
        "application_guidance",
    }

    def __init__(
        self,
        ai_service: AIService,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
        eligibility_evaluator: EligibilityEvaluator | None = None,
    ) -> None:
        super().__init__(
            name="DocumentAgent",
            ai_service=ai_service,
            retrieval_provider=retrieval_provider,
            eligibility_evaluator=eligibility_evaluator,
        )

    async def _execute(self, context: AgentContext) -> AgentResult:
        """Execute document agent logic.

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

        # Extract business context from entities
        business_attributes = self._extract_business_attributes(
            context.extracted_entities
        )

        # Identify the relevant service/application
        service_name = self._identify_service(intent, context.message)

        # Attempt to retrieve document requirements
        evidence = await self.retrieve_evidence(
            query=self._build_document_query(intent, service_name, business_attributes),
            context=context,
            filters=None,
            limit=5,
        )

        if not evidence:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.NEEDS_RETRIEVAL,
                response=self._build_no_requirements_response(intent, service_name),
                structured_data={
                    "service_name": service_name,
                    "intent": intent,
                    "business_attributes": business_attributes,
                },
                missing_information=[],
                clarification_question=None,
                evidence_references=[],
                warnings=[
                    "Official document requirements are not available. "
                    "Please consult the relevant government department "
                    "directly.",
                ],
            )

        # Build document checklist from evidence
        checklist = self._build_checklist(evidence, service_name)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            response=self._build_document_response(checklist, service_name, intent),
            structured_data={
                "service_name": service_name,
                "intent": intent,
                "business_attributes": business_attributes,
                "checklist": checklist,
            },
            missing_information=[],
            clarification_question=None,
            evidence_references=evidence,
            warnings=[
                "Document requirements may vary by state and scheme. "
                "Verify on official government websites.",
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

    def _identify_service(self, intent: str, message: str) -> str:
        """Identify the relevant service or application."""
        mapping = {
            "document_guidance": "Government service document requirements",
            "document_validation": "Document validation",
            "document_upload": "Document upload",
            "application_guidance": "Application guidance",
        }
        return mapping.get(intent, "Document guidance")

    def _build_document_query(
        self,
        intent: str,
        service_name: str,
        business_attributes: dict[str, Any],
    ) -> str:
        """Build a document requirements retrieval query."""
        parts = [
            f"Intent: {intent}",
            f"Service: {service_name}",
        ]
        if business_attributes:
            parts.append("Business context:")
            for key, value in business_attributes.items():
                parts.append(f"  - {key}: {value}")
        parts.append(
            "Required documents, accepted formats, and verification status"
        )
        return "\n".join(parts)

    def _build_no_requirements_response(
        self, intent: str, service_name: str
    ) -> str:
        """Build response when document requirements are unavailable."""
        intent_label = intent.replace("_", " ").title()
        return (
            f"I understand you need {intent_label.lower()} for "
            f"{service_name.lower()}. However, I cannot retrieve "
            "official document requirements at this time. Please "
            "consult the relevant government department or official "
            "website for document requirements."
        )

    def _build_checklist(
        self, evidence: list[RetrievalSource], service_name: str
    ) -> list[dict[str, Any]]:
        """Build a document checklist from retrieved evidence."""
        checklist: list[dict[str, Any]] = []
        for i, source in enumerate(evidence, 1):
            item = {
                "id": i,
                "document_name": source.source_title or "Untitled document",
                "purpose": source.relevant_excerpt or "No description available",
                "mandatory": None,  # Never invent mandatory status
                "accepted_format": None,  # Never invent format
                "evidence_reference": {
                    "source_title": source.source_title,
                    "issuing_authority": source.issuing_authority,
                    "source_url": source.source_url,
                    "page_or_section": source.page_or_section,
                },
                "verification_status": "unverified",
                "user_action_required": True,
            }
            checklist.append(item)
        return checklist

    def _build_document_response(
        self,
        checklist: list[dict[str, Any]],
        service_name: str,
        intent: str,
    ) -> str:
        """Build user-facing document response."""
        lines = [
            f"Document requirements for {service_name}:\n",
        ]
        for item in checklist:
            lines.append(f"{item['id']}. {item['document_name']}")
            if item["purpose"]:
                lines.append(f"   Purpose: {item['purpose'][:200]}")
            lines.append(
                f"   Verification status: {item['verification_status']}"
            )
            lines.append(
                f"   Evidence: {item['evidence_reference'].get('source_title', 'N/A')}"
            )
            if item["evidence_reference"].get("issuing_authority"):
                lines.append(
                    f"   Authority: {item['evidence_reference']['issuing_authority']}"
                )
            lines.append("")
        lines.append(
            "Note: Document requirements may vary by state and scheme. "
            "Verify on official government websites before submitting "
            "any documents. Uploaded documents are not officially "
            "verified until reviewed by the relevant authority."
        )
        return "\n".join(lines)
