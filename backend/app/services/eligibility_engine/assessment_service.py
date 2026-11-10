"""Assessment service for eligibility engine.

Coordinates input preparation, rule evaluation, result persistence,
and retrieval. Keeps evaluation logic separate from database
persistence.

Integrates with the existing EligibilityEvaluator protocol used by
EligibilityAgent.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eligibility_rule import (
    EligibilityAssessment,
)
from app.services.eligibility import (
    EligibilityAssessmentRequest,
    EligibilityAssessmentResult,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.ownership import OwnershipService, ResourceNotFoundError

logger = logging.getLogger(__name__)


class EligibilityAssessmentService:
    """Service for running and retrieving eligibility assessments.

    Coordinates the full assessment lifecycle:
    1. Validate business profile ownership
    2. Resolve the approved rule set
    3. Execute the eligibility engine
    4. Persist the assessment result
    5. Return a typed response

    Keeps evaluation logic (in the engine) separate from persistence.
    """

    def __init__(
        self,
        db: AsyncSession,
        engine: EligibilityEngine,
        ownership_service: OwnershipService | None = None,
    ) -> None:
        self.db = db
        self.engine = engine
        self.ownership = ownership_service or OwnershipService(db)

    async def assess(
        self,
        request: EligibilityAssessmentRequest,
    ) -> EligibilityAssessmentResult:
        """Run a complete eligibility assessment.

        Args:
            request: Structured eligibility assessment request.

        Returns:
            Typed eligibility assessment result.

        Raises:
            ResourceNotFoundError: If business profile is not found
                or not owned by the user.
            ValueError: If the request is invalid.
        """
        # Validate business profile ownership if provided
        if request.business_profile_id is not None:
            try:
                await self.ownership.get_user_business_profile(
                    user_id=request.user_id,
                    business_profile_id=request.business_profile_id,
                )
            except ResourceNotFoundError:
                logger.warning(
                    "Business profile not found or not owned",
                    extra={
                        "user_id": str(request.user_id),
                        "business_profile_id": str(
                            request.business_profile_id
                        ),
                    },
                )
                raise

        # Run the engine
        result = await self.engine.evaluate(request)

        # Persist the assessment
        await self._persist_assessment(request, result)

        return result

    async def get_assessment(
        self,
        assessment_id: str,
        user_id: UUID,
    ) -> EligibilityAssessmentResult | None:
        """Retrieve a persisted eligibility assessment.

        Only returns assessments owned by the requesting user.

        Args:
            assessment_id: Stable assessment identifier.
            user_id: Authenticated user ID.

        Returns:
            The assessment result, or None if not found or not owned.
        """
        result = await self.db.execute(
            select(EligibilityAssessment).where(
                EligibilityAssessment.assessment_id == assessment_id,
                EligibilityAssessment.user_id == user_id,
            )
        )
        assessment = result.scalar_one_or_none()
        if assessment is None:
            return None

        return self._assessment_to_result(assessment)

    async def list_assessments_for_business(
        self,
        business_profile_id: UUID,
        user_id: UUID,
    ) -> list[EligibilityAssessmentResult]:
        """List all assessments for a business profile.

        Only returns assessments owned by the requesting user.

        Args:
            business_profile_id: Business profile ID.
            user_id: Authenticated user ID.

        Returns:
            List of assessment results.
        """
        # Verify business profile ownership first
        try:
            await self.ownership.get_user_business_profile(
                user_id=user_id,
                business_profile_id=business_profile_id,
            )
        except ResourceNotFoundError:
            return []

        result = await self.db.execute(
            select(EligibilityAssessment).where(
                EligibilityAssessment.business_profile_id
                == business_profile_id,
                EligibilityAssessment.user_id == user_id,
            ).order_by(EligibilityAssessment.evaluated_at.desc())
        )
        assessments = list(result.scalars().all())
        return [
            self._assessment_to_result(a) for a in assessments
        ]

    async def _persist_assessment(
        self,
        request: EligibilityAssessmentRequest,
        result: EligibilityAssessmentResult,
    ) -> None:
        """Persist an assessment result to the database.

        Historical assessments are never overwritten.

        Args:
            request: Original assessment request.
            result: Engine assessment result.
        """
        # Resolve the rule set's database UUID from its string identifier.
        rule_set_db_id = None
        rule_set_id_str = result.result_data.get("rule_set_id")
        if rule_set_id_str:
            from app.services.eligibility_engine.rule_registry import RuleRegistry

            registry = RuleRegistry(self.db)
            rule_set = await registry.get_rule_set(
                rule_set_id_str, result.rule_set_version
            )
            if rule_set:
                rule_set_db_id = rule_set.id

        assessment = EligibilityAssessment(
            assessment_id=result.assessment_id,
            user_id=request.user_id,
            business_profile_id=request.business_profile_id,
            rule_set_id=rule_set_db_id,
            rule_set_version=result.rule_set_version,
            scheme_name=result.scheme_name,
            registration_type=request.registration_type,
            assessment_status=result.assessment_status,
            input_snapshot=dict(request.business_attributes),
            result_data=result.result_data,
            missing_information={
                "fields": result.missing_information,
            },
            rule_outcomes=result.result_data.get(
                "condition_outcomes", []
            ),
            evidence_references=result.evidence_references,
            warnings=result.warnings,
        )
        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        logger.info(
            "Assessment persisted",
            extra={
                "assessment_id": result.assessment_id,
                "status": result.assessment_status,
            },
        )

    def _assessment_to_result(
        self,
        assessment: EligibilityAssessment,
    ) -> EligibilityAssessmentResult:
        """Convert a persisted assessment to a typed result.

        Args:
            assessment: Persisted EligibilityAssessment model.

        Returns:
            EligibilityAssessmentResult.
        """
        return EligibilityAssessmentResult(
            assessment_id=assessment.assessment_id,
            user_id=assessment.user_id,
            scheme_name=assessment.scheme_name,
            registration_type=assessment.registration_type,
            assessment_status=assessment.assessment_status,
            rule_set_version=assessment.rule_set_version,
            result_data=assessment.result_data,
            missing_information=(
                assessment.missing_information.get("fields", [])
                if isinstance(assessment.missing_information, dict)
                else []
            ),
            evidence_references=assessment.evidence_references,
            warnings=assessment.warnings,
            evaluated_at=assessment.evaluated_at,
            business_profile_id=assessment.business_profile_id,
            condition_results=assessment.rule_outcomes or [],
        )
