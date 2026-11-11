"""UploadedDocument model."""
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.business import BusinessProfile
    from app.models.document_intelligence import DocumentExtraction
    from app.models.user import User


class UploadedDocument(Base):
    """Uploaded document metadata model."""

    __tablename__ = "uploaded_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
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
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extracted_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="uploaded_documents")
    business_profile: Mapped["BusinessProfile | None"] = relationship(
        "BusinessProfile",
        back_populates="uploaded_documents",
    )
    extraction: Mapped["DocumentExtraction | None"] = relationship(
        "DocumentExtraction",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<UploadedDocument(id={self.id}, filename={self.original_filename}, status={self.processing_status})>"
