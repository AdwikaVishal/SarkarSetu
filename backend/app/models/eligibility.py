"""EligibilityResult model."""
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.business import BusinessProfile
    from app.models.recommendation import Recommendation
    from app.models.user import User


class EligibilityResult(Base):
    """Eligibility assessment result model."""

    __tablename__ = "eligibility_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule_set_version: Mapped[str] = mapped_column(String(50), nullable=False)
    assessment_status: Mapped[str] = mapped_column(String(50), nullable=False)
    result_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    missing_information: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="eligibility_results")
    business_profile: Mapped["BusinessProfile"] = relationship(
        "BusinessProfile",
        back_populates="eligibility_results",
    )
    recommendation: Mapped["Recommendation | None"] = relationship(
        "Recommendation",
        back_populates="eligibility_results",
    )

    def __repr__(self) -> str:
        return f"<EligibilityResult(id={self.id}, rule_set_version={self.rule_set_version}, status={self.assessment_status})>"
