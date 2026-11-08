"""Response builder for orchestrator.

Builds assistant responses based on intent classification results,
conversation context, and clarification state. Keeps response type
routing and prompt construction centralized.
"""

import logging

from app.schemas.intent import IntentDetectionResult
from app.schemas.orchestrator import ResponseType

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """Builds assistant responses for different intents and states.

    Does not call AI services directly; it constructs prompt context
    and determines the response type. AI generation is delegated to
    the orchestrator service.
    """

    # Intents that indicate the platform cannot yet fulfill the request
    WORKFLOW_NOT_AVAILABLE_INTENTS = {
        "create_roadmap",
        "view_roadmap",
        "task_progress",
        "compliance_guidance",
        "tax_guidance",
        "deadline_query",
        "application_status",
        "application_guidance",
        "document_validation",
    }

    # Intents that require clarification before proceeding
    CLARIFICATION_REQUIRED_INTENTS = {
        "scheme_eligibility",
        "udyam_eligibility",
        "gst_applicability",
        "scheme_discovery",
        "subsidy_discovery",
        "loan_discovery",
    }

    def build_response_type(
        self,
        intent_result: IntentDetectionResult | None,
        clarification_pending: bool,
        clarification_question: str | None,
        has_sufficient_context: bool = False,
    ) -> ResponseType:
        """Determine the response type from pipeline state.

        Args:
            intent_result: Intent classification result, if available.
            clarification_pending: Whether a clarification is pending.
            clarification_question: The pending clarification question.
            has_sufficient_context: Whether enough info is available to proceed.

        Returns:
            The appropriate ResponseType enum value.
        """
        if clarification_pending and clarification_question:
            return ResponseType.CLARIFICATION

        if intent_result is None:
            return ResponseType.ERROR

        if not intent_result.requires_clarification and not has_sufficient_context:
            if intent_result.primary_intent.value in self.CLARIFICATION_REQUIRED_INTENTS:
                return ResponseType.CLARIFICATION

        if intent_result.primary_intent.value == "greeting":
            return ResponseType.GREETING

        if intent_result.primary_intent.value == "general_question":
            return ResponseType.GENERAL_GUIDANCE

        if intent_result.primary_intent.value in self.WORKFLOW_NOT_AVAILABLE_INTENTS:
            return ResponseType.WORKFLOW_NOT_AVAILABLE

        if intent_result.primary_intent.value == "out_of_scope":
            return ResponseType.OUT_OF_SCOPE

        if intent_result.primary_intent.value == "unknown":
            return ResponseType.INTENT_UNCERTAIN

        if intent_result.requires_clarification:
            return ResponseType.CLARIFICATION

        if intent_result.confidence < 0.65:
            return ResponseType.INTENT_UNCERTAIN

        return ResponseType.GENERAL_GUIDANCE

    def build_clarification_prompt(
        self,
        message: str,
        clarification_question: str,
        original_intent: str | None,
        conversation_context: str,
    ) -> str:
        """Build a prompt for handling a clarification answer.

        Args:
            message: User's answer to the clarification question.
            clarification_question: The original clarification question.
            original_intent: The intent that triggered the clarification.
            conversation_context: Recent conversation history.

        Returns:
            A prompt string for generating a clarification-aware response.
        """
        return (
            f"The user previously asked for help with: {original_intent or 'a government service'}\n"
            f"You asked them: {clarification_question}\n"
            f"They responded: {message}\n\n"
            f"Conversation context:\n{conversation_context}\n\n"
            "Incorporate the user's answer into the original request context "
            "and provide a helpful next step. Do not claim government approval "
            "or completed registration. Ask only for information still needed."
        )

    def build_general_prompt(
        self,
        message: str,
        intent_result: IntentDetectionResult,
        conversation_context: str,
        business_context: str | None,
        warnings: list[str],
    ) -> str:
        """Build a prompt for general assistant response generation.

        Args:
            message: User message text.
            intent_result: Intent classification result.
            conversation_context: Recent conversation history.
            business_context: Optional business profile context.
            warnings: Non-fatal warnings to surface.

        Returns:
            A prompt string for the AI service.
        """
        warning_text = ""
        if warnings:
            warning_text = "\nWarnings collected during processing:\n" + "\n".join(
                f"- {w}" for w in warnings
            )

        return (
            f"User message: {message}\n"
            f"Detected intent: {intent_result.primary_intent.value}\n"
            f"Confidence: {intent_result.confidence:.2f} ({intent_result.confidence_level})\n"
            f"Reasoning: {intent_result.reasoning_summary}\n"
            f"Conversation context:\n{conversation_context}\n"
            f"Business context: {business_context or 'None provided'}{warning_text}\n\n"
            "Generate a helpful, accurate response for an Indian entrepreneur "
            "navigating government services. Do not invent government rules, "
            "schemes, deadlines, fees, or official approvals. Clearly distinguish "
            "verified information from general guidance. Ask targeted follow-up "
            "questions only when information is genuinely missing. Do not claim "
            "that registration is complete or that the user is approved for any "
            "scheme."
        )

    def build_out_of_scope_prompt(self, message: str) -> str:
        """Build a prompt for out-of-scope responses."""
        return (
            f"User message: {message}\n\n"
            "The user is asking about something outside the supported scope "
            "of SarkarSetu AI. Politely explain what the platform can help "
            "with (government scheme discovery, registration guidance, "
            "document requirements, general entrepreneurship questions) and "
            "what it cannot do. Do not invent capabilities."
        )

    def build_greeting_response(self) -> str:
        """Return a standard greeting response."""
        return (
            "Hello! I'm SarkarSetu AI, your guide to Indian government "
            "services for entrepreneurs. I can help you with:\n"
            "• Discovering government schemes and subsidies\n"
            "• Understanding registration requirements (Udyam, GST, business)\n"
            "• Finding document guidance\n"
            "• Answering general entrepreneurship questions\n\n"
            "How can I help you today?"
        )

    def build_workflow_not_available_response(self, intent: str) -> str:
        """Return a response for workflows not yet available."""
        return (
            f"The '{intent.replace('_', ' ')}' workflow is not yet available "
            "in SarkarSetu AI. I can help you with scheme discovery, "
            "registration guidance, document requirements, and general "
            "entrepreneurship questions instead. What would you like to explore?"
        )

    def build_out_of_scope_response(self) -> str:
        """Return a standard out-of-scope response."""
        return (
            "I'm sorry, but that request is outside the scope of SarkarSetu AI. "
            "I specialize in helping Indian entrepreneurs navigate government "
            "services — scheme discovery, registration guidance, document "
            "requirements, and general entrepreneurship questions. "
            "How can I help you with one of those topics?"
        )

    def build_uncertain_intent_response(self, message: str) -> str:
        """Return a response when intent is uncertain."""
        return (
            "I'm not entirely sure what you're looking for. Could you please "
            "rephrase your question or tell me more about what you need help "
            "with? For example, you can ask about:\n"
            "• Government schemes for your business\n"
            "• Registration requirements (Udyam, GST)\n"
            "• Documents needed for a service\n"
            "• General entrepreneurship guidance"
        )
