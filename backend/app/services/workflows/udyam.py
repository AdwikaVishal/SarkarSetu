"""Udyam Registration workflow for SarkarSetu AI.

Handles Udyam registration guidance workflow:
1. Understand the user's business registration needs
2. Load/create business profile
3. Identify missing business information
4. Ask targeted clarification questions
5. Retrieve official Udyam registration guidance
6. Run deterministic eligibility assessment if rule set exists
7. Generate document and information checklist
8. Generate next-step action plan
9. Provide official portal references

Critical restriction: Never invent registration requirements, eligibility
thresholds, document lists, or fees. If official evidence is unavailable,
mark the affected step NEEDS_RETRIEVAL or NEEDS_VERIFICATION.
"""

import logging
from typing import Any
from uuid import UUID

from app.schemas.agents import RetrievalSource
from app.services.ai.ai_service import AIService
from app.services.conversation.clarification_service import (
    ClarificationService,
)
from app.services.conversation.conversation_service import (
    ConversationService,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.retrieval import GovernmentKnowledgeProvider

from .base import BaseWorkflow
from .context import WorkflowContext
from .workflow_result import WorkflowStepResult

logger = logging.getLogger(__name__)


class UdyamRegistrationWorkflow(BaseWorkflow):
    """Handles Udyam registration workflow.

    Guides users through Udyam registration process:
    1. Understand business requirements
    2. Collect business information
    3. Retrieve official Udyam registration guidance
    4. Run deterministic eligibility assessment if rules exist
    5. Generate document checklist
    6. Provide next-step action plan
    """

    SUPPORTED_INTENTS = {
        "udyam_registration",
        "udyam_eligibility",
        "business_registration",
    }

    # Business attributes needed for Udyam registration
    REQUIRED_ATTRIBUTES = [
        "business_name",
        "business_type",
        "state",
        "district",
        "annual_turnover",
        "employee_count",
        "establishment_date",
    ]

    def __init__(
        self,
        ai_service: AIService,
        conversation_service: ConversationService,
        clarification_service: ClarificationService,
        eligibility_engine: EligibilityEngine,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
    ) -> None:
        super().__init__(
            name="UdyamRegistrationWorkflow",
            service_type="udyam_registration",
            ai_service=ai_service,
            conversation_service=conversation_service,
            clarification_service=clarification_service,
            eligibility_engine=eligibility_engine,
            retrieval_provider=retrieval_provider,
        )

    async def _execute_steps(
        self,
        context: WorkflowContext,
    ) -> list[WorkflowStepResult]:
        """Execute Udyam registration workflow steps.

        Steps:
        1. Extract business attributes from entities
        2. Identify missing required attributes
        3. If missing, request clarification
        4. If complete, retrieve Udyam registration guidance
        5. Run eligibility assessment if rule set exists
        6. Generate document checklist
        7. Provide next-step action plan
        """
        intent = context.primary_intent or ""
        if intent not in self.SUPPORTED_INTENTS:
            return [
                WorkflowStepResult(
                    step_id="validate_intent",
                    step_name="validate_intent",
                    status="failed",
                    response="This workflow does not support the requested intent.",
                    warnings=[
                        f"Intent '{intent}' is not supported by "
                        f"UdyamRegistrationWorkflow."
                    ],
                )
            ]

        # Step 1: Extract business attributes from entities
        business_attributes = self._extract_business_attributes(
            context.extracted_entities
        )

        # Step 2: Identify missing required attributes
        missing = self._identify_missing_attributes(business_attributes)

        # Step 3: If information is missing, ask for clarification
        if missing:
            return [
                WorkflowStepResult(
                    step_id="clarify_info",
                    step_name="clarify_missing_info",
                    status="needs_information",
                    response=self._build_missing_info_response(
                        missing, intent
                    ),
                    missing_information=missing,
                    clarification_question=self._build_clarification_question(
                        missing
                    ),
                    evidence_references=[],
                    warnings=[
                        "Official-source verification is required before "
                        "scheme-specific claims."
                    ],
                )
            ]

        # Step 4: Retrieve Udyam registration guidance
        discovery_query = self._build_discovery_query(
            message=context.message,
            business_attributes=business_attributes,
            intent=intent,
        )

        if not self.retrieval_provider:
            return [
                WorkflowStepResult(
                    step_id="retrieve_guidance",
                    step_name="retrieve_udyam_guidance",
                    status="needs_retrieval",
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
                        "Government document retrieval provider is not available. "
                        "Official-source verification is required before "
                        "scheme-specific claims."
                    ],
                )
            ]

        evidence = await self.retrieval_provider.retrieve(
            query=discovery_query,
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            filters={"scheme_or_scheme": ["udyam_registration"]},
            limit=5,
        )

        if not evidence:
            return [
                WorkflowStepResult(
                    step_id="retrieve_guidance",
                    step_name="retrieve_udyam_guidance",
                    status="needs_retrieval",
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
                        "scheme-specific claims."
                    ],
                )
            ]

        # Step 5: Run eligibility assessment if rule set exists
        eligibility_result = await self._evaluate_eligibility(
            conversation_id=context.conversation_id,
            user_id=context.user_id,
            business_attributes=business_attributes,
        )

        # Step 6: Generate document checklist
        checklist = self._build_document_checklist(evidence)

        # Step 7: Build final response
        return [
            WorkflowStepResult(
                step_id="build_response",
                step_name="build_udyam_response",
                status="completed",
                response=self._build_udyam_response(
                    evidence, checklist, eligibility_result, intent
                ),
                structured_data={
                    "discovery_query": discovery_query,
                    "business_attributes": business_attributes,
                    "intent": intent,
                    "retrieved_guidance": [
                        {
                            "source_title": s.source_title,
                            "issuing_authority": s.issuing_authority,
                            "relevant_excerpt": s.relevant_excerpt,
                            "page_or_section": s.page_or_section,
                        }
                        for s in evidence
                    ],
                    "eligibility_assessment": eligibility_result,
                    "checklist": checklist,
                },
                missing_information=[],
                clarification_question=None,
                evidence_references=[
                    {
                        "document_id": s.document_id,
                        "source_title": s.source_title,
                        "issuing_authority": s.issuing_authority,
                        "source_url": s.source_url,
                        "relevant_excerpt": s.relevant_excerpt,
                        "page_or_section": s.page_or_section,
                        "retrieval_score": s.retrieval_score,
                        "document_version": s.document_version,
                    }
                    for s in evidence
                ],
                warnings=[
                    "Verify scheme details on official government websites "
                    "before applying."
                ],
            )
        ]

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _extract_business_attributes(
        self,
        entities: list[dict[str, Any]],
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
        self,
        attributes: dict[str, Any],
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
        self,
        missing: list[str],
        intent: str,
    ) -> str:
        """Build response when business information is missing."""
        intent_label = intent.replace("_", " ").title()
        missing_list = "\n".join(
            f"- {m.replace('_', ' ')}" for m in missing
        )
        return (
            f"To help you with {intent_label.lower()}, I need a "
            f"few more details about your business:\n{missing_list}\n\n"
            "Please provide this information so I can proceed with "
            "your Udyam registration guidance."
        )

    def _build_clarification_question(
        self,
        missing: list[str],
    ) -> str:
        """Build a clarification question for missing attributes."""
        if len(missing) == 1:
            return f"What is your business {missing[0].replace('_', ' ')}?"
        missing_list = ", ".join(
            m.replace("_", " ") for m in missing[:-1]
        )
        return (
            f"Could you provide your business {missing_list} and "
            f"{missing[-1].replace('_', ' ')}?"
        )

    def _build_no_evidence_response(
        self,
        intent: str,
    ) -> str:
        """Build response when retrieval is unavailable."""
        intent_label = intent.replace("_", " ").title()
        return (
            f"I understand you're looking for {intent_label.lower()}. "
            "However, I cannot retrieve official government guidance "
            "at this time. Please consult the Udyam registration portal "
            "or a qualified professional for accurate information."
        )

    async def _evaluate_eligibility(
        self,
        conversation_id: UUID,
        user_id: UUID,
        business_attributes: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Run eligibility assessment if rule set exists.

        Args:
            conversation_id: Conversation ID.
            user_id: User ID.
            business_attributes: Business attributes extracted from message.

        Returns:
            Eligibility assessment result dict, or None if not available.
        """
        from app.services.eligibility import EligibilityAssessmentRequest

        try:
            result = await self.eligibility_engine.evaluate(
                EligibilityAssessmentRequest(
                    user_id=user_id,
                    business_profile_id=None,
                    scheme_name="udyam_registration",
                    registration_type="udyam_registration",
                    business_attributes=business_attributes,
                    missing_information=[],
                    context={
                        "conversation_id": str(conversation_id),
                        "user_message": "",
                        "primary_intent": "udyam_registration",
                    },
                )
            )
            return {
                "assessment_id": result.assessment_id,
                "scheme_name": result.scheme_name,
                "registration_type": result.registration_type,
                "assessment_status": result.assessment_status,
                "rule_set_version": result.rule_set_version,
                "result_data": result.result_data,
                "missing_information": result.missing_information,
                "evidence_references": result.evidence_references,
                "warnings": result.warnings,
            }
        except Exception as exc:  # noqa: BLE001 - safe error handling
            logger.warning(
                "Eligibility evaluation failed",
                extra={
                    "error": str(exc),
                },
            )
            return None

    def _build_document_checklist(
        self,
        evidence: list[RetrievalSource],
    ) -> list[dict[str, Any]]:
        """Build a document checklist from retrieved evidence."""
        checklist: list[dict[str, Any]] = []
        for i, source in enumerate(evidence, 1):
            item = {
                "id": i,
                "document_name": source.source_title
                or "Untitled document",
                "purpose": source.relevant_excerpt
                or "No description available",
                "mandatory": None,
                "accepted_format": None,
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

    def _build_udyam_response(
        self,
        evidence: list[RetrievalSource],
        checklist: list[dict[str, Any]],
        eligibility_result: dict[str, Any] | None,
        intent: str,
    ) -> str:
        """Build user-facing Udyam registration response."""
        intent_label = intent.replace("_", " ").title()
        lines = [
            f"Udyam Registration Guidance for {intent_label.lower()}:\n",
        ]
        for i, source in enumerate(evidence, 1):
            lines.append(
                f"{i}. {source.source_title or 'Untitled source'}"
            )
            if source.issuing_authority:
                lines.append(
                    f"   Authority: {source.issuing_authority}"
                )
            if source.relevant_excerpt:
                lines.append(
                    f"   Guidance: {source.relevant_excerpt[:300]}..."
                )
            if source.page_or_section:
                lines.append(
                    f"   Reference: {source.page_or_section}"
                )
            lines.append("")
        lines.append(
            "Important: This is general guidance, not personalized legal "
            "or tax advice. Consult a qualified professional for your "
            "specific situation. Verify all deadlines, fees, and "
            "requirements on official government websites before taking "
            "action."
        )
        return "\n".join(lines)
