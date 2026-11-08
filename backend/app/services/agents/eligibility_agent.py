"""Eligibility Agent for SarkarSetu AI.

Collects information needed for scheme eligibility assessment and
coordinates with the deterministic eligibility engine.

Supported intents:
- SCHEME_ELIGIBILITY
- UDYAM_ELIGIBILITY
- GST_APPLICABILITY

Critical architectural rule: The LLM must NEVER independently decide
whether a user is eligible or ineligible. The deterministic eligibility
engine (Prompt 10) is the sole authority for eligibility decisions.
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


class EligibilityAgent(BaseAgent):
    """Coordinates eligibility assessment with the deterministic engine.

    Identifies the scheme/registration being assessed, collects
    business information, identifies missing fields, asks targeted
    clarification questions, and passes the request to the
    deterministic eligibility engine when available.

    Never makes independent eligibility decisions.
    """

    SUPPORTED_INTENTS = {
        "scheme_eligibility",
        "udyam_eligibility",
        "gst_applicability",
    }

    # Business attributes commonly needed for eligibility assessment
    ELIGIBILITY_ATTRIBUTES = [
        "business_type",
        "industry",
        "state",
        "district",
        "annual_turnover",
        "employee_count",
        "business_stage",
        "establishment_date",
    ]

    def __init__(
        self,
        ai_service: AIService,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
        eligibility_evaluator: EligibilityEvaluator | None = None,
    ) -> None:
        super().__init__(
            name="EligibilityAgent",
            ai_service=ai_service,
            retrieval_provider=retrieval_provider,
            eligibility_evaluator=eligibility_evaluator,
        )

    async def _execute(self, context: AgentContext) -> AgentResult:
        """Execute eligibility agent logic.

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

        # Determine the scheme/registration being assessed
        assessment_target = self._determine_assessment_target(intent)

        # If we have missing information, ask for it first
        if missing:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.NEEDS_INFORMATION,
                response=self._build_missing_info_response(
                    missing, assessment_target
                ),
                structured_data={
                    "assessment_target": assessment_target,
                    "business_attributes": business_attributes,
                    "missing_attributes": missing,
                    "intent": intent,
                },
                missing_information=missing,
                clarification_question=self._build_clarification_question(
                    missing, assessment_target
                ),
                evidence_references=[],
                warnings=[
                    "Eligibility decisions require verified business "
                    "information and official rule evaluation.",
                ],
            )

        # We have enough information - delegate to deterministic engine
        assessment_result = await self.evaluate_eligibility(
            scheme_name=assessment_target,
            registration_type=(
                intent if "registration" in intent else None
            ),
            business_attributes=business_attributes,
            missing_information=[],
            context={
                "conversation_id": str(context.conversation_id),
                "user_message": context.message,
                "primary_intent": intent,
            },
            user_id=context.user_id,
        )

        # Build response from engine result
        return self._build_engine_response(assessment_result, intent)

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
        for attr in self.ELIGIBILITY_ATTRIBUTES:
            if attr not in attributes or not attributes[attr]:
                missing.append(attr)
        return missing

    def _determine_assessment_target(self, intent: str) -> str:
        """Determine the scheme or registration being assessed."""
        mapping = {
            "scheme_eligibility": "Government scheme eligibility",
            "udyam_eligibility": "Udyam registration eligibility",
            "gst_applicability": "GST registration applicability",
        }
        return mapping.get(intent, "Eligibility assessment")

    def _build_missing_info_response(
        self, missing: list[str], assessment_target: str
    ) -> str:
        """Build response when eligibility information is missing."""
        missing_list = "\n".join(f"- {m.replace('_', ' ')}" for m in missing)
        return (
            f"To assess your {assessment_target.lower()}, I need "
            "the following business details:\n{missing_list}\n\n"
            "Please provide this information so I can prepare an "
            "eligibility assessment request for official evaluation."
        ).replace("{missing_list}", missing_list)

    def _build_clarification_question(
        self, missing: list[str], assessment_target: str
    ) -> str:
        """Build a clarification question for missing attributes."""
        if len(missing) == 1:
            return (
                f"What is your business {missing[0].replace('_', ' ')}? "
                f"This is needed for {assessment_target.lower()}."
            )
        missing_list = ", ".join(m.replace("_", " ") for m in missing[:-1])
        return (
            f"Could you provide your business {missing_list} and "
            f"{missing[-1].replace('_', ' ')}? These are needed for "
            f"{assessment_target.lower()}."
        )

    def _build_engine_response(
        self,
        result: Any,  # EligibilityAssessmentResult
        intent: str,
    ) -> AgentResult:
        """Build AgentResult from deterministic engine result."""
        status = result.assessment_status

        # Map engine status to agent status
        if status in ("eligible", "ineligible", "partial"):
            agent_status = AgentStatus.COMPLETED
        elif status == "verification_required":
            agent_status = AgentStatus.NEEDS_VERIFICATION
        else:
            agent_status = AgentStatus.NEEDS_VERIFICATION

        # Build evidence references from engine result
        evidence: list[RetrievalSource] = []
        for ref in result.evidence_references:
            evidence.append(
                RetrievalSource(
                    document_id=ref.get("document_id"),
                    source_title=ref.get("source_title"),
                    issuing_authority=ref.get("issuing_authority"),
                    source_url=ref.get("source_url"),
                    publication_date=ref.get("publication_date"),
                    relevant_excerpt=ref.get("relevant_excerpt"),
                    page_or_section=ref.get("page_or_section"),
                    retrieval_score=ref.get("retrieval_score"),
                    document_version=ref.get("document_version"),
                )
            )

        # Build user-facing response
        response = self._build_user_response(result, intent)

        return AgentResult(
            agent_name=self.name,
            status=agent_status,
            response=response,
            structured_data={
                "assessment_id": result.assessment_id,
                "scheme_name": result.scheme_name,
                "registration_type": result.registration_type,
                "assessment_status": result.assessment_status,
                "rule_set_version": result.rule_set_version,
                "result_data": result.result_data,
                "intent": intent,
            },
            missing_information=list(result.missing_information),
            clarification_question=None,
            warnings=list(result.warnings),
            evidence_references=evidence,
            handoff_required=False,
        )

    def _build_user_response(
        self, result: Any, intent: str
    ) -> str:
        """Build user-facing response from engine result."""
        status = result.assessment_status
        target = (
            result.scheme_name or result.registration_type or "this scheme"
        )

        if status == "verification_required":
            return (
                f"Eligibility verification for {target} requires official "
                "rule evaluation. The deterministic eligibility engine is "
                "not yet configured. Please consult official government "
                "resources or a qualified professional for guidance."
            )

        if status == "eligible":
            return (
                f"Based on the evaluated rules, your business appears to "
                f"meet the eligibility criteria for {target}. Please "
                "verify this on official government websites before "
                "proceeding with any application."
            )

        if status == "ineligible":
            return (
                f"Based on the evaluated rules, your business does not "
                f"appear to meet the eligibility criteria for {target}. "
                "Please consult official government resources or a "
                "qualified professional for guidance on alternatives."
            )

        if status == "partial":
            return (
                f"Your business partially meets the eligibility criteria "
                f"for {target}. Additional information or documentation "
                "may be required. Please consult official government "
                "resources for complete details."
            )

        return (
            f"Eligibility assessment for {target} could not be completed "
            "at this time. Please consult official government resources "
            "or a qualified professional for guidance."
        )
