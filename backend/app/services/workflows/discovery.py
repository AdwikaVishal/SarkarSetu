"""Discovery workflow for SarkarSetu AI.

Handles government scheme discovery workflows:
- GOVERNMENT_SCHEME_DISCOVERY
- SUBSIDY_DISCOVERY
- LOAN_DISCOVERY
- REGISTRATION_DISCOVERY

The workflow:
1. Extracts business attributes from extracted entities
2. Identifies missing required attributes
3. If information is missing, asks for clarification
4. If information is complete, retrieves scheme guidance from knowledge provider
5. Returns grounded results with source citations

Critical restriction: Never fabricate scheme names, funding amounts,
deadlines, benefits, or eligibility requirements. If retrieval is
unavailable, return NEEDS_RETRIEVAL.
"""

import logging
from typing import Any

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


class DiscoveryWorkflow(BaseWorkflow):
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
        conversation_service: ConversationService,
        clarification_service: ClarificationService,
        eligibility_engine: EligibilityEngine,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
    ) -> None:
        super().__init__(
            name="DiscoveryWorkflow",
            service_type="discovery",
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
        """Execute discovery workflow steps.

        Steps:
        1. Extract business attributes from entities
        2. Identify missing required attributes
        3. If missing, request clarification
        4. If complete, retrieve scheme guidance from knowledge provider
        5. Return grounded results with citations
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
                        f"Intent '{intent}' is not supported by DiscoveryWorkflow."
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

        # Step 4: Retrieve scheme guidance from knowledge provider
        discovery_query = self._build_discovery_query(
            message=context.message,
            business_attributes=business_attributes,
            intent=intent,
        )

        if not self.retrieval_provider:
            return [
                WorkflowStepResult(
                    step_id="retrieve_entities",
                    step_name="retrieve_scheme_guidance",
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
            filters=None,
            limit=5,
        )

        if not evidence:
            return [
                WorkflowStepResult(
                    step_id="retrieve_entities",
                    step_name="retrieve_scheme_guidance",
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

        # Step 5: Build grounded response
        return [
            WorkflowStepResult(
                step_id="build_response",
                step_name="build_grounded_response",
                status="completed",
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
            f"To help you find relevant {intent_label.lower()}, I need a "
            f"few more details about your business:\n{missing_list}\n\n"
            "Please provide this information so I can search for "
            "appropriate government schemes and programs."
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
            "However, I cannot search official government sources at "
            "this time. Once document retrieval is available, I'll be "
            "able to search for relevant schemes and programs based on "
            "your business details. Please try again later or consult "
            "official government websites directly."
        )

    def _build_grounded_response(
        self,
        evidence: list[RetrievalSource],
        intent: str,
    ) -> str:
        """Build a grounded response using retrieved evidence."""
        intent_label = intent.replace("_", " ").title()
        lines = [
            f"Based on available government sources, here's information "
            f"related to {intent_label.lower()}:\n",
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
                    f"   Excerpt: {source.relevant_excerpt[:200]}..."
                )
            if source.page_or_section:
                lines.append(
                    f"   Reference: {source.page_or_section}"
                )
            lines.append("")
        lines.append(
            "Please verify scheme details on official government websites "
            "before applying. This information is for guidance only and "
            "does not constitute official approval."
        )
        return "\n".join(lines)
