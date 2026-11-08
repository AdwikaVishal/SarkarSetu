"""Government source research report.

Documents which sources were collected, which could not be accessed,
which require manual verification, key extracted information, and
known limitations. No dates or facts are fabricated.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from rag.config.logging_config import get_logger

logger = get_logger("research_report")


class SourceCollectionEntry(BaseModel):
    source_id: str
    title: str
    authority: str
    source_url: str
    status: str  # collected / failed / manual_verification / unverified
    notes: str | None = None


class ResearchReport(BaseModel):
    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    sources_collected: list[SourceCollectionEntry] = Field(default_factory=list)
    sources_failed: list[SourceCollectionEntry] = Field(default_factory=list)
    sources_manual_verification: list[SourceCollectionEntry] = Field(
        default_factory=list
    )
    important_extracted_information: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        lines = ["# Government Source Research Report", ""]
        lines.append(f"Generated at: {self.generated_at}")
        lines.append("")
        lines.append(f"## Sources Collected ({len(self.sources_collected)})")
        for entry in self.sources_collected:
            lines.append(
                f"- [{entry.source_id}] {entry.title} — {entry.authority} ({entry.source_url})"
            )
            if entry.notes:
                lines.append(f"  - {entry.notes}")
        lines.append("")
        lines.append(f"## Sources Failed to Access ({len(self.sources_failed)})")
        for entry in self.sources_failed:
            lines.append(
                f"- [{entry.source_id}] {entry.title} — {entry.source_url}: {entry.notes or 'access failed'}"
            )
        lines.append("")
        lines.append(
            f"## Sources Requiring Manual Verification ({len(self.sources_manual_verification)})"
        )
        for entry in self.sources_manual_verification:
            lines.append(
                f"- [{entry.source_id}] {entry.title}: {entry.notes or 'verification needed'}"
            )
        lines.append("")
        lines.append("## Important Extracted Information")
        for item in self.important_extracted_information:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("## Known Limitations")
        for item in self.known_limitations:
            lines.append(f"- {item}")
        return "\n".join(lines)

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(), encoding="utf-8")
        logger.info("Research report saved to %s", path)


def build_report_from_registry(
    collected: list[dict[str, Any]],
    failed: list[dict[str, Any]],
    manual: list[dict[str, Any]],
    extracted_info: list[str] | None = None,
    limitations: list[str] | None = None,
) -> ResearchReport:
    return ResearchReport(
        sources_collected=[
            SourceCollectionEntry(**item) for item in collected
        ],
        sources_failed=[SourceCollectionEntry(**item) for item in failed],
        sources_manual_verification=[
            SourceCollectionEntry(**item) for item in manual
        ],
        important_extracted_information=extracted_info or [],
        known_limitations=limitations or [],
    )
