"""Eligibility assessment API router.

Provides authenticated endpoints for running and retrieving
eligibility assessments:

- POST /api/v1/eligibility/assess - Run an eligibility assessment
- GET /api/v1/eligibility/assessments/{assessment_id} - Get an assessment
- GET /api/v1/eligibility/businesses/{business_id}/assessments - List assessments
- POST /api/v1/eligibility/rule-sets - Create a rule set (administrative)
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.eligibility_rule import (
    AssessmentStatus,
    ConditionResult,
    EligibilityAssessmentResponse,
    RuleCreateRequest,
    RuleSetResponse,
    RuleStatus,
)
from app.services.eligibility import EligibilityAssessmentRequest
from app.services.eligibility_engine.assessment_service import (
    EligibilityAssessmentService,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.eligibility_engine.rule_registry import RuleRegistry
from app.services.ownership import OwnershipService

router = APIRouter(prefix="/eligibility", tags=["eligibility"])


async def get_rule_registry(
    db: AsyncSession = Depends(get_db),
) -> RuleRegistry:
    """Dependency to get RuleRegistry instance."""
    return RuleRegistry(db)


async def get_eligibility_engine(
    registry: RuleRegistry = Depends(get_rule_registry),
) -> EligibilityEngine:
    """Dependency to get EligibilityEngine instance."""
    from app.services.eligibility_engine.rule_evaluator import RuleEvaluator

    return EligibilityEngine(
        registry=registry,
        evaluator=RuleEvaluator(),
    )


async def get_assessment_service(
    db: AsyncSession = Depends(get_db),
    engine: EligibilityEngine = Depends(get_eligibility_engine),
) -> EligibilityAssessmentService:
    """Dependency to get EligibilityAssessmentService instance."""

    return EligibilityAssessmentService(
        db=db,
        engine=engine,
        ownership_service=OwnershipService(db),
    )


def _build_condition_results(
    result: Any,
) -> list[ConditionResult]:
    """Build condition result objects from engine result.

    The engine stores condition results in result_data or
    condition_results field. Extract them for the API response.
    """
    condition_results = getattr(result, "condition_results", None)
    if condition_results is not None:
        return [
            ConditionResult(
                rule_id=c.get("rule_id", ""),
                description=c.get("description", ""),
                field=c.get("field", ""),
                operator=c.get("operator", ""),
                expected_value=c.get("expected_value"),
                actual_value=c.get("actual_value"),
                outcome=c.get("outcome", ""),
                mandatory=c.get("mandatory", False),
                source_reference=c.get("source_reference"),
                failure_message=c.get("failure_message"),
            )
            for c in condition_results
        ]
    # Fallback: extract from result_data if stored there
    result_data = getattr(result, "result_data", {}) or {}
    stored = result_data.get("condition_results", [])
    return [
        ConditionResult(
            rule_id=c.get("rule_id", ""),
            description=c.get("description", ""),
            field=c.get("field", ""),
            operator=c.get("operator", ""),
            expected_value=c.get("expected_value"),
            actual_value=c.get("actual_value"),
            outcome=c.get("outcome", ""),
            mandatory=c.get("mandatory", False),
            source_reference=c.get("source_reference"),
            failure_message=c.get("failure_message"),
        )
        for c in stored
    ]


@router.post(
    "/assess",
    response_model=EligibilityAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Run eligibility assessment",
    description=(
        "Evaluate business information against approved eligibility rules. "
        "The deterministic engine is the sole authority for eligibility "
        "decisions. Gemini is never used to determine eligibility."
    ),
)
async def assess_eligibility(
    request: EligibilityAssessmentRequest,
    service: EligibilityAssessmentService = Depends(get_assessment_service),
    current_user: User = Depends(get_current_active_user),
) -> EligibilityAssessmentResponse:
    """Run an eligibility assessment for the authenticated user.

    Requires authentication. The user_id is taken from the JWT token,
    never from client input.

    If a business_profile_id is provided, ownership is verified.
    Archived business profiles are rejected for new assessments.
    """
    # Override user_id from JWT - never trust client-supplied user_id
    request.user_id = current_user.id

    result = await service.assess(request)

    condition_results = _build_condition_results(result)

    return EligibilityAssessmentResponse(
        assessment_id=result.assessment_id,
        user_id=result.user_id,
        business_profile_id=request.business_profile_id,
        rule_set_id=result.result_data.get("rule_set_id", ""),
        rule_set_version=result.rule_set_version,
        scheme_name=result.scheme_name,
        registration_type=result.registration_type,
        assessment_status=AssessmentStatus(result.assessment_status),
        result_data=result.result_data,
        missing_information=result.missing_information,
        condition_results=condition_results,
        evidence_references=result.evidence_references,
        warnings=result.warnings,
        evaluated_at=result.evaluated_at,
    )


@router.get(
    "/assessments/{assessment_id}",
    response_model=EligibilityAssessmentResponse,
    summary="Get eligibility assessment",
    description="Retrieve a persisted eligibility assessment by ID.",
)
async def get_assessment(
    assessment_id: UUID,
    service: EligibilityAssessmentService = Depends(get_assessment_service),
    current_user: User = Depends(get_current_active_user),
) -> EligibilityAssessmentResponse:
    """Get an eligibility assessment by ID.

    Requires authentication and assessment ownership.
    """
    result = await service.get_assessment(str(assessment_id), current_user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or not owned by user",
        )

    condition_results = _build_condition_results(result)

    return EligibilityAssessmentResponse(
        assessment_id=result.assessment_id,
        user_id=result.user_id,
        business_profile_id=result.business_profile_id,
        rule_set_id=result.result_data.get("rule_set_id", ""),
        rule_set_version=result.rule_set_version,
        scheme_name=result.scheme_name,
        registration_type=result.registration_type,
        assessment_status=AssessmentStatus(result.assessment_status),
        result_data=result.result_data,
        missing_information=result.missing_information,
        condition_results=condition_results,
        evidence_references=result.evidence_references,
        warnings=result.warnings,
        evaluated_at=result.evaluated_at,
    )


@router.get(
    "/businesses/{business_id}/assessments",
    response_model=list[EligibilityAssessmentResponse],
    summary="List business assessments",
    description="List all eligibility assessments for a business profile.",
)
async def list_business_assessments(
    business_id: UUID,
    service: EligibilityAssessmentService = Depends(get_assessment_service),
    current_user: User = Depends(get_current_active_user),
) -> list[EligibilityAssessmentResponse]:
    """List all assessments for a business profile.

    Requires authentication and business profile ownership.
    """
    results = await service.list_assessments_for_business(business_id, current_user.id)

    response_list = []
    for r in results:
        condition_results = _build_condition_results(r)
        response_list.append(
            EligibilityAssessmentResponse(
                assessment_id=r.assessment_id,
                user_id=r.user_id,
                business_profile_id=r.business_profile_id,
                rule_set_id=r.result_data.get("rule_set_id", ""),
                rule_set_version=r.rule_set_version,
                scheme_name=r.scheme_name,
                registration_type=r.registration_type,
                assessment_status=AssessmentStatus(r.assessment_status),
                result_data=r.result_data,
                missing_information=r.missing_information,
                condition_results=condition_results,
                evidence_references=r.evidence_references,
                warnings=r.warnings,
                evaluated_at=r.evaluated_at,
            )
        )
    return response_list


@router.post(
    "/rule-sets",
    response_model=RuleSetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create rule set (administrative)",
    description=(
        "Register a new eligibility rule set. Only APPROVED rule sets "
        "are used in production assessments. Requires administrative "
        "privileges (not enforced in this version)."
    ),
)
async def create_rule_set(
    request: RuleCreateRequest,
    service: EligibilityAssessmentService = Depends(get_assessment_service),
    current_user: User = Depends(get_current_active_user),
) -> RuleSetResponse:
    """Create a new eligibility rule set (administrative endpoint).

    Rule sets are created in DRAFT status and must be explicitly
    approved before they can be used in assessments.
    """
    from app.services.eligibility_engine.rule_loader import RuleLoader

    loader = RuleLoader()
    rule_set = loader.load_rule_set(
        request,
        created_by=current_user.id,
    )

    # Persist via registry
    registry = RuleRegistry(service.db)
    persisted = await registry.register_rule_set(rule_set)

    return RuleSetResponse(
        rule_set_id=persisted.rule_set_id,
        version=persisted.version,
        scheme_id=persisted.scheme_id,
        scheme_name=persisted.scheme_name,
        description=persisted.description,
        jurisdiction=persisted.jurisdiction,
        issuing_authority=persisted.issuing_authority,
        source_title=persisted.source_title,
        source_url=persisted.source_url,
        source_section=persisted.source_section,
        publication_date=persisted.publication_date,
        effective_from=persisted.effective_from,
        effective_until=persisted.effective_until,
        approval_status=RuleStatus(persisted.approval_status),
        approved_at=persisted.approved_at,
        approved_by=persisted.approved_by,
        created_at=persisted.created_at,
        created_by=persisted.created_by,
        rule_count=len(persisted.rules),
    )
