"""Recommendation model."""
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.business import BusinessProfile
    from app.models.eligibility import EligibilityResult
    from app.models.user import User


class Recommendation(Base):
    """AI-generated recommendation model."""

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    business_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("business_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )
    eligibility_status: Mapped[str] = mapped_column(
        String(50),
        default="unverified",
        nullable=False,
    )
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    business_profile: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile",
        back_populates="recommendations",
    )
    eligibility_results: Mapped[list["EligibilityResult"]] = relationship(
        "EligibilityResult",
        back_populates="recommendation",
        cascade="save-update, merge",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, category={self.category}, title={self.title})>"
