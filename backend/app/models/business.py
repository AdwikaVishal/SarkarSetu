"""BusinessProfile model."""
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.document import UploadedDocument
    from app.models.eligibility import EligibilityResult
    from app.models.recommendation import Recommendation
    from app.models.roadmap import Roadmap
    from app.models.user import User


class BusinessProfile(Base):
    """Business profile model for entrepreneurs."""

    __tablename__ = "business_profiles"

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
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    annual_turnover: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=True,
    )
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sales_channels: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    business_structure: Mapped[str] = mapped_column(String(100), nullable=False)
    business_stage: Mapped[str] = mapped_column(String(100), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    # Additional business information
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    udyam_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    woman_owned: Mapped[bool] = mapped_column(default=False, nullable=False)
    social_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    products_services: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    operating_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_establishment: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships - preserve historical data on business profile deletion
    user: Mapped["User"] = relationship("User", back_populates="business_profiles")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="business_profile",
        cascade="save-update, merge",
        lazy="selectin",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="business_profile",
        cascade="save-update, merge",
        lazy="selectin",
    )
    eligibility_results: Mapped[list["EligibilityResult"]] = relationship(
        "EligibilityResult",
        back_populates="business_profile",
        cascade="save-update, merge",
        lazy="selectin",
    )
    roadmaps: Mapped[list["Roadmap"]] = relationship(
        "Roadmap",
        back_populates="business_profile",
        cascade="save-update, merge",
        lazy="selectin",
    )
    uploaded_documents: Mapped[list["UploadedDocument"]] = relationship(
        "UploadedDocument",
        back_populates="business_profile",
        cascade="save-update, merge",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "annual_turnover IS NULL OR annual_turnover >= 0",
            name="ck_business_profiles_annual_turnover_non_negative",
        ),
        CheckConstraint(
            "employee_count IS NULL OR employee_count >= 0",
            name="ck_business_profiles_employee_count_non_negative",
        ),
    )

    def __repr__(self) -> str:
        return f"<BusinessProfile(id={self.id}, business_name={self.business_name}, user_id={self.user_id}, deleted={self.is_deleted})>"
