"""Evidence mapper for roadmap engine.

Maps evidence from various sources to roadmap tasks and maintains
traceability from tasks back to official sources.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.services.roadmap.schemas import EvidenceReference


class EvidenceMapper:
    """Maps and manages evidence references for roadmap tasks.

    Supports evidence from:
    - GovernmentKnowledgeProvider (official documents)
    - EligibilityAssessmentService (assessment results)
    - DocumentIntelligenceService (extracted documents)
    - WorkflowEngine (workflow step results)
    """

    def __init__(self) -> None:
        pass

    def create_government_source_evidence(
        self,
        document_id: str,
        source_title: str,
        issuing_authority: str,
        source_url: str | None = None,
        relevant_excerpt: str | None = None,
        page_or_section: str | None = None,
        description: str | None = None,
    ) -> EvidenceReference:
        """Create evidence reference from a government document."""
        return EvidenceReference(
            source_id=document_id,
            source_type="government_source",
            description=description or f"Official guidance from {issuing_authority}: {source_title}",
            retrieved_at=datetime.now(UTC),
        )

    def create_eligibility_evidence(
        self,
        assessment_id: str,
        scheme_name: str,
        assessment_status: str,
        rule_set_version: str,
        description: str | None = None,
    ) -> EvidenceReference:
        """Create evidence reference from an eligibility assessment."""
        return EvidenceReference(
            source_id=assessment_id,
            source_type="eligibility_assessment",
            description=description or f"Eligibility assessment for {scheme_name}: {assessment_status} (rules v{rule_set_version})",
            retrieved_at=datetime.now(UTC),
        )

    def create_document_evidence(
        self,
        document_id: UUID,
        field_type: str,
        verification_status: str,
        raw_value: str,
        normalized_value: str | None = None,
        confidence: float | None = None,
        description: str | None = None,
    ) -> EvidenceReference:
        """Create evidence reference from an uploaded/extracted document."""
        return EvidenceReference(
            source_id=str(document_id),
            source_type="document",
            description=description or f"Extracted {field_type} from uploaded document (status: {verification_status})",
            retrieved_at=datetime.now(UTC),
        )

    def create_workflow_evidence(
        self,
        workflow_execution_id: str,
        step_id: str,
        step_name: str,
        evidence_references: list[EvidenceReference],
    ) -> list[EvidenceReference]:
        """Pass through workflow step evidence references."""
        return evidence_references

    def merge_evidence(
        self,
        *evidence_lists: list[EvidenceReference],
    ) -> list[EvidenceReference]:
        """Merge multiple evidence lists, deduplicating by source_id."""
        seen = set()
        merged = []

        for ev_list in evidence_lists:
            for ev in ev_list:
                key = (ev.source_type, ev.source_id)
                if key not in seen:
                    seen.add(key)
                    merged.append(ev)

        return merged

    def filter_evidence_for_task(
        self,
        evidence: list[EvidenceReference],
        task_keywords: list[str],
    ) -> list[EvidenceReference]:
        """Filter evidence relevant to a task based on keywords."""
        relevant = []
        for ev in evidence:
            for keyword in task_keywords:
                if keyword.lower() in ev.description.lower():
                    relevant.append(ev)
                    break
        return relevant

    def get_evidence_summary(
        self,
        evidence: list[EvidenceReference],
    ) -> dict[str, Any]:
        """Get a summary of evidence by type."""
        summary: dict[str, Any] = {
            "total": len(evidence),
            "by_type": {},
            "by_source": {},
        }

        for ev in evidence:
            summary["by_type"][ev.source_type] = summary["by_type"].get(ev.source_type, 0) + 1
            source_key = str(ev.source_id)
            summary["by_source"][source_key] = summary["by_source"].get(source_key, 0) + 1

        return summary
