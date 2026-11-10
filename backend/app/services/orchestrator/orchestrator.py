"""SarkarSetu AI orchestrator with agent integration.

Coordinates all existing backend services into a single end-to-end
conversational workflow:

1. Validate request
2. Create or retrieve conversation
3. Persist user message
4. Retrieve conversation context
5. Handle pending clarification
6. Intent classification and entity extraction
7. Agent dispatch (specialized agents for supported intents)
8. Route to response strategy
9. Generate assistant response
10. Persist assistant message
11. Return typed response
"""

import logging
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.schemas.agents import AgentContext, AgentStatus
from app.schemas.intent import IntentDetectionResult
from app.schemas.intent_enums import Intent, LanguageCode, UrgencyLevel
from app.schemas.orchestrator import (
    AssistantResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationStatusResponse,
    ExtractedEntitySummary,
    IntentSummary,
    ResponseType,
)
from app.services.agents.agent_registry import AgentRegistry
from app.services.ai.ai_service import AIService
from app.services.ai.exceptions import (
    AIError,
    AIResponseValidationError,
    AIServiceUnavailableError,
)
from app.services.ai.local_knowledge import get_knowledge_base
from app.services.ai.providers import (
    LocalFallbackProvider,
    ProviderResult,
    ProviderStatus,
)
from app.services.conversation.clarification_service import ClarificationService
from app.services.conversation.context_manager import (
    ConversationContextManager,
)
from app.services.conversation.conversation_service import ConversationService
from app.services.intent.intent_classifier import IntentClassifier
from app.services.intent.intent_taxonomy import ConfidenceLevel
from app.services.ownership import OwnershipService, ResourceNotFoundError

from .pipeline import PipelineContext, StageTimer
from .response_builder import ResponseBuilder

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 5000
CONTEXT_MAX_MESSAGES = 10


class SarkarSetuOrchestrator:
    """Central orchestrator for SarkarSetu AI conversational workflow.

    Coordinates existing services rather than duplicating their logic.
    Each pipeline stage delegates to the appropriate specialized service.
    Specialized agents are dispatched via AgentRegistry for supported intents.
    """

    def __init__(
        self,
        ai_service: AIService,
        intent_classifier: IntentClassifier,
        conversation_service: ConversationService,
        clarification_service: ClarificationService,
        context_manager: ConversationContextManager,
        ownership_service: OwnershipService,
        agent_registry: AgentRegistry | None = None,
    ) -> None:
        self.ai_service = ai_service
        self.intent_classifier = intent_classifier
        self.conversation_service = conversation_service
        self.clarification_service = clarification_service
        self.context_manager = context_manager
        self.ownership_service = ownership_service
        self.agent_registry = agent_registry or AgentRegistry(
            ai_service=ai_service
        )
        self.response_builder = ResponseBuilder()

    async def process_message(
        self, request: ChatMessageRequest, user_id: UUID
    ) -> ChatMessageResponse:
        """Process an incoming user message through the full pipeline.

        Args:
            request: Chat message request from the API layer.
            user_id: Authenticated user ID (never from client input).

        Returns:
            Typed orchestration response.
        """
        start_time = time.perf_counter()

        ctx = PipelineContext(
            user_id=user_id,
            conversation_id=request.conversation_id,
            business_profile_id=request.business_profile_id,
            message=request.message,
            idempotency_key=request.idempotency_key,
        )

        try:
            await self._run_pipeline(ctx)
        except Exception as exc:  # noqa: BLE001 - pipeline catches internally
            ctx.errors.append(f"pipeline: {exc}")
            logger.exception(
                "Pipeline exception",
                extra={"request_id": ctx.request_id, "error": str(exc)},
            )

        return self._build_response(ctx, start_time)

    async def _run_pipeline(self, ctx: PipelineContext) -> None:
        """Execute all pipeline stages in sequence."""
        stages = [
            self._validate_request,
            self._load_conversation,
            self._persist_user_message,
            self._retrieve_context,
            self._handle_clarification,
            self._classify_and_extract,
            self._dispatch_agent,
            self._route_response,
            self._generate_response,
            self._persist_assistant_message,
        ]

        for stage in stages:
            async with StageTimer(stage.__name__, ctx):
                await stage(ctx)

    # ------------------------------------------------------------------
    # Stage 1 — Validate request
    # ------------------------------------------------------------------
    async def _validate_request(self, ctx: PipelineContext) -> None:
        if not ctx.message or not ctx.message.strip():
            ctx.errors.append("Message is empty or whitespace-only")
            return

        if len(ctx.message) > MAX_MESSAGE_LENGTH:
            ctx.errors.append(
                f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"
            )
            return

        if not ctx.user_id:
            ctx.errors.append("Authenticated user ID is required")
            return

    # ------------------------------------------------------------------
    # Stage 2 — Create or retrieve conversation
    # ------------------------------------------------------------------
    async def _load_conversation(self, ctx: PipelineContext) -> None:
        if ctx.has_fatal_error:
            return
        if ctx.conversation_id:
            await self._retrieve_existing(ctx)
        else:
            await self._create_new(ctx)

    async def _retrieve_existing(self, ctx: PipelineContext) -> None:
        if ctx.conversation_id is None:
            ctx.errors.append("Conversation ID is required")
            return

        conversation = await self.conversation_service.get_conversation(
            conversation_id=ctx.conversation_id,
            user_id=ctx.user_id,
        )
        if conversation is None:
            ctx.errors.append("Conversation not found or not owned by user")
            return

        if conversation.is_deleted or conversation.status == "archived":
            ctx.errors.append("Conversation is archived")
            return

        if conversation.business_profile_id is not None:
            try:
                await self.ownership_service.get_user_business_profile(
                    user_id=ctx.user_id,
                    business_profile_id=conversation.business_profile_id,
                )
            except ResourceNotFoundError:
                ctx.errors.append("Conversation business profile not owned by user")
                return

        ctx.conversation = conversation
        ctx.business_profile_id = conversation.business_profile_id

    async def _create_new(self, ctx: PipelineContext) -> None:
        if ctx.business_profile_id:
            try:
                await self.ownership_service.get_user_business_profile(
                    user_id=ctx.user_id,
                    business_profile_id=ctx.business_profile_id,
                )
            except ResourceNotFoundError:
                ctx.errors.append("Business profile not found or not owned by user")
                return

        conversation = await self.conversation_service.create_conversation(
            user_id=ctx.user_id,
            business_profile_id=ctx.business_profile_id,
            title=ctx.message[:80],
        )
        ctx.conversation = conversation
        ctx.conversation_id = conversation.id

    # ------------------------------------------------------------------
    # Stage 3 — Persist user message
    # ------------------------------------------------------------------
    async def _persist_user_message(self, ctx: PipelineContext) -> None:
        if ctx.has_fatal_error:
            return
        if ctx.conversation is None:
            return

        message = await self.conversation_service.persist_user_message(
            conversation_id=ctx.conversation.id,
            user_id=ctx.user_id,
            content=ctx.message,
            intent=None,
            message_metadata=None,
        )
        if message is None:
            ctx.errors.append("Failed to persist user message")
            return

        ctx.user_message = message

    # ------------------------------------------------------------------
    # Stage 4 — Retrieve conversation context
    # ------------------------------------------------------------------
    async def _retrieve_context(self, ctx: PipelineContext) -> None:
        if ctx.has_fatal_error:
            return
        if ctx.conversation is None:
            return

        context = await self.context_manager.get_conversation_context(
            conversation_id=ctx.conversation.id,
            user_id=ctx.user_id,
            max_messages=CONTEXT_MAX_MESSAGES,
        )
        ctx.context_dict = context if context else {}

    # ------------------------------------------------------------------
    # Stage 5 — Handle pending clarification
    # ------------------------------------------------------------------
    async def _handle_clarification(self, ctx: PipelineContext) -> None:
        if ctx.has_fatal_error:
            return
        if ctx.conversation is None:
            return

        state = await self.clarification_service.get_clarification_state(
            conversation_id=ctx.conversation.id
        )
        ctx.clarification_state = state

        if state is None:
            return

        question = state.get("question", "")
        answer = ctx.message.strip()

        resolved = await self.clarification_service.resolve_clarification(
            conversation_id=ctx.conversation.id,
            answer=answer,
            answer_data={"answered_at": datetime.now(UTC).isoformat()},
        )

        if resolved:
            ctx.warnings.append(
                f"Clarification resolved: user answered '{answer}' to '{question}'"
            )
        else:
            ctx.warnings.append(
                f"Clarification still pending: '{question}'"
            )

    # ------------------------------------------------------------------
    # Stage 6 — Intent classification and entity extraction
    # ------------------------------------------------------------------
    async def _classify_and_extract(self, ctx: PipelineContext) -> None:
        if ctx.has_fatal_error:
            return
        if ctx.conversation is None:
            return

        history = ctx.context_dict.get("messages", [])
        if not isinstance(history, list):
            history = []
        typed_history: list[dict[str, str]] = [
            {"role": str(m.get("role", "user")), "content": str(m.get("content", ""))}
            for m in history
            if isinstance(m, dict)
        ]

        business_context = None
        if ctx.conversation.business_profile_id:
            business_context = (
                f"Business profile ID: {ctx.conversation.business_profile_id}"
            )

        try:
            intent_result, entities = await self.intent_classifier.classify_and_extract(
                message=ctx.message,
                user_id=str(ctx.user_id),
                conversation_history=typed_history,
                business_context=business_context,
            )
            ctx.intent_result = intent_result
            ctx.entities = entities
        except AIServiceUnavailableError as exc:
            ctx.warnings.append(f"AI service unavailable for intent classification: {exc}")
            ctx.intent_result = self._empty_intent()
        except AIError as exc:
            ctx.warnings.append(f"AI error during classification: {exc.message}")
            ctx.intent_result = self._empty_intent()
        except Exception as exc:  # noqa: BLE001
            ctx.warnings.append(f"Classification failed: {exc}")
            ctx.intent_result = self._empty_intent()

    # ------------------------------------------------------------------
    # Stage 7 — Agent dispatch
    # ------------------------------------------------------------------
    async def _dispatch_agent(self, ctx: PipelineContext) -> None:
        """Dispatch to a specialized agent if the intent is supported.

        If no agent supports the intent, the pipeline continues to
        standard routing without agent intervention.
        """
        if ctx.has_fatal_error:
            return
        if ctx.conversation is None:
            return
        if ctx.intent_result is None:
            return

        intent = ctx.intent_result.primary_intent.value
        agent = self.agent_registry.resolve_from_intent(intent)
        if agent is None:
            # No agent for this intent — continue with standard routing
            return

        # Build AgentContext from pipeline context
            # Build conversation history for agent context
            raw_messages = ctx.context_dict.get("messages", [])
            messages_list = (
                raw_messages if isinstance(raw_messages, list) else []
            )
            conversation_history: list[dict[str, str]] = [
                {
                    "role": str(m.get("role", "user")),
                    "content": str(m.get("content", "")),
                }
                for m in messages_list
                if isinstance(m, dict)
            ]

            agent_context: AgentContext = AgentContext(
                user_id=ctx.user_id,
                conversation_id=ctx.conversation.id,
                business_profile_id=ctx.business_profile_id,
                message=ctx.message,
                primary_intent=ctx.intent_result.primary_intent.value,
                secondary_intents=[
                    i.value for i in ctx.intent_result.secondary_intents
                ],
                extracted_entities=[
                    {
                        "entity_type": e.entity_type.value,
                        "value": e.value,
                        "confidence": e.confidence,
                        "source": e.source,
                        "needs_clarification": e.needs_clarification,
                    }
                    for e in ctx.entities
                ],
                conversation_history=conversation_history,
                clarification_state=ctx.clarification_state,
                request_id=ctx.request_id,
            )

        try:
            agent_result = await agent.execute(agent_context)
            ctx.agent_result = agent_result
        except Exception as exc:  # noqa: BLE001 - safe error handling
            ctx.warnings.append(f"Agent dispatch failed: {exc}")
            logger.exception(
                "Agent dispatch failed",
                extra={"request_id": ctx.request_id, "agent": agent.name},
            )

    # ------------------------------------------------------------------
    # Stage 8 — Route to response strategy
    # ------------------------------------------------------------------
    async def _route_response(self, ctx: PipelineContext) -> None:
        if ctx.has_fatal_error:
            ctx.response_type = ResponseType.ERROR
            return

        # If an agent produced a result, use its status to determine response type
        if ctx.agent_result is not None:
            agent_status = ctx.agent_result.status
            if agent_status == AgentStatus.COMPLETED:
                ctx.response_type = ResponseType.GENERAL_GUIDANCE
            elif agent_status == AgentStatus.NEEDS_INFORMATION:
                ctx.response_type = ResponseType.CLARIFICATION
            elif agent_status == AgentStatus.NEEDS_RETRIEVAL:
                ctx.response_type = ResponseType.CLARIFICATION
            elif agent_status == AgentStatus.NEEDS_VERIFICATION:
                ctx.response_type = ResponseType.CLARIFICATION
            elif agent_status == AgentStatus.NOT_SUPPORTED:
                ctx.response_type = ResponseType.WORKFLOW_NOT_AVAILABLE
            elif agent_status == AgentStatus.FAILED:
                ctx.response_type = ResponseType.ERROR
            else:
                ctx.response_type = ResponseType.GENERAL_GUIDANCE
            return

        clarification_pending = ctx.clarification_state is not None
        clarification_question: str | None = None
        if clarification_pending and ctx.clarification_state:
            q = ctx.clarification_state.get("question")
            if isinstance(q, str):
                clarification_question = q

        has_context = bool(ctx.context_dict.get("messages"))

        ctx.response_type = self.response_builder.build_response_type(
            intent_result=ctx.intent_result,
            clarification_pending=clarification_pending,
            clarification_question=clarification_question,
            has_sufficient_context=has_context,
        )

    # ------------------------------------------------------------------
    # Stage 9 — Generate assistant response
    # ------------------------------------------------------------------
    async def _generate_response(self, ctx: PipelineContext) -> None:
        if ctx.has_fatal_error:
            ctx.assistant_response_text = (
                "I'm sorry, I couldn't process your request at this time. "
                "Please try again later."
            )
            ctx.response_type = ResponseType.ERROR
            return

        # If an agent produced a response, use it directly
        if ctx.agent_result is not None:
            ctx.assistant_response_text = ctx.agent_result.response
            ctx.warnings.extend(ctx.agent_result.warnings)
            return

        if ctx.response_type == ResponseType.GREETING:
            ctx.assistant_response_text = (
                self.response_builder.build_greeting_response()
            )
            return

        if ctx.response_type == ResponseType.WORKFLOW_NOT_AVAILABLE:
            intent_name = (
                ctx.intent_result.primary_intent.value
                if ctx.intent_result
                else "unknown"
            )
            ctx.assistant_response_text = (
                self.response_builder.build_workflow_not_available_response(intent_name)
            )
            return

        if ctx.response_type == ResponseType.OUT_OF_SCOPE:
            ctx.assistant_response_text = (
                self.response_builder.build_out_of_scope_response()
            )
            return

        if ctx.response_type == ResponseType.INTENT_UNCERTAIN:
            # Before declaring intent uncertain, attempt local knowledge
            # retrieval so that valid government-scheme questions still
            # get answered even when intent classification fails.
            local_result = await self._try_local_knowledge_retrieval(ctx)
            if local_result is not None:
                ctx.assistant_response_text = local_result.text
                ctx.provider = local_result.provider
                ctx.fallback_used = local_result.fallback_used
                ctx.confidence = local_result.confidence
                if local_result.sources:
                    ctx.retrieval_sources = local_result.sources
                ctx.response_type = ResponseType.GENERAL_GUIDANCE
                return

            ctx.assistant_response_text = (
                self.response_builder.build_uncertain_intent_response(ctx.message)
            )
            return

        if ctx.response_type == ResponseType.CLARIFICATION:
            question = (
                ctx.clarification_state.get("question", "")
                if ctx.clarification_state
                else ""
            )
            if not question and ctx.agent_result:
                question = ctx.agent_result.clarification_question or ""
            original_intent = (
                ctx.intent_result.primary_intent.value
                if ctx.intent_result
                else None
            )
            conversation_context = self._format_context(ctx)
            ctx.assistant_response_text = (
                f"I need a bit more information to help you with "
                f"{original_intent or 'your request'}.\n{question}\n\n"
                f"Previous context:\n{conversation_context}"
            )
            return

        # Default: general guidance via AI with fallback
        await self._generate_ai_response(ctx)

    async def _generate_ai_response(self, ctx: PipelineContext) -> None:
        """Generate an AI-powered assistant response using multi-provider router.

        Attempts Gemini first, falls back to local knowledge-based provider
        if Gemini is unavailable or fails. Records which provider was used.
        """
        conversation_context = self._format_context(ctx)
        business_context = None
        if ctx.conversation and ctx.conversation.business_profile_id:
            business_context = (
                f"Business profile ID: {ctx.conversation.business_profile_id}"
            )

        prompt = self.response_builder.build_general_prompt(
            message=ctx.message,
            intent_result=ctx.intent_result or self._empty_intent(),
            conversation_context=conversation_context,
            business_context=business_context,
            warnings=ctx.warnings,
        )

        system_instruction = self._system_instruction()

        try:
            result = await self.ai_service.generate_response(
                message=ctx.message,
                conversation_history=(
                    ctx.context_dict.get("messages", [])
                    if isinstance(ctx.context_dict.get("messages"), list)
                    else None
                ),
                business_context=business_context,
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=1024,
            )

            # result is a ProviderResult from the multi-provider router
            ctx.assistant_response_text = result.text
            ctx.ai_model = result.provider
            ctx.provider = result.provider
            ctx.fallback_used = result.fallback_used
            ctx.confidence = result.confidence

            if result.sources:
                ctx.retrieval_sources = result.sources

            if result.warnings:
                ctx.warnings.extend(result.warnings)

            if result.status == ProviderStatus.ERROR:
                ctx.response_type = ResponseType.ERROR
                ctx.warnings.append(
                    "Both AI service and local knowledge base are unavailable. "
                    "Please try again later."
                )

        except AIServiceUnavailableError as exc:
            ctx.assistant_response_text = (
                "I'm sorry, the AI service is not configured. "
                "Please contact support to enable AI assistance."
            )
            ctx.response_type = ResponseType.ERROR
            ctx.warnings.append(str(exc))
        except Exception as exc:  # noqa: BLE001
            ctx.assistant_response_text = (
                "I'm sorry, I encountered an error generating a response. "
                "Please try again later."
            )
            ctx.response_type = ResponseType.ERROR
            ctx.warnings.append(str(exc))

    async def _try_local_knowledge_retrieval(self, ctx: PipelineContext) -> ProviderResult | None:
        try:
            kb = get_knowledge_base()
            result = await kb.retrieve(ctx.message)
            matched_schemes = result.get("matched_schemes", [])
            if not matched_schemes:
                return None
            confidence = result.get("confidence", 0.0)
            match_type = result.get("match_type", "keyword")
            lines = []
            if match_type == "exact":
                lines.append(f"## {matched_schemes[0].get('name', 'Scheme Information')}")
            else:
                lines.append("## Relevant Government Schemes")
            lines.append("")
            lines.append(
                "*Using SarkarSetu's offline knowledge base. Some information may not reflect the latest government updates.*"
            )
            lines.append("")
            for scheme in matched_schemes[:3]:
                lines.append(f"### {scheme.get('name', 'Unknown Scheme')}")
                lines.append("")
                if scheme.get("description"):
                    lines.append(f"**Description:** {scheme['description']}")
                    lines.append("")
                if scheme.get("eligibility"):
                    lines.append(f"**Eligibility:** {scheme['eligibility']}")
                    lines.append("")
                if scheme.get("benefits"):
                    lines.append(f"**Benefits:** {scheme['benefits']}")
                    lines.append("")
                if scheme.get("required_documents"):
                    docs = scheme["required_documents"]
                    if isinstance(docs, list):
                        lines.append("**Required Documents:**")
                        for doc in docs:
                            lines.append(f"  - {doc}")
                    else:
                        lines.append(f"**Required Documents:** {docs}")
                    lines.append("")
                if scheme.get("application_procedure"):
                    lines.append(f"**Application Procedure:** {scheme['application_procedure']}")
                    lines.append("")
                if scheme.get("official_url"):
                    lines.append(f"**Official URL:** {scheme['official_url']}")
                    lines.append("")
                if scheme.get("official_source"):
                    lines.append(f"**Source:** {scheme['official_source']}")
                    lines.append("")
                lines.append("---")
                lines.append("")
            lines.append(
                "This information is for general guidance only and does not constitute official eligibility confirmation or government approval. Please verify details on the official government website before applying."
            )
            text = "\n".join(lines)
            sources = [
                {
                    "source_title": s.get("name"),
                    "issuing_authority": s.get("issuing_authority"),
                    "source_url": s.get("official_url"),
                    "relevant_excerpt": s.get("description"),
                    "retrieval_score": s.get("confidence"),
                }
                for s in matched_schemes
            ]
            return ProviderResult(
                text=text,
                provider="local_fallback",
                status="success",
                confidence=confidence,
                sources=sources,
                fallback_used=True,
                requires_verification=True,
                warnings=[
                    "Using SarkarSetu's offline knowledge base. Some information may not reflect the latest government updates."
                ],
                metadata={"match_type": match_type},
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Local knowledge retrieval failed for uncertain intent", extra={"error": str(exc)}
            )
            return None

    def _format_context(self, ctx: PipelineContext) -> str:
        """Format conversation context as a string for prompts."""
        messages = ctx.context_dict.get("messages", []) or []
        if not isinstance(messages, list):
            return "No previous conversation history."
        if not messages:
            return "No previous conversation history."

        lines: list[str] = []
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role", "unknown"))
            content = str(m.get("content", ""))
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _empty_intent(self) -> IntentDetectionResult:
        """Return a minimal IntentDetectionResult for fallback cases."""
        return IntentDetectionResult(
            primary_intent=Intent.UNKNOWN,
            secondary_intents=[],
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            requires_clarification=True,
            clarification_question=None,
            reasoning_summary="Unable to classify intent",
            detected_language=LanguageCode.UNKNOWN,
            is_follow_up=False,
            referenced_entity=None,
            urgency=UrgencyLevel.NORMAL,
            risk_flags=[],
            taxonomy_version="1.0.0",
        )

    @staticmethod
    def _system_instruction() -> str:
        return (
            "You are SarkarSetu AI, an assistant that helps Indian entrepreneurs "
            "navigate government services. Provide helpful, accurate guidance. "
            "Do not invent government rules, schemes, deadlines, fees, or "
            "official approvals. Clearly distinguish verified information from "
            "general guidance. Never claim registration is complete or that the "
            "user is approved for any scheme."
        )

    # ------------------------------------------------------------------
    # Stage 10 — Persist assistant message
    # ------------------------------------------------------------------
    async def _persist_assistant_message(self, ctx: PipelineContext) -> None:
        if ctx.conversation is None or not ctx.assistant_response_text:
            return

        intent_name = (
            ctx.intent_result.primary_intent.value
            if ctx.intent_result
            else None
        )
        confidence = (
            ctx.intent_result.confidence
            if ctx.intent_result
            else None
        )

        metadata: dict[str, object] = {
            "response_type": ctx.response_type.value,
            "intent": intent_name,
            "confidence": confidence,
            "clarification_required": ctx.clarification_state is not None,
            "provider": ctx.provider,
            "fallback_used": ctx.fallback_used,
        }
        if ctx.confidence is not None:
            metadata["confidence_score"] = ctx.confidence
        if ctx.entities:
            metadata["entities"] = [
                {
                    "entity_type": e.entity_type.value,
                    "value": e.value,
                    "confidence": e.confidence,
                    "source": e.source,
                }
                for e in ctx.entities
            ]
        if ctx.ai_model:
            metadata["ai_model"] = ctx.ai_model
        if ctx.retrieval_sources:
            metadata["retrieval_sources"] = ctx.retrieval_sources
        if ctx.agent_result:
            metadata["agent_name"] = ctx.agent_result.agent_name
            metadata["agent_status"] = ctx.agent_result.status.value
            if ctx.agent_result.structured_data:
                metadata["agent_structured_data"] = ctx.agent_result.structured_data

        message = await self.conversation_service.persist_assistant_message(
            conversation_id=ctx.conversation.id,
            user_id=ctx.user_id,
            content=ctx.assistant_response_text,
            intent=intent_name,
            message_metadata=metadata,
        )
        if message is None:
            ctx.warnings.append("Failed to persist assistant message")
            return

        ctx.assistant_message = message

    # ------------------------------------------------------------------
    # Response building
    # ------------------------------------------------------------------
    def _build_response(
        self, ctx: PipelineContext, start_time: float
    ) -> ChatMessageResponse:
        """Build the final ChatMessageResponse from pipeline context."""
        intent_summary: IntentSummary | None = None
        if ctx.intent_result:
            intent_summary = IntentSummary(
                primary_intent=ctx.intent_result.primary_intent.value,
                secondary_intents=[
                    i.value for i in ctx.intent_result.secondary_intents
                ],
                confidence=ctx.intent_result.confidence,
                confidence_level=ctx.intent_result.confidence_level,
                requires_clarification=ctx.intent_result.requires_clarification,
                clarification_question=ctx.intent_result.clarification_question,
            )

        entities_summary = [
            ExtractedEntitySummary(
                entity_type=e.entity_type.value,
                value=e.value,
                confidence=e.confidence,
                source=e.source,
                needs_clarification=e.needs_clarification,
            )
            for e in ctx.entities
        ]

        clarification_required = bool(
            ctx.clarification_state is not None
            or (
                ctx.intent_result is not None
                and ctx.intent_result.requires_clarification
            )
            or (
                ctx.agent_result is not None
                and ctx.agent_result.status
                in (
                    AgentStatus.NEEDS_INFORMATION,
                    AgentStatus.NEEDS_RETRIEVAL,
                    AgentStatus.NEEDS_VERIFICATION,
                )
            )
        )
        clarification_question: str | None = None
        if ctx.intent_result:
            clarification_question = ctx.intent_result.clarification_question
        if ctx.clarification_state:
            q = ctx.clarification_state.get("question")
            if isinstance(q, str):
                clarification_question = q
        if ctx.agent_result and ctx.agent_result.clarification_question:
            clarification_question = ctx.agent_result.clarification_question

        conversation_status = "active"
        if ctx.conversation:
            conversation_status = (
                "archived"
                if ctx.conversation.is_deleted
                else ctx.conversation.status
            )

        user_message_id = (
            ctx.user_message.id if ctx.user_message is not None else uuid4()
        )
        assistant_message_id = (
            ctx.assistant_message.id
            if ctx.assistant_message is not None
            else uuid4()
        )

        return ChatMessageResponse(
            conversation_id=ctx.conversation_id or uuid4(),
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            assistant_response=ctx.assistant_response_text,
            intent=intent_summary or self._empty_intent_summary(),
            extracted_entities=entities_summary,
            clarification_required=clarification_required,
            clarification_question=clarification_question,
            warnings=ctx.warnings,
            response_type=ctx.response_type,
            conversation_status=conversation_status,
            ai_model=ctx.ai_model,
            provider=ctx.provider,
            fallback_used=ctx.fallback_used,
            confidence=ctx.confidence,
            created_at=datetime.now(UTC),
        )

    def _empty_intent_summary(self) -> IntentSummary:
        return IntentSummary(
            primary_intent="unknown",
            secondary_intents=[],
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            requires_clarification=True,
            clarification_question=None,
        )

    async def get_conversation_status(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ConversationStatusResponse | None:
        """Get the status of a conversation for the status API endpoint.

        Returns None if the conversation is not found or not owned by the user.
        """
        conversation = await self.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            return None

        state = await self.clarification_service.get_clarification_state(
            conversation_id=conversation_id
        )

        last_message_at = None
        if conversation.updated_at:
            last_message_at = conversation.updated_at

        clarification_question: str | None = None
        if state:
            q = state.get("question")
            if isinstance(q, str):
                clarification_question = q

        return ConversationStatusResponse(
            conversation_id=conversation.id,
            status="archived" if conversation.is_deleted else conversation.status,
            clarification_pending=state is not None,
            clarification_question=clarification_question,
            business_profile_id=conversation.business_profile_id,
            last_message_at=last_message_at,
        )
