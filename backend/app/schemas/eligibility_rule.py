"""Eligibility rule schemas.

Defines Pydantic models for rule definitions, rule sets, evaluation
results, and assessment requests/responses.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class RuleOperator(str, Enum):
    """Supported rule evaluation operators.

    Only explicitly implemented operations are permitted. No
    arbitrary code execution or expression evaluation is supported.
    """

    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    IN = "IN"
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"
    IS_TRUE = "IS_TRUE"
    IS_FALSE = "IS_FALSE"
    IS_PRESENT = "IS_PRESENT"
    IS_MISSING = "IS_MISSING"


class ConditionOutcome(str, Enum):
    """Outcome of evaluating a single rule condition."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RuleStatus(str, Enum):
    """Rule set approval lifecycle status."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    RETIRED = "retired"


class AssessmentStatus(str, Enum):
    """Final eligibility assessment status."""

    ELIGIBLE = "eligible"
    POTENTIALLY_ELIGIBLE = "potentially_eligible"
    INELIGIBLE = "ineligible"
    NEEDS_INFORMATION = "needs_information"
    UNVERIFIED = "unverified"


class DataProvenance(str, Enum):
    """Provenance of input data used in evaluation."""

    BUSINESS_PROFILE = "BUSINESS_PROFILE"
    USER_CONFIRMED = "USER_CONFIRMED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    UNKNOWN = "UNKNOWN"


class RuleCondition(BaseModel):
    """A single rule condition within a rule set.

    Each condition references a field, applies an operator to an
    expected value, and produces a deterministic outcome.
    """

    rule_id: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    field: str = Field(..., min_length=1, max_length=255)
    operator: RuleOperator
    expected_value: Any = Field(..., description="Expected value for comparison.")
    mandatory: bool = Field(
        default=False,
        description="Whether this rule is mandatory for eligibility.",
    )
    priority: int = Field(
        default=0,
        description="Evaluation priority (lower numbers first).",
    )
    source_reference: str | None = Field(
        default=None,
        max_length=500,
        description="Source reference for this rule.",
    )
    failure_message: str | None = Field(
        default=None,
        max_length=1000,
        description="User-facing message when this rule fails.",
    )


class RuleSetDefinition(BaseModel):
    """A complete rule set definition for creating or updating rules.

    Used for rule authoring and approval workflows. Not used for
    evaluation directly - the engine works with database models.
    """

    rule_set_id: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., min_length=1, max_length=50)
    scheme_id: str | None = Field(default=None, max_length=100)
    scheme_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    jurisdiction: str | None = Field(default=None, max_length=100)
    issuing_authority: str | None = Field(default=None, max_length=255)
    source_title: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=1000)
    source_section: str | None = Field(default=None, max_length=255)
    publication_date: datetime | None = None
    effective_from: datetime
    effective_until: datetime | None = None
    rules: list[RuleCondition] = Field(..., min_length=1)


class ConditionResult(BaseModel):
    """Result of evaluating a single condition."""

    rule_id: str
    description: str
    field: str
    operator: RuleOperator
    expected_value: Any
    actual_value: Any | None = None
    outcome: ConditionOutcome
    mandatory: bool
    source_reference: str | None = None
    failure_message: str | None = None


class AssessmentResult(BaseModel):
    """Structured result of an eligibility assessment.

    Returned by the engine to the EligibilityAgent and API layer.
    """

    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: UUID
    business_profile_id: UUID | None = None
    rule_set_id: str
    rule_set_version: str
    scheme_name: str | None = None
    registration_type: str | None = None
    assessment_status: AssessmentStatus
    result_data: dict[str, Any] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    condition_results: list[ConditionResult] = Field(default_factory=list)
    evidence_references: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EligibilityAssessmentRequest(BaseModel):
    """Request sent to the eligibility engine for assessment.

    Mirrors the protocol in app/services/eligibility.py for API
    layer compatibility.

    user_id is optional in the request because it is always overridden
    from the authenticated JWT token in the API layer.
    """

    user_id: UUID | None = None
    business_profile_id: UUID | None = None
    scheme_name: str | None = None
    registration_type: str | None = None
    business_attributes: dict[str, Any] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: str(uuid4()))


class EligibilityAssessmentResponse(BaseModel):
    """Response returned to the API client after assessment."""

    assessment_id: str
    user_id: UUID
    business_profile_id: UUID | None
    rule_set_id: str
    rule_set_version: str
    scheme_name: str | None
    registration_type: str | None
    assessment_status: AssessmentStatus
    result_data: dict[str, Any]
    missing_information: list[str]
    condition_results: list[ConditionResult]
    evidence_references: list[dict[str, Any]]
    warnings: list[str]
    evaluated_at: datetime


class RuleSetResponse(BaseModel):
    """Response for rule set queries."""

    rule_set_id: str
    version: str
    scheme_id: str | None
    scheme_name: str | None
    description: str | None
    jurisdiction: str | None
    issuing_authority: str | None
    source_title: str | None
    source_url: str | None
    source_section: str | None
    publication_date: datetime | None
    effective_from: datetime
    effective_until: datetime | None
    approval_status: RuleStatus
    approved_at: datetime | None
    approved_by: UUID | None
    created_at: datetime
    created_by: UUID | None
    rule_count: int

    model_config = {"from_attributes": True}


class RuleCreateRequest(BaseModel):
    """Request to create a new rule set (administrative)."""

    rule_set_id: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., min_length=1, max_length=50)
    scheme_id: str | None = Field(default=None, max_length=100)
    scheme_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    jurisdiction: str | None = Field(default=None, max_length=100)
    issuing_authority: str | None = Field(default=None, max_length=255)
    source_title: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=1000)
    source_section: str | None = Field(default=None, max_length=255)
    publication_date: datetime | None = None
    effective_from: datetime
    effective_until: datetime | None = None
    rules: list[RuleCondition] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_effective_dates(self) -> "RuleCreateRequest":
        if self.effective_until and self.effective_until < self.effective_from:
            raise ValueError("effective_until must be >= effective_from")
        return self
