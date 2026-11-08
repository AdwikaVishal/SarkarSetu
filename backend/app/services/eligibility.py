"""Deterministic eligibility evaluator interface.

Prompt 10 will implement the actual eligibility engine. For now,
this module defines the clean interface that the engine must
implement.

The EligibilityEvaluator accepts a structured assessment request
and returns a typed assessment result. It is the sole authority
for eligibility decisions — agents never make independent
eligibility determinations.

If no implementation exists, EligibilityEvaluatorUnavailable
gracefully reports that verification is required.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EligibilityAssessmentRequest(BaseModel):
    """Request sent to the deterministic eligibility engine.

    Contains all information needed to evaluate eligibility without
    exposing authentication tokens or secrets.
    """

    user_id: UUID = Field(..., description="Authenticated user ID.")
    business_profile_id: UUID | None = Field(
        default=None,
        description="Optional associated business profile ID.",
    )
    scheme_name: str | None = Field(
        default=None,
        description="Name of the scheme being assessed, if known.",
    )
    registration_type: str | None = Field(
        default=None,
        description="Type of registration being assessed, if known.",
    )
    business_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Known business attributes relevant to eligibility.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Information still needed from the user.",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context from conversation and agents.",
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique request correlation ID for tracing.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the request was created.",
    )


class EligibilityAssessmentResult(BaseModel):
    """Result returned by the deterministic eligibility engine.

    The engine is the sole authority for eligibility decisions.
    Agents may explain validated results but cannot create them.
    """

    assessment_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique assessment ID for tracing.",
    )
    user_id: UUID = Field(..., description="Authenticated user ID.")
    business_profile_id: UUID | None = Field(
        default=None,
        description="Optional associated business profile ID.",
    )
    scheme_name: str | None = Field(
        default=None,
        description="Name of the scheme assessed, if known.",
    )
    registration_type: str | None = Field(
        default=None,
        description="Type of registration assessed, if known.",
    )
    assessment_status: str = Field(
        ...,
        description="Eligibility status (eligible, ineligible, partial, unknown).",
    )
    rule_set_version: str = Field(
        ...,
        description="Version of the rule set used for evaluation.",
    )
    result_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured assessment result data.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Information still needed from the user.",
    )
    evidence_references: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source references for eligibility criteria.",
    )
    condition_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-condition evaluation outcomes.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings collected during evaluation.",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the assessment was evaluated.",
    )


@runtime_checkable
class EligibilityEvaluator(Protocol):
    """Protocol for deterministic eligibility evaluation.

    Prompt 10 will implement this protocol. Agents depend on this
    interface, not on any concrete implementation.
    """

    async def evaluate(
        self,
        request: EligibilityAssessmentRequest,
    ) -> EligibilityAssessmentResult:
        """Evaluate eligibility using deterministic versioned rules.

        Args:
            request: Structured eligibility assessment request.

        Returns:
            Typed eligibility assessment result.

        Raises:
            Should not raise for normal unavailability; return a
            result with assessment_status indicating verification
            is required. May raise for configuration errors.
        """
        ...


class EligibilityEvaluatorUnavailable:
    """Fallback implementation when no eligibility engine is connected.

    Agents using this evaluator will receive results indicating
    that verification is required and should return
    NEEDS_VERIFICATION status.
    """

    async def evaluate(
        self,
        request: EligibilityAssessmentRequest,
    ) -> EligibilityAssessmentResult:
        """Return a result indicating the evaluator is unavailable."""
        logger.warning(
            "EligibilityEvaluator not available",
            extra={
                "user_id": str(request.user_id),
                "scheme_name": request.scheme_name,
                "request_id": request.request_id,
            },
        )
        return EligibilityAssessmentResult(
            user_id=request.user_id,
            scheme_name=request.scheme_name,
            registration_type=request.registration_type,
            assessment_status="verification_required",
            rule_set_version="unavailable",
            result_data={},
            missing_information=list(request.missing_information),
            evidence_references=[],
            warnings=[
                "Deterministic eligibility engine is not configured. "
                "Official verification is required."
            ],
        )


def get_unavailable_evaluator() -> EligibilityEvaluatorUnavailable:
    """Factory function to create an unavailable evaluator instance."""
    return EligibilityEvaluatorUnavailable()
