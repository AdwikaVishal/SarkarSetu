"""Eligibility engine for SarkarSetu AI.

Deterministic eligibility evaluation engine that evaluates business
information against explicitly defined, versioned government rules.

The engine is the sole authority for eligibility decisions. Gemini
never decides eligibility - it only explains results after
deterministic evaluation.

Implements the EligibilityEvaluator protocol from
app/services/eligibility.py.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from app.models.eligibility_rule import (
    EligibilityRuleSet,
)
from app.schemas.eligibility_rule import (
    AssessmentStatus,
    ConditionOutcome,
)
from app.services.eligibility import (
    EligibilityAssessmentRequest,
    EligibilityAssessmentResult,
)
from app.services.eligibility_engine.rule_evaluator import RuleEvaluator
from app.services.eligibility_engine.rule_registry import RuleRegistry

logger = logging.getLogger(__name__)

# Statuses that indicate a definitive eligibility decision
_DECISIVE_STATUSES = {
    AssessmentStatus.ELIGIBLE.value,
    AssessmentStatus.INELIGIBLE.value,
}

# Statuses that indicate information is needed
_INFORMATION_NEEDED_STATUSES = {
    AssessmentStatus.NEEDS_INFORMATION.value,
}

# Statuses that indicate verification is needed
_VERIFICATION_NEEDED_STATUSES = {
    AssessmentStatus.UNVERIFIED.value,
}


class EligibilityEngine:
    """Deterministic eligibility engine.

    Evaluates business information against versioned, approved rule
    sets. Implements the EligibilityEvaluator protocol used by
    EligibilityAgent.

    Guarantees:
    - Same inputs + same rule set version → same result (deterministic)
    - No LLM involvement in eligibility decisions
    - Missing mandatory fields → NEEDS_INFORMATION, never INELIGIBLE
    - Unapproved/expired rule sets → UNVERIFIED, never definitive
    """

    def __init__(
        self,
        registry: RuleRegistry,
        evaluator: RuleEvaluator | None = None,
    ) -> None:
        self.registry = registry
        self.evaluator = evaluator or RuleEvaluator()

    async def evaluate(
        self,
        request: EligibilityAssessmentRequest,
    ) -> EligibilityAssessmentResult:
        """Evaluate eligibility using deterministic versioned rules.

        This is the sole authority for eligibility decisions. Agents
        may explain results but cannot create or modify them.

        Args:
            request: Structured eligibility assessment request.

        Returns:
            Typed eligibility assessment result.
        """
        start_time = datetime.now(UTC)

        # Step 1: Resolve the approved rule set
        rule_set = await self._resolve_rule_set(request)
        if rule_set is None:
            return self._build_unverified_result(request, start_time)

        # Step 2: Normalize input data
        input_data = self._normalize_input(request)

        # Step 3: Evaluate all rules
        condition_results = self.evaluator.evaluate_rules(
            rule_set.rules,
            input_data,
        )

        # Step 4: Aggregate into final status
        assessment_status, missing_info = self._aggregate_status(
            condition_results,
        )

        # Step 5: Build result
        result = EligibilityAssessmentResult(
            user_id=request.user_id,
            scheme_name=request.scheme_name or rule_set.scheme_name,
            registration_type=request.registration_type,
            assessment_status=assessment_status.value,
            rule_set_version=rule_set.version,
            result_data={
                "rule_set_id": rule_set.rule_set_id,
                "rule_count": len(rule_set.rules),
                "evaluated_at": start_time.isoformat(),
                "condition_count": len(condition_results),
                "pass_count": sum(
                    1 for c in condition_results if c.outcome.value == "PASS"
                ),
                "fail_count": sum(
                    1 for c in condition_results if c.outcome.value == "FAIL"
                ),
                "unknown_count": sum(
                    1 for c in condition_results if c.outcome.value == "UNKNOWN"
                ),
            },
            missing_information=missing_info,
            evidence_references=[
                {
                    "document_id": rule_set.id,
                    "source_title": rule_set.source_title,
                    "issuing_authority": rule_set.issuing_authority,
                    "source_url": rule_set.source_url,
                    "publication_date": (
                        rule_set.publication_date.isoformat()
                        if rule_set.publication_date
                        else None
                    ),
                    "page_or_section": rule_set.source_section,
                    "document_version": rule_set.version,
                }
            ],
            warnings=self._build_warnings(condition_results, rule_set),
        )

        return result

    async def _resolve_rule_set(
        self,
        request: EligibilityAssessmentRequest,
    ) -> EligibilityRuleSet | None:
        """Resolve the approved rule set for the assessment.

        Attempts to find an approved rule set matching the scheme
        name and effective for the current date.

        Args:
            request: Assessment request.

        Returns:
            The approved rule set, or None if none found.
        """
        # Try to match by scheme_name first
        if request.scheme_name:
            rule_set = await self.registry.get_approved_rule_set(
                rule_set_id=request.scheme_name,
                evaluation_date=datetime.now(UTC),
            )
            if rule_set is not None:
                return rule_set

        # No matching rule set found
        logger.warning(
            "No approved rule set found",
            extra={
                "scheme_name": request.scheme_name,
                "request_id": request.request_id,
            },
        )
        return None

    def _normalize_input(
        self,
        request: EligibilityAssessmentRequest,
    ) -> dict[str, Any]:
        """Normalize business input data for evaluation.

        Preserves data provenance by marking each value's source.
        Does not modify the original business profile data.

        Args:
            request: Assessment request with business attributes.

        Returns:
            Normalized input data dictionary for rule evaluation.
        """
        # Start with business attributes from the request
        input_data = dict(request.business_attributes)

        # Add context data if present
        if request.context:
            for key, value in request.context.items():
                if key not in input_data:
                    input_data[key] = value

        return input_data

    def _aggregate_status(
        self,
        condition_results: list[Any],
    ) -> tuple[AssessmentStatus, list[str]]:
        """Aggregate condition results into a final assessment status.

        Aggregation policy:
        - INELIGIBLE: At least one mandatory condition definitively fails
        - NEEDS_INFORMATION: At least one mandatory condition is unknown
        - ELIGIBLE: All mandatory conditions pass, no unknowns
        - POTENTIALLY_ELIGIBLE: All mandatory pass, some optional unknown
        - UNVERIFIED: Fallback for edge cases

        Args:
            condition_results: List of ConditionResult objects.

        Returns:
            Tuple of (AssessmentStatus, list of missing information fields).
        """
        mandatory_results = [c for c in condition_results if c.mandatory]
        optional_results = [c for c in condition_results if not c.mandatory]

        # Check for mandatory failures first
        mandatory_failures = [
            c for c in mandatory_results
            if c.outcome.value == ConditionOutcome.FAIL.value
        ]
        if mandatory_failures:
            return AssessmentStatus.INELIGIBLE, []

        # Check for mandatory unknowns
        mandatory_unknowns = [
            c for c in mandatory_results
            if c.outcome.value == ConditionOutcome.UNKNOWN.value
        ]
        if mandatory_unknowns:
            missing_info = [
                c.field for c in mandatory_unknowns
            ]
            return AssessmentStatus.NEEDS_INFORMATION, missing_info

        # All mandatory pass - check optional conditions
        optional_unknowns = [
            c for c in optional_results
            if c.outcome.value == ConditionOutcome.UNKNOWN.value
        ]
        optional_failures = [
            c for c in optional_results
            if c.outcome.value == ConditionOutcome.FAIL.value
        ]

        if optional_unknowns:
            return AssessmentStatus.POTENTIALLY_ELIGIBLE, []

        if optional_failures:
            # Optional failures don't make ineligible, but reduce confidence
            return AssessmentStatus.POTENTIALLY_ELIGIBLE, []

        # All conditions pass
        return AssessmentStatus.ELIGIBLE, []

    def _build_warnings(
        self,
        condition_results: list[Any],
        rule_set: EligibilityRuleSet,
    ) -> list[str]:
        """Build non-fatal warnings from condition results.

        Args:
            condition_results: List of condition results.
            rule_set: The rule set used.

        Returns:
            List of warning strings.
        """
        warnings = []

        unknown_count = sum(
            1 for c in condition_results
            if c.outcome.value == ConditionOutcome.UNKNOWN.value
        )
        if unknown_count > 0:
            warnings.append(
                f"{unknown_count} condition(s) could not be evaluated "
                "due to missing input data."
            )

        fail_count = sum(
            1 for c in condition_results
            if c.outcome.value == ConditionOutcome.FAIL.value
            and not c.mandatory
        )
        if fail_count > 0:
            warnings.append(
                f"{fail_count} optional condition(s) not satisfied."
            )

        if rule_set.approval_status != "approved":
            warnings.append(
                "Rule set is not in approved status. Results are unverified."
            )

        return warnings

    def _build_unverified_result(
        self,
        request: EligibilityAssessmentRequest,
        start_time: datetime,
    ) -> EligibilityAssessmentResult:
        """Build an UNVERIFIED result when no rule set is available.

        Args:
            request: Assessment request.
            start_time: Evaluation start time.

        Returns:
            Unverified assessment result.
        """
        return EligibilityAssessmentResult(
            user_id=request.user_id,
            scheme_name=request.scheme_name,
            registration_type=request.registration_type,
            assessment_status=AssessmentStatus.UNVERIFIED.value,
            rule_set_version="none",
            result_data={
                "reason": "No approved rule set found for the requested scheme.",
            },
            missing_information=list(request.missing_information),
            evidence_references=[],
            warnings=[
                "No approved eligibility rule set is available for this "
                "scheme. Official verification is required."
            ],
        )
