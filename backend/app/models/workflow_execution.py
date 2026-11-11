"""Workflow execution database models.

Defines versioned, auditable workflow execution models for tracking
multi-step government service workflows (Udyam registration, GST
registration, MSME scheme discovery).

Workflow executions are immutable once created - historical executions
are preserved for audit and reproducibility.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.business import BusinessProfile
    from app.models.conversation import Conversation
    from app.models.user import User


class WorkflowExecution(Base):
    """A persisted workflow execution result.

    Historical workflow executions are never overwritten. Each
    execution stores a snapshot of the input data, the service type,
    and the complete evaluation outcome for audit and reproducibility.
    """

    __tablename__ = "workflow_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    workflow_id: Mapped[str] = mapped_column(
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
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    workflow_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    current_step: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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
    step_results: Mapped[list[dict]] = mapped_column(
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        foreign_keys=[conversation_id],
        lazy="selectin",
    )
    steps: Mapped[list["WorkflowStep"]] = relationship(
        "WorkflowStep",
        back_populates="workflow_execution",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_number",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "workflow_status IN ('not_started', 'in_progress', 'needs_information', "
            "'needs_retrieval', 'needs_verification', 'eligibility_pending', "
            "'eligibility_complete', 'actions_available', 'completed', 'failed', 'cancelled')",
            name="ck_workflow_executions_workflow_status_valid",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowExecution(workflow_id={self.workflow_id}, "
            f"service_type={self.service_type}, status={self.workflow_status})>"
        )


class WorkflowStep(Base):
    """A single step within a workflow execution.

    Tracks the execution state of individual steps within a workflow,
    including their status, results, and any missing information.
    """

    __tablename__ = "workflow_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    step_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    step_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    step_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    step_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    structured_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    missing_information: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    clarification_question: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    evidence_references: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    next_step_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_final: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    workflow_execution: Mapped["WorkflowExecution"] = relationship(
        "WorkflowExecution",
        back_populates="steps",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "step_status IN ('pending', 'completed', 'needs_information', "
            "'needs_retrieval', 'needs_verification', 'failed')",
            name="ck_workflow_steps_step_status_valid",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowStep(step_id={self.step_id}, "
            f"step_name={self.step_name}, step_status={self.step_status})>"
        )
