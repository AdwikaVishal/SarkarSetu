"""Step executor for SarkarSetu AI workflow engine.

Executes individual workflow steps, handling clarification requests,
evidence retrieval, and eligibility evaluation as needed.
"""

import logging
from typing import Any
from uuid import uuid4

from app.services.ai.ai_service import AIService
from app.services.conversation.clarification_service import ClarificationService
from app.services.conversation.conversation_service import ConversationService
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.retrieval import GovernmentKnowledgeProvider

from .context import WorkflowContext
from .workflow_result import WorkflowStepResult

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executes individual workflow steps.

    Provides methods for executing different types of workflow steps:
    - user_input steps: collect information from the user
    - retrieval steps: retrieve evidence from the knowledge provider
    - eligibility steps: evaluate eligibility using the deterministic engine
    - completion steps: finalize the workflow with a response
    """

    def __init__(
        self,
        ai_service: AIService,
        conversation_service: ConversationService,
        clarification_service: ClarificationService,
        eligibility_engine: EligibilityEngine,
        retrieval_provider: GovernmentKnowledgeProvider | None = None,
    ) -> None:
        self.ai_service = ai_service
        self.conversation_service = conversation_service
        self.clarification_service = clarification_service
        self.eligibility_engine = eligibility_engine
        self.retrieval_provider = retrieval_provider

    async def execute_step(
        self,
        step: dict[str, Any],
        context: WorkflowContext,
    ) -> WorkflowStepResult:
        """Execute a single workflow step.

        Args:
            step: Step definition dictionary.
            context: Validated workflow context.

        Returns:
            WorkflowStepResult with the step execution outcome.
        """
        step_type = step.get("type", "unknown")
        step_id = step.get("step_id", str(uuid4()))
        step_name = step.get("name", step_id)

        try:
            if step_type == "clarification":
                return await self._execute_clarification_step(
                    step, context, step_id, step_name
                )
            elif step_type == "retrieval":
                return await self._execute_retrieval_step(
                    step, context, step_id, step_name
                )
            elif step_type == "eligibility":
                return await self._execute_eligibility_step(
                    step, context, step_id, step_name
                )
            elif step_type == "completion":
                return await self._execute_completion_step(
                    step, context, step_id, step_name
                )
            else:
                return WorkflowStepResult(
                    step_id=step_id,
                    step_name=step_name,
                    status="failed",
                    response=f"Unknown step type: {step_type}",
                    warnings=[f"Unknown step type: {step_type}"],
                )
        except Exception as exc:  # noqa: BLE001 - safe error handling
            logger.exception(
                "Step execution failed",
                extra={
                    "workflow_id": str(context.workflow_id),
                    "step_id": step_id,
                    "step_name": step_name,
                    "error": str(exc),
                },
            )
            return WorkflowStepResult(
                step_id=step_id,
                step_name=step_name,
                status="failed",
                response="I'm sorry, I encountered an error processing this step. Please try again.",
                warnings=[str(exc)],
            )

    # ------------------------------------------------------------------
    # Individual step handlers
    # ------------------------------------------------------------------

    async def _execute_clarification_step(
        self,
        step: dict[str, Any],
        context: WorkflowContext,
        step_id: str,
        step_name: str,
    ) -> WorkflowStepResult:
        """Execute a clarification step.

        Prompts the user for missing information. The step should
        specify which information is needed via `missing_fields` or
        `clarification_question`.

        Args:
            step: Step definition dictionary.
            context: Validated workflow context.
            step_id: Unique step ID.
            step_name: Human-readable step name.

        Returns:
            WorkflowStepResult with the clarification outcome.
        """
        missing_fields = step.get("missing_fields", [])
        clarification_question = step.get(
            "clarification_question",
            "Please provide the required information to proceed.",
        )

        # Check if we already have the missing information from entities
        provided_fields = self._extract_provided_fields(
            context.extracted_entities, missing_fields
        )
        remaining_missing = [
            f for f in missing_fields if f not in provided_fields
        ]

        if remaining_missing:
            return WorkflowStepResult(
                step_id=step_id,
                step_name=step_name,
                status="needs_information",
                response=step.get(
                    "response",
                    self._build_clarification_response(
                        remaining_missing, context.primary_intent or ""
                    ),
                ),
                missing_information=remaining_missing,
                clarification_question=clarification_question,
                warnings=[
                    "Please provide the missing information to proceed."
                ],
            )

        # All required information is provided
        return WorkflowStepResult(
            step_id=step_id,
            step_name=step_name,
            status="completed",
            response=step.get(
                "response", "Thank you. I have the information I need."
            ),
            structured_data={
                "provided_fields": provided_fields,
                "step_type": "clarification",
            },
        )

    async def _execute_retrieval_step(
        self,
        step: dict[str, Any],
        context: WorkflowContext,
        step_id: str,
        step_name: str,
    ) -> WorkflowStepResult:
        """Execute a retrieval step.

        Retrieves evidence from the knowledge provider based on
        the step's query and filters.

        Args:
            step: Step definition dictionary.
            context: Validated workflow context.
            step_id: Unique step ID.
            step_name: Human-readable step name.

        Returns:
            WorkflowStepResult with retrieved evidence.
        """
        query = step.get("query", context.message)
        filters = step.get("filters", {})
        limit = step.get("limit", 5)

        if not self.retrieval_provider:
            return WorkflowStepResult(
                step_id=step_id,
                step_name=step_name,
                status="needs_retrieval",
                response=step.get(
                    "response",
                    "I'm unable to retrieve government service information at this time. "
                    "Please try again later or consult official government sources directly.",
                ),
                warnings=[
                    "Knowledge retrieval provider is not available.",
                ],
            )

        evidence = await self.retrieval_provider.retrieve(
            query=query,
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            filters=filters,
            limit=limit,
        )

        if not evidence:
            return WorkflowStepResult(
                step_id=step_id,
                step_name=step_name,
                status="needs_retrieval",
                response=step.get(
                    "response",
                    "I was unable to find relevant government service information "
                    "for your request. Please try again with more specific details, "
                    "or consult official government sources directly.",
                ),
                warnings=[
                    "No relevant government documents found for this query.",
                ],
            )

        return WorkflowStepResult(
            step_id=step_id,
            step_name=step_name,
            status="completed",
            response=step.get(
                "response",
                "I've found relevant government service information for your request.",
            ),
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
            structured_data={
                "retrieved_entities": [
                    {
                        "source_title": s.source_title,
                        "issuing_authority": s.issuing_authority,
                        "relevant_excerpt": s.relevant_excerpt,
                    }
                    for s in evidence
                ],
            },
        )

    async def _execute_eligibility_step(
        self,
        step: dict[str, Any],
        context: WorkflowContext,
        step_id: str,
        step_name: str,
    ) -> WorkflowStepResult:
        """Execute an eligibility evaluation step.

        Runs the deterministic eligibility engine against the
        user's business information.

        Args:
            step: Step definition dictionary.
            context: Validated workflow context.
            step_id: Unique step ID.
            step_name: Human-readable step name.

        Returns:
            WorkflowStepResult with the eligibility assessment result.
        """
        scheme_name = step.get("scheme_name")
        registration_type = step.get("registration_type")

        # Build business attributes from context
        business_attributes = self._extract_business_attributes(
            context.extracted_entities
        )

        # Check for missing required attributes
        missing_attributes = step.get("missing_attributes", [])
        provided_attributes = {
            k: v
            for k, v in business_attributes.items()
            if k in missing_attributes and v
        }
        still_missing = [
            f for f in missing_attributes if f not in provided_attributes
        ]

        if still_missing:
            return WorkflowStepResult(
                step_id=step_id,
                step_name=step_name,
                status="needs_information",
                response=step.get(
                    "response",
                    f"I need the following information to assess your eligibility: "
                    f"{', '.join(still_missing)}.",
                ),
                missing_information=still_missing,
                clarification_question=step.get(
                    "clarification_question",
                    "Please provide the missing business information to proceed.",
                ),
            )

        # Run the eligibility engine
        from app.services.eligibility import EligibilityAssessmentRequest

        request = EligibilityAssessmentRequest(
            user_id=context.user_id,
            business_profile_id=context.business_profile_id,
            scheme_name=scheme_name,
            registration_type=registration_type,
            business_attributes=business_attributes,
            missing_information=still_missing,
            context={
                "conversation_id": str(context.conversation_id),
                "user_message": context.message,
                "primary_intent": context.primary_intent,
            },
        )

        result = await self.eligibility_engine.evaluate(request)

        # Map engine status to step status
        status = result.assessment_status
        if status == "eligible":
            step_status = "completed"
        elif status == "ineligible":
            step_status = "completed"
        elif status == "potentially_eligible":
            step_status = "completed"
        elif status == "needs_information":
            step_status = "needs_information"
        elif status == "unverified":
            step_status = "needs_verification"
        else:
            step_status = "failed"

        return WorkflowStepResult(
            step_id=step_id,
            step_name=step_name,
            status=step_status,
            response=step.get(
                "response",
                f"Eligibility assessment completed for {scheme_name or 'the requested scheme'}.",
            ),
            structured_data={
                "assessment_id": result.assessment_id,
                "scheme_name": result.scheme_name,
                "registration_type": result.registration_type,
                "assessment_status": result.assessment_status,
                "rule_set_version": result.rule_set_version,
                "result_data": result.result_data,
            },
            missing_information=result.missing_information,
            clarification_question=None,
            warnings=list(result.warnings),
            evidence_references=result.evidence_references,
        )

    async def _execute_completion_step(
        self,
        step: dict[str, Any],
        context: WorkflowContext,
        step_id: str,
        step_name: str,
    ) -> WorkflowStepResult:
        """Execute a completion step.

        Finalizes the workflow with a response message.

        Args:
            step: Step definition dictionary.
            context: Validated workflow context.
            step_id: Unique step ID.
            step_name: Human-readable step name.

        Returns:
            WorkflowStepResult with the completion result.
        """
        return WorkflowStepResult(
            step_id=step_id,
            step_name=step_name,
            status="completed",
            response=step.get(
                "response",
                "Thank you for using SarkarSetu AI. Your request has been processed.",
            ),
            structured_data={
                "step_type": "completion",
                "service_type": context.service_type,
            },
        )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _extract_provided_fields(
        self,
        entities: list[dict[str, Any]],
        required_fields: list[str],
    ) -> dict[str, Any]:
        """Extract provided field values from extracted entities.

        Args:
            entities: List of extracted entity dictionaries.
            required_fields: List of required field names.

        Returns:
            Dictionary mapping field names to provided values.
        """
        provided: dict[str, Any] = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "")
            value = entity.get("value", "")
            if value and entity_type in required_fields:
                provided[entity_type] = value
        return provided

    def _build_clarification_response(
        self,
        missing_fields: list[str],
        intent: str,
    ) -> str:
        """Build a clarification response message.

        Args:
            missing_fields: List of missing field names.
            intent: Primary intent string.

        Returns:
            User-facing clarification response string.
        """
        intent_label = intent.replace("_", " ").title()
        missing_list = "\n".join(
            f"- {f.replace('_', ' ')}" for f in missing_fields
        )
        return (
            f"To help you with {intent_label.lower()}, I need a few "
            f"more details about your business:\n{missing_list}\n\n"
            "Please provide this information so I can proceed."
        )

    def _extract_business_attributes(
        self,
        entities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Extract business attributes from extracted entities.

        Args:
            entities: List of extracted entity dictionaries.

        Returns:
            Dictionary mapping attribute names to values.
        """
        attributes: dict[str, Any] = {}
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
        for entity in entities:
            entity_type = entity.get("entity_type", "")
            value = entity.get("value", "")
            if not value:
                continue
            if entity_type in mapping:
                attributes[mapping[entity_type]] = value
        return attributes
