"""Workflow API router.

Provides authenticated endpoints for workflow management:

- POST /api/v1/workflows - Start a new workflow execution
- GET /api/v1/workflows/{workflow_id} - Get workflow execution status
- POST /api/v1/workflows/{workflow_id}/respond - Respond to clarification
- POST /api/v1/workflows/{workflow_id}/resume - Resume a paused workflow
- POST /api/v1/workflows/{workflow_id}/cancel - Cancel a workflow
- GET /api/v1/workflows - List supported workflow service types
- GET /api/v1/workflows/history - List user's workflow executions
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.config import settings
from app.database.connection import get_db
from app.models.user import User
from app.schemas.workflow import (
    ClarificationResponse,
    ResumeWorkflowRequest,
    StepStatus,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowServiceTypeInfo,
    WorkflowServiceTypeResponse,
)
from app.schemas.workflow import WorkflowStepResult as SchemaWorkflowStepResult
from app.services.ai.ai_service import AIService
from app.services.conversation.clarification_service import ClarificationService
from app.services.conversation.conversation_service import ConversationService
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.eligibility_engine.rule_evaluator import RuleEvaluator
from app.services.eligibility_engine.rule_registry import RuleRegistry
from app.services.knowledge.provider import get_fixture_provider
from app.services.workflows.engine import WorkflowEngine
from app.services.workflows.registry import WorkflowRegistry
from app.services.workflows.state_manager import WorkflowStateManager
from app.services.workflows.step_executor import StepExecutor
from app.services.workflows.workflow_result import WorkflowStepResult as ServiceWorkflowStepResult

router = APIRouter(prefix="/workflows", tags=["workflows"])


async def get_ai_service() -> AIService:
    """Dependency to get AIService instance."""
    return AIService()


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    """Dependency to get ConversationService instance."""
    return ConversationService(db)


async def get_clarification_service(
    db: AsyncSession = Depends(get_db),
) -> ClarificationService:
    """Dependency to get ClarificationService instance."""
    return ClarificationService(db)


async def get_state_manager(
    db: AsyncSession = Depends(get_db),
) -> WorkflowStateManager:
    """Dependency to get WorkflowStateManager instance."""
    return WorkflowStateManager(db)


async def get_workflow_engine(
    state_manager: WorkflowStateManager = Depends(get_state_manager),
    ai_service: AIService = Depends(get_ai_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
    clarification_service: ClarificationService = Depends(get_clarification_service),
    db: AsyncSession = Depends(get_db),
) -> WorkflowEngine:
    """Dependency to get WorkflowEngine instance."""
    rule_registry = RuleRegistry(db)
    engine = EligibilityEngine(
        registry=rule_registry,
        evaluator=RuleEvaluator(),
    )
    knowledge_provider = get_fixture_provider(
        enabled=settings.knowledge_retrieval_enabled
    )
    return WorkflowEngine(
        state_manager=state_manager,
        step_executor=StepExecutor(
            ai_service=ai_service,
            conversation_service=conversation_service,
            clarification_service=clarification_service,
            eligibility_engine=engine,
            retrieval_provider=knowledge_provider,
        ),
        ai_service=ai_service,
        conversation_service=conversation_service,
        clarification_service=clarification_service,
        eligibility_engine=engine,
        retrieval_provider=knowledge_provider,
    )


async def get_workflow_registry(
    ai_service: AIService = Depends(get_ai_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
    clarification_service: ClarificationService = Depends(get_clarification_service),
    db: AsyncSession = Depends(get_db),
) -> WorkflowRegistry:
    """Dependency to get WorkflowRegistry instance."""
    rule_registry = RuleRegistry(db)
    engine = EligibilityEngine(
        registry=rule_registry,
        evaluator=RuleEvaluator(),
    )
    knowledge_provider = get_fixture_provider(
        enabled=settings.knowledge_retrieval_enabled
    )
    return WorkflowRegistry(
        ai_service=ai_service,
        conversation_service=conversation_service,
        clarification_service=clarification_service,
        eligibility_engine=engine,
        retrieval_provider=knowledge_provider,
    )


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post(
    "/",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a workflow execution",
    description=(
        "Start a new workflow execution for the given service type. "
        "The deterministic workflow engine processes the user message "
        "through a sequence of steps including clarification, "
        "retrieval, eligibility assessment, and response generation."
    ),
)
async def start_workflow(
    request: WorkflowExecutionRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowExecutionResponse:
    """Start a new workflow execution for the authenticated user.

    Requires authentication. The user_id is taken from the JWT token,
    never from client input.

    If a business_profile_id is provided, ownership is verified.
    Archived business profiles are rejected for new workflows.
    """
    try:
        result = await engine.execute_workflow(
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            service_type=request.service_type,
            message=request.message,
            business_profile_id=request.business_profile_id,
        )

        return WorkflowExecutionResponse(
            workflow_id=result.workflow_id,
            service_type=result.service_type,
            status=result.status,
            response=result.response,
            step_results=_convert_step_results(result.step_results),
            structured_data=result.structured_data,
            missing_information=result.missing_information,
            clarification_question=result.clarification_question,
            warnings=result.warnings,
            evidence_references=result.evidence_references,
            next_actions=result.next_actions,
            eligibility_assessment_id=result.eligibility_assessment_id,
            completed_at=result.completed_at,
            created_at=result.created_at,
        )

    except Exception as exc:  # noqa: BLE001 - safe error response
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Workflow execution error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing "
            "the workflow.",
        ) from exc


@router.get(
    "/{workflow_id}",
    response_model=WorkflowExecutionResponse,
    summary="Get workflow execution status",
    description="Retrieve a workflow execution by ID.",
)
async def get_workflow_execution(
    workflow_id: UUID,
    engine: WorkflowEngine = Depends(get_workflow_engine),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowExecutionResponse:
    """Get a workflow execution by ID.

    Requires authentication and workflow ownership.
    """
    state_manager = engine.state_manager
    execution = await state_manager.get_workflow_execution(
        workflow_id=str(workflow_id),
        user_id=current_user.id,
    )

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found or not owned by user",
        )

    return WorkflowExecutionResponse(
        workflow_id=execution.workflow_id,
        service_type=execution.service_type,
        status=execution.workflow_status,
        response=execution.result_data.get("result", {}).get(
            "response", ""
        ),
        step_results=[
            SchemaWorkflowStepResult(
                step_id=sr.get("step_id", ""),
                step_name=sr.get("step_name", ""),
                status=StepStatus(sr.get("status", "pending")),
                response=sr.get("response", ""),
                structured_data=sr.get("structured_data", {}),
                missing_information=sr.get("missing_information", []),
                clarification_question=sr.get("clarification_question"),
                warnings=sr.get("warnings", []),
                evidence_references=sr.get("evidence_references", []),
                next_step_id=sr.get("next_step"),
                is_final=sr.get("is_final", False),
            )
            for sr in execution.result_data.get("step_results", [])
        ],
        structured_data=execution.result_data,
        missing_information=execution.missing_information,
        clarification_question=execution.clarification_question,
        warnings=execution.warnings,
        evidence_references=execution.evidence_references,
        next_actions=execution.result_data.get("next_actions", []),
        eligibility_assessment_id=execution.result_data.get(
            "eligibility_assessment_id"
        ),
        completed_at=execution.completed_at,
        created_at=execution.created_at,
    )


@router.post(
    "/{workflow_id}/respond",
    response_model=WorkflowExecutionResponse,
    summary="Respond to clarification",
    description=(
        "Respond to a clarification question in an ongoing workflow. "
        "The workflow resumes from the clarification step with the "
        "user's answer."
    ),
)
async def respond_to_clarification(
    workflow_id: UUID,
    request: ClarificationResponse,
    engine: WorkflowEngine = Depends(get_workflow_engine),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowExecutionResponse:
    """Respond to a clarification question in an ongoing workflow.

    Requires authentication and workflow ownership.

    The response is treated as the user's answer to the clarification
    question. The workflow resumes from the clarification step.
    """
    state_manager = engine.state_manager
    execution = await state_manager.get_workflow_execution(
        workflow_id=str(workflow_id),
        user_id=current_user.id,
    )

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found or not owned by user",
        )

    if execution.workflow_status not in (
        "needs_information",
        "needs_retrieval",
        "needs_verification",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not waiting for clarification.",
        )

    # Re-execute the workflow with the clarification response
    result = await engine.execute_workflow(
        user_id=current_user.id,
        conversation_id=execution.conversation_id,
        service_type=execution.service_type,
        message=request.response,
        business_profile_id=execution.business_profile_id,
    )

    return WorkflowExecutionResponse(
        workflow_id=result.workflow_id,
        service_type=result.service_type,
        status=result.status,
        response=result.response,
        step_results=_convert_step_results(result.step_results),
        structured_data=result.structured_data,
        missing_information=result.missing_information,
        clarification_question=result.clarification_question,
        warnings=result.warnings,
        evidence_references=result.evidence_references,
        next_actions=result.next_actions,
        eligibility_assessment_id=result.eligibility_assessment_id,
        completed_at=result.completed_at,
        created_at=result.created_at,
    )


@router.post(
    "/{workflow_id}/resume",
    response_model=WorkflowExecutionResponse,
    summary="Resume a paused workflow",
    description=(
        "Resume a paused workflow execution. The workflow continues "
        "from the step where it was paused."
    ),
)
async def resume_workflow(
    workflow_id: UUID,
    request: ResumeWorkflowRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowExecutionResponse:
    """Resume a paused workflow execution.

    Requires authentication and workflow ownership.
    """
    state_manager = engine.state_manager
    execution = await state_manager.get_workflow_execution(
        workflow_id=str(workflow_id),
        user_id=current_user.id,
    )

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found or not owned by user",
        )

    if execution.workflow_status not in (
        "needs_information",
        "needs_retrieval",
        "needs_verification",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not in a resumable state.",
        )

    # Re-execute with the same message (the workflow already has the
    # user's previous message in context)
    result = await engine.execute_workflow(
        user_id=current_user.id,
        conversation_id=execution.conversation_id,
        service_type=execution.service_type,
        message=execution.result_data.get("message", ""),
        business_profile_id=execution.business_profile_id,
    )

    return WorkflowExecutionResponse(
        workflow_id=result.workflow_id,
        service_type=result.service_type,
        status=result.status,
        response=result.response,
        step_results=_convert_step_results(result.step_results),
        structured_data=result.structured_data,
        missing_information=result.missing_information,
        clarification_question=result.clarification_question,
        warnings=result.warnings,
        evidence_references=result.evidence_references,
        next_actions=result.next_actions,
        eligibility_assessment_id=result.eligibility_assessment_id,
        completed_at=result.completed_at,
        created_at=result.created_at,
    )


@router.post(
    "/{workflow_id}/cancel",
    response_model=WorkflowExecutionResponse,
    summary="Cancel a workflow execution",
    description=(
        "Cancel a workflow execution. The workflow status is set to "
        "'cancelled' and no further processing occurs."
    ),
)
async def cancel_workflow(
    workflow_id: UUID,
    engine: WorkflowEngine = Depends(get_workflow_engine),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowExecutionResponse:
    """Cancel a workflow execution.

    Requires authentication and workflow ownership.
    """
    state_manager = engine.state_manager
    execution = await state_manager.cancel_workflow(
        workflow_id=str(workflow_id),
        user_id=current_user.id,
    )

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found or not owned by user",
        )

    return WorkflowExecutionResponse(
        workflow_id=execution.workflow_id,
        service_type=execution.service_type,
        status=execution.workflow_status,
        response=execution.result_data.get("result", {}).get(
            "response", "Workflow cancelled."
        ),
        step_results=[
            SchemaWorkflowStepResult(
                step_id=sr.get("step_id", ""),
                step_name=sr.get("step_name", ""),
                status=StepStatus(sr.get("status", "pending")),
                response=sr.get("response", ""),
                structured_data=sr.get("structured_data", {}),
                missing_information=sr.get("missing_information", []),
                clarification_question=sr.get("clarification_question"),
                warnings=sr.get("warnings", []),
                evidence_references=sr.get("evidence_references", []),
                next_step_id=sr.get("next_step"),
                is_final=sr.get("is_final", False),
            )
            for sr in execution.result_data.get("step_results", [])
        ],
        structured_data=execution.result_data,
        missing_information=execution.missing_information,
        clarification_question=execution.clarification_question,
        warnings=execution.warnings,
        evidence_references=execution.evidence_references,
        next_actions=execution.result_data.get("next_actions", []),
        eligibility_assessment_id=execution.result_data.get(
            "eligibility_assessment_id"
        ),
        completed_at=execution.completed_at,
        created_at=execution.created_at,
    )


@router.get(
    "/",
    response_model=WorkflowServiceTypeResponse,
    summary="List supported workflow service types",
    description=(
        "List all workflow service types supported by the workflow "
        "engine. Each service type corresponds to a specific "
        "government service workflow (Udyam registration, GST "
        "registration, MSME scheme discovery, etc.)."
    ),
)
async def list_service_types(
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowServiceTypeResponse:
    """List all supported workflow service types.

    Returns the list of service types that can be used to start
    workflow executions, along with their descriptive names.
    """
    service_types = engine.get_supported_service_types()

    service_type_info = []
    for st in service_types:
        service_type_info.append(
            WorkflowServiceTypeInfo(
                service_type=st,
                display_name=st.replace("_", " ").title(),
                description=f"Workflow for {intent_label(st)}",
            )
        )

    return WorkflowServiceTypeResponse(
        service_types=service_type_info,
    )


def intent_label(intent: str) -> str:
    """Convert a service type identifier to a human-readable label."""
    return intent.replace("_", " ").title()


def _convert_step_results(
    step_results: list[ServiceWorkflowStepResult],
) -> list[SchemaWorkflowStepResult]:
    """Convert service WorkflowStepResult to schema WorkflowStepResult."""
    return [
        SchemaWorkflowStepResult(
            step_id=s.step_id,
            step_name=s.step_name,
            status=StepStatus(s.status),
            response=s.response,
            structured_data=s.structured_data,
            missing_information=s.missing_information,
            clarification_question=s.clarification_question,
            warnings=s.warnings,
            evidence_references=s.evidence_references,
            next_step_id=s.next_step,
            is_final=s.is_final,
        )
        for s in step_results
    ]
