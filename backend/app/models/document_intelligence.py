"""Document Intelligence database models.

Defines models for document extraction results, fields, review items,
and audit events.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.business import BusinessProfile
    from app.models.document import UploadedDocument
    from app.models.user import User


class DocumentExtraction(Base):
    """Extracted document information from external providers.

    Stores the complete extraction result including all fields,
    provenance, and provider metadata.
    """

    __tablename__ = "document_extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    document_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    provider_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    extraction_status: Mapped[str] = mapped_column(
        String(50),
        default="extracted",
        nullable=False,
    )
    extracted_fields: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    normalized_fields: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    page_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    source_document_reference: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    raw_response: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    extraction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
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

    # Relationships
    document: Mapped["UploadedDocument"] = relationship(
        "UploadedDocument",
        back_populates="extraction",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User", lazy="selectin")
    business_profile: Mapped["BusinessProfile | None"] = relationship(
        "BusinessProfile",
        lazy="selectin",
    )
    fields: Mapped[list["DocumentField"]] = relationship(
        "DocumentField",
        back_populates="extraction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    review_items: Mapped[list["DocumentReviewItem"]] = relationship(
        "DocumentReviewItem",
        back_populates="extraction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DocumentExtraction(id={self.id}, document_id={self.document_id}, provider={self.provider})>"


class DocumentField(Base):
    """Individual extracted and normalized field from a document.

    Stores both raw extracted value and normalized value with provenance.
    """

    __tablename__ = "document_fields"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_extractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    raw_value: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    normalized_value: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    page_reference: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    location: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    format_valid: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        default="unverified",
        nullable=False,
    )
    provenance: Mapped[str] = mapped_column(
        String(50),
        default="unknown",
        nullable=False,
    )
    applied_to_profile: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    applied_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    # Relationships
    extraction: Mapped["DocumentExtraction"] = relationship(
        "DocumentExtraction",
        back_populates="fields",
        lazy="selectin",
    )
    reviewer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[applied_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DocumentField(id={self.id}, field_type={self.field_type}, verification={self.verification_status})>"


class DocumentReviewItem(Base):
    """Review item for conflicts between extracted data and profile.

    Tracks conflicts that need user resolution.
    """

    __tablename__ = "document_review_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_extractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    existing_value: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    extracted_value: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    normalized_value: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    conflict_reason: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        default="medium",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )
    resolution: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    resolved_value: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    # Relationships
    extraction: Mapped["DocumentExtraction"] = relationship(
        "DocumentExtraction",
        back_populates="review_items",
        lazy="selectin",
    )
    document: Mapped["UploadedDocument"] = relationship(
        "UploadedDocument",
        lazy="selectin",
    )
    business_profile: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile",
        lazy="selectin",
    )
    resolver: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[resolved_by],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DocumentReviewItem(id={self.id}, field_type={self.field_type}, status={self.status})>"


class DocumentAuditEvent(Base):
    """Audit log for document intelligence operations.

    Immutable audit trail for compliance and debugging.
    """

    __tablename__ = "document_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    extraction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_extractions.id", ondelete="SET NULL"),
        nullable=True,
    )
    field_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    old_value: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    new_value: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    provenance: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    event_metadata: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    document: Mapped["UploadedDocument"] = relationship(
        "UploadedDocument",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User", lazy="selectin")
    business_profile: Mapped["BusinessProfile | None"] = relationship(
        "BusinessProfile",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DocumentAuditEvent(id={self.id}, event_type={self.event_type}, document_id={self.document_id})>"