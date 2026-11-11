"""Eligibility rule database models.

Defines versioned, auditable eligibility rule sets and their
individual conditions. Rules are immutable once approved and are
evaluated deterministically by the eligibility engine.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.business import BusinessProfile
    from app.models.user import User


class EligibilityRuleSet(Base):
    """A versioned, approved set of eligibility rules for a scheme.

    Rule sets are immutable once approved. Each version represents
    a complete, self-contained set of conditions that can be
    evaluated deterministically against business data.
    """

    __tablename__ = "eligibility_rule_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    rule_set_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    scheme_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    scheme_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    issuing_authority: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    source_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    source_section: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    publication_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    effective_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approval_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("users.id"),
        nullable=True,
    )

    # Relationships
    rules: Mapped[list["EligibilityRule"]] = relationship(
        "EligibilityRule",
        back_populates="rule_set",
        cascade="all, delete-orphan",
        order_by="EligibilityRule.priority",
        lazy="selectin",
    )
    assessments: Mapped[list["EligibilityAssessment"]] = relationship(
        "EligibilityAssessment",
        back_populates="rule_set",
        cascade="save-update, merge",
        lazy="selectin",
    )
    creator: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "rule_set_id",
            "version",
            name="uq_eligibility_rule_sets_rule_set_id_version",
        ),
        CheckConstraint(
            "approval_status IN ('draft', 'pending_review', 'approved', 'retired')",
            name="ck_eligibility_rule_sets_approval_status_valid",
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_until >= effective_from",
            name="ck_eligibility_rule_sets_effective_until_after_from",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EligibilityRuleSet(rule_set_id={self.rule_set_id}, "
            f"version={self.version}, status={self.approval_status})>"
        )


class EligibilityRule(Base):
    """A single condition within an eligibility rule set.

    Rules are evaluated deterministically. Each rule references a
    field, applies an operator to an expected value, and produces
    a PASS/FAIL/UNKNOWN/NOT_APPLICABLE outcome.
    """

    __tablename__ = "eligibility_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    rule_set_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("eligibility_rule_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    field: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    operator: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    expected_value: Mapped[Any] = mapped_column(
        JSONB,
        nullable=False,
    )
    mandatory: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    source_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    failure_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    # Relationships
    rule_set: Mapped["EligibilityRuleSet"] = relationship(
        "EligibilityRuleSet",
        back_populates="rules",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "rule_set_id",
            "rule_id",
            name="uq_eligibility_rules_rule_set_id_rule_id",
        ),
        CheckConstraint(
            "operator IN ('EQUALS', 'NOT_EQUALS', 'GREATER_THAN', "
            "'GREATER_THAN_OR_EQUAL', 'LESS_THAN', 'LESS_THAN_OR_EQUAL', "
            "'IN', 'NOT_IN', 'CONTAINS', 'IS_TRUE', 'IS_FALSE', "
            "'IS_PRESENT', 'IS_MISSING')",
            name="ck_eligibility_rules_operator_valid",
        ),
    )

    def __repr__(self) -> str:
        return f"<EligibilityRule(rule_id={self.rule_id}, field={self.field}, operator={self.operator})>"


class EligibilityAssessment(Base):
    """A persisted eligibility assessment result.

    Historical assessments are never overwritten. Each assessment
    stores a snapshot of the input data, the rule set version used,
    and the complete evaluation outcome for audit and reproducibility.
    """

    __tablename__ = "eligibility_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    assessment_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("business_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule_set_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("eligibility_rule_sets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule_set_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    scheme_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    registration_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    assessment_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    input_snapshot: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    result_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    missing_information: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    rule_outcomes: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    evidence_references: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    warnings: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    business_profile: Mapped["BusinessProfile | None"] = relationship(
        "BusinessProfile",
        foreign_keys=[business_profile_id],
        lazy="selectin",
    )
    rule_set: Mapped["EligibilityRuleSet | None"] = relationship(
        "EligibilityRuleSet",
        foreign_keys=[rule_set_id],
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "assessment_status IN ('eligible', 'potentially_eligible', "
            "'ineligible', 'needs_information', 'unverified')",
            name="ck_eligibility_assessments_assessment_status_valid",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EligibilityAssessment(assessment_id={self.assessment_id}, "
            f"status={self.assessment_status}, version={self.rule_set_version})>"
        )
