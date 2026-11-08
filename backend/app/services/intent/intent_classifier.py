"""Intent classification service.

Classifies user messages into intent categories using the Gemini AI service.
Maintains a taxonomy of supported intents and applies confidence thresholds.
"""

from pydantic import BaseModel

from app.schemas.entities import ExtractedEntity
from app.schemas.intent import IntentDetectionResult
from app.services.ai.ai_service import AIService
from app.services.intent.context_builder import (
    build_conversation_context,
)
from app.services.intent.entity_extractor import EntityExtractor
from app.services.intent.intent_taxonomy import (
    ALL_INTENT_VALUES,
    Intent,
    LanguageCode,
    RiskFlag,
    UrgencyLevel,
    get_confidence_level,
)


class IntentClassifier:
    """Classifies user messages into intent categories using AI.

    Uses the Gemini AI service through structured output generation
    to classify user messages into intent categories with confidence scores.
    Also extracts entities from messages using a dedicated entity extractor.
    """

    def __init__(self, ai_service: AIService) -> None:
        self.ai_service = ai_service
        self.entity_extractor = EntityExtractor(ai_service)
        self._intent_schema = self._build_intent_schema()

    def _build_intent_schema(self) -> dict:
        """Build JSON schema for intent detection response.

        Returns:
            JSON schema dict for intent detection.
        """
        intent_values = ", ".join(sorted(ALL_INTENT_VALUES))
        return {
            "type": "object",
            "properties": {
                "primary_intent": {
                    "type": "string",
                    "enum": intent_values,
                },
                "secondary_intents": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": intent_values,
                    },
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "requires_clarification": {
                    "type": "boolean",
                },
                "clarification_question": {
                    "type": "string",
                },
                "reasoning_summary": {
                    "type": "string",
                },
                "detected_language": {
                    "type": "string",
                    "enum": ["en", "hi", "kn", "en-hi", "mixed", "unknown"],
                },
                "is_follow_up": {
                    "type": "boolean",
                },
                "referenced_entity": {
                    "type": "string",
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                },
                "risk_flags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "primary_intent",
                "confidence",
                "requires_clarification",
                "reasoning_summary",
                "detected_language",
                "is_follow_up",
                "urgency",
                "risk_flags",
            ],
        }

    async def classify_intent(
        self,
        message: str,
        *,
        user_id: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        business_context: str | None = None,
    ) -> IntentDetectionResult:
        """Classify user message intent using AI.

        Args:
            message: User message text.
            user_id: Optional user ID for context.
            conversation_history: Optional conversation history.
            business_context: Optional business context string.

        Returns:
            IntentDetectionResult with classification results.

        Raises:
            AIServiceUnavailableError: If AI service is not configured.
        """
        # Build context strings
        conversation_context = build_conversation_context(
            conversation_history or []
        )
        business_context_str = business_context or ""

        # Build the classification prompt
        prompt = self._build_classification_prompt(
            message=message,
            conversation_context=conversation_context,
            business_context=business_context_str,
        )

        # Generate structured output using AI service
        result = await self.ai_service.generate_structured_output(
            prompt=prompt,
            response_model=_IntentDetectionResult,
            temperature=0.3,
            max_output_tokens=1024,
            system_instruction=self._get_system_instruction(),
        )

        # Convert internal result to public schema with confidence level
        confidence_level = get_confidence_level(result.confidence)
        return IntentDetectionResult(
            primary_intent=Intent(result.primary_intent),
            secondary_intents=[Intent(s) for s in result.secondary_intents],
            confidence=result.confidence,
            confidence_level=confidence_level,
            requires_clarification=result.requires_clarification,
            clarification_question=result.clarification_question,
            reasoning_summary=result.reasoning_summary,
            detected_language=LanguageCode(result.detected_language),
            is_follow_up=result.is_follow_up,
            referenced_entity=result.referenced_entity,
            urgency=UrgencyLevel(result.urgency),
            risk_flags=[RiskFlag(r) for r in result.risk_flags],
            taxonomy_version="1.0.0",
        )

    async def extract_entities(
        self,
        message: str,
        *,
        business_context: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> list[ExtractedEntity]:
        """Extract entities from user message using AI.

        Delegates to the EntityExtractor service.

        Args:
            message: User message text.
            business_context: Optional business context string.
            conversation_history: Optional conversation history.

        Returns:
            List of typed ExtractedEntity objects.

        Raises:
            AIServiceUnavailableError: If AI service is not configured.
        """
        return await self.entity_extractor.extract_entities(
            message=message,
            business_context=business_context,
            conversation_history=conversation_history,
        )

    async def classify_and_extract(
        self,
        message: str,
        *,
        user_id: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        business_context: str | None = None,
    ) -> tuple[IntentDetectionResult, list[ExtractedEntity]]:
        """Classify intent and extract entities in a single pass.

        Args:
            message: User message text.
            user_id: Optional user ID for context.
            conversation_history: Optional conversation history.
            business_context: Optional business context string.

        Returns:
            Tuple of (IntentDetectionResult, list of ExtractedEntity).

        Raises:
            AIServiceUnavailableError: If AI service is not configured.
        """
        # Build context strings
        conversation_context = build_conversation_context(
            conversation_history or []
        )
        business_context_str = business_context or ""

        # Build the classification prompt
        prompt = self._build_classification_prompt(
            message=message,
            conversation_context=conversation_context,
            business_context=business_context_str,
        )

        # Generate structured output using AI service
        result = await self.ai_service.generate_structured_output(
            prompt=prompt,
            response_model=_IntentDetectionResult,
            temperature=0.3,
            max_output_tokens=1024,
            system_instruction=self._get_system_instruction(),
        )

        # Convert internal result to public schema with confidence level
        confidence_level = get_confidence_level(result.confidence)
        intent_result = IntentDetectionResult(
            primary_intent=Intent(result.primary_intent),
            secondary_intents=[Intent(s) for s in result.secondary_intents],
            confidence=result.confidence,
            confidence_level=confidence_level,
            requires_clarification=result.requires_clarification,
            clarification_question=result.clarification_question,
            reasoning_summary=result.reasoning_summary,
            detected_language=LanguageCode(result.detected_language),
            is_follow_up=result.is_follow_up,
            referenced_entity=result.referenced_entity,
            urgency=UrgencyLevel(result.urgency),
            risk_flags=[RiskFlag(r) for r in result.risk_flags],
            taxonomy_version="1.0.0",
        )

        # Extract entities using the entity extractor
        entities = await self.entity_extractor.extract_entities(
            message=message,
            business_context=business_context_str,
            conversation_history=conversation_history,
        )

        return intent_result, entities

    def _build_classification_prompt(
        self,
        message: str,
        conversation_context: str,
        business_context: str,
    ) -> str:
        """Build the classification prompt for the AI model.

        Args:
            message: User message text.
            conversation_context: Conversation history context.
            business_context: Business context string.

        Returns:
            Formatted prompt string.
        """
        intent_list = "\n".join(
            f"- {intent.value}: {intent.name.replace('_', ' ')}"
            for intent in Intent
        )

        return (
            f"Classify the following user message into one of these intent "
            f"categories:\n{intent_list}\n\n"
            f"User message: {message}\n"
            f"{conversation_context}\n"
            f"{business_context}\n\n"
            "Respond with ONLY a JSON object containing:\n"
            '  "primary_intent": one of the intent categories above,\n'
            '  "secondary_intents": array of up to 2 secondary intents,\n'
            '  "confidence": number between 0.0 and 1.0,\n'
            '  "requires_clarification": true/false,\n'
            '  "clarification_question": string or null,\n'
            '  "reasoning_summary": brief explanation,\n'
            '  "detected_language": one of "en", "hi", "kn", "en-hi", '
            '"mixed", "unknown",\n'
            '  "is_follow_up": true/false,\n'
            '  "referenced_entity": string or null,\n'
            '  "urgency": one of "low", "normal", "high",\n'
            '  "risk_flags": array of relevant risk flags\n'
        )

    def _get_system_instruction(self) -> str:
        """Get system instruction for intent classification.

        Returns:
            System instruction string.
        """
        return (
            "You are an intent classification engine for SarkarSetu AI, "
            "a platform that helps Indian entrepreneurs navigate "
            "government services. "
            "Classify the user's message into exactly one primary intent "
            "category from the provided list. Optionally classify up to "
            "2 secondary intents if relevant. Assign a confidence score "
            "between 0.0 and 1.0 based on how confidently the message "
            "matches the intent. Determine the language of the message "
            "(en, hi, kn, en-hi, mixed, or unknown). Identify the urgency "
            "level (low, normal, high). Do not invent government rules, "
            "schemes, or official approvals. Do not ask follow-up "
            "questions. Respond only with valid JSON."
        )


class _IntentDetectionResult(BaseModel):
    """Internal Pydantic model for intent detection validation.

    This is an internal model used to parse the AI model's JSON output.
    It is converted to the public IntentDetectionResult schema after
    validation.
    """

    primary_intent: str
    secondary_intents: list[str] = []
    confidence: float
    confidence_level: str = "low"
    requires_clarification: bool = False
    clarification_question: str | None = None
    reasoning_summary: str
    detected_language: str
    is_follow_up: bool = False
    referenced_entity: str | None = None
    urgency: str = "normal"
    risk_flags: list[str] = []
