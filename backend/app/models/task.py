"""RoadmapTask model."""
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.roadmap import Roadmap


class RoadmapTask(Base):
    """Individual task within a roadmap."""

    __tablename__ = "roadmap_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    official_portal_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    required_documents: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    source_references: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
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
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<RoadmapTask(id={self.id}, title={self.title}, status={self.status}, sequence={self.sequence_number})>"
