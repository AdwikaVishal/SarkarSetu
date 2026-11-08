"""Roadmap generator for personalized action plans.

Converts workflow outputs, eligibility assessments, and document intelligence
into structured, personalized roadmaps.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.services.document_intelligence.schemas import (
    DocumentVerificationStatus,
)
from app.services.roadmap.schemas import (
    EvidenceReference,
    RoadmapGenerationContext,
    RoadmapGenerationResult,
    RoadmapTaskDefinition,
    TaskCategory,
    TaskPriority,
)


class RoadmapGenerator:
    """Generates personalized roadmaps from business context.

    Takes workflow outputs, eligibility assessments, document intelligence,
    and business profile data to create actionable, evidence-backed roadmaps.
    """

    def __init__(self) -> None:
        pass

    async def generate(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate roadmap tasks from context.

        Args:
            context: All relevant business and workflow context.

        Returns:
            List of task definitions for the roadmap.
        """
        tasks = []

        # 1. Information collection tasks from missing information
        tasks.extend(self._generate_information_tasks(context))

        # 2. Document verification tasks
        tasks.extend(self._generate_document_tasks(context))

        # 3. Eligibility-aware tasks
        tasks.extend(self._generate_eligibility_tasks(context))

        # 3. Workflow-specific next-step tasks
        tasks.extend(self._generate_workflow_tasks(context))

        # 4. Evidence review tasks
        tasks.extend(self._generate_evidence_review_tasks(context))

        # Sort by priority and dependencies
        return self._sort_tasks(tasks, context)

    # ------------------------------------------------------------------
    # Task Generation Methods
    # ------------------------------------------------------------------

    def _generate_information_tasks(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate tasks for missing business information."""
        tasks: list[RoadmapTaskDefinition] = []

        for info in context.missing_information:
            tasks.append(
                RoadmapTaskDefinition(
                    title=f"Provide {info.replace('_', ' ')}",
                    description=(
                        f"This information is required to proceed with "
                        f"{context.service_type or 'the requested service'}."
                    ),
                    category=TaskCategory.PROVIDE_INFORMATION,
                    priority=TaskPriority.HIGH,
                    completion_criteria=f"User provides valid {info}",
                    workflow_step_id="collect_information",
                )
            )

        return tasks

    def _generate_document_tasks(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate tasks from document intelligence status."""
        tasks: list[RoadmapTaskDefinition] = []

        doc_status = context.document_status
        if not doc_status:
            return tasks

        # Documents awaiting user confirmation
        for doc_id, doc_info in doc_status.items():
            fields = doc_info.get("fields", [])
            for field in fields:
                if field.get("verification_status") == DocumentVerificationStatus.USER_CONFIRMED.value:
                    continue

                if field.get("verification_status") == DocumentVerificationStatus.UNVERIFIED.value:
                    tasks.append(
                        RoadmapTaskDefinition(
                            title=f"Confirm extracted {field.get('field_type', 'field')} from document",
                            description=(
                                f"Document {doc_id} contains an extracted "
                                f"{field.get('field_type', 'field')} that needs your confirmation."
                            ),
                            category=TaskCategory.VERIFY_INFORMATION,
                            priority=TaskPriority.HIGH,
                            completion_criteria="User confirms or corrects the extracted value",
                            document_ids=[UUID(doc_id) if isinstance(doc_id, str) else doc_id],
                            evidence_references=[
                                EvidenceReference(
                                    source_id=doc_id,
                                    source_type="document",
                                    description=f"Extracted {field.get('field_type', 'field')} from uploaded document",
                                    retrieved_at=datetime.now(UTC),
                                )
                            ],
                        )
                    )

            # Documents with conflicts
            conflicts = doc_info.get("conflicts", [])
            for conflict in conflicts:
                tasks.append(
                    RoadmapTaskDefinition(
                        title=f"Resolve {conflict.get('field_type', 'field')} conflict",
                        description=(
                            f"Document {doc_id} has a {conflict.get('field_type', 'field')} "
                            f"({conflict.get('extracted_value', 'extracted')}) that conflicts "
                            f"with your profile ({conflict.get('existing_value', 'existing')})."
                        ),
                        category=TaskCategory.VERIFY_INFORMATION,
                        priority=TaskPriority.CRITICAL,
                        completion_criteria="User resolves the conflict by accepting extracted, keeping existing, or providing manual value",
                        document_ids=[UUID(doc_id) if isinstance(doc_id, str) else doc_id],
                        evidence_references=[
                            EvidenceReference(
                                source_id=doc_id,
                                source_type="document",
                                description=f"Conflict in {conflict.get('field_type', 'field')}",
                                retrieved_at=datetime.now(UTC),
                            )
                        ],
                    )
                )

        return tasks

    def _generate_eligibility_tasks(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate tasks based on eligibility assessment status."""
        tasks: list[RoadmapTaskDefinition] = []

        if not context.eligibility_assessment_id:
            return tasks

        # We don't have the actual assessment here, but we can generate
        # generic tasks based on the service type and context
        service_type = context.service_type or ""

        if "udyam" in service_type:
            tasks.extend(self._udyam_eligibility_tasks(context))
        elif "gst" in service_type:
            tasks.extend(self._gst_eligibility_tasks(context))
        elif "msme" in service_type or "scheme" in service_type:
            tasks.extend(self._scheme_eligibility_tasks(context))

        return tasks

    def _udyam_eligibility_tasks(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate Udyam-specific eligibility tasks."""
        tasks = []

        # Udyam registration requires specific info
        required = ["pan", "aadhaar", "business_name", "business_type", "state", "district"]
        for req in required:
            if req in context.missing_information:
                tasks.append(
                    RoadmapTaskDefinition(
                        title=f"Provide {req.replace('_', ' ')} for Udyam registration",
                        description=f"Udyam registration requires your {req.replace('_', ' ')}.",
                        category=TaskCategory.PROVIDE_INFORMATION,
                        priority=TaskPriority.HIGH,
                        completion_criteria=f"Valid {req} provided",
                        workflow_step_id="udyam_prerequisites",
                    )
                )

        return tasks

    def _gst_eligibility_tasks(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate GST-specific eligibility tasks."""
        tasks = []

        # GST registration typically needs PAN, business proof, address proof
        required = ["pan", "business_address", "business_proof"]
        for req in required:
            if req in context.missing_information:
                tasks.append(
                    RoadmapTaskDefinition(
                        title=f"Provide {req.replace('_', ' ')} for GST registration",
                        description=f"GST registration requires {req.replace('_', ' ')}.",
                        category=TaskCategory.PROVIDE_INFORMATION,
                        priority=TaskPriority.HIGH,
                        completion_criteria=f"Valid {req} provided",
                        workflow_step_id="gst_prerequisites",
                    )
                )

        return tasks

    def _scheme_eligibility_tasks(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate scheme eligibility tasks."""
        tasks = []

        # Schemes often need business size, location, industry
        required = ["annual_turnover", "employee_count", "industry"]
        for req in required:
            if req in context.missing_information:
                tasks.append(
                    RoadmapTaskDefinition(
                        title=f"Provide {req.replace('_', ' ')} for scheme eligibility",
                        description=f"Scheme eligibility assessment needs your {req.replace('_', ' ')}.",
                        category=TaskCategory.PROVIDE_INFORMATION,
                        priority=TaskPriority.MEDIUM,
                        completion_criteria=f"Valid {req} provided",
                        workflow_step_id="scheme_prerequisites",
                    )
                )

        return tasks

    def _generate_workflow_tasks(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate next-step tasks based on workflow state."""
        tasks = []

        service_type = context.service_type or ""

        if "udyam_registration" in service_type:
            tasks.append(
                RoadmapTaskDefinition(
                    title="Review official Udyam registration requirements",
                    description="Review the official Udyam registration portal requirements before proceeding.",
                    category=TaskCategory.REVIEW_REQUIREMENT,
                    priority=TaskPriority.HIGH,
                    completion_criteria="Requirements reviewed on official portal",
                    official_portal_url="https://udyamregistration.gov.in",
                    evidence_references=[
                        EvidenceReference(
                            source_id="udyam_official",
                            source_type="government_source",
                            description="Official Udyam registration requirements",
                            retrieved_at=datetime.now(UTC),
                        )
                    ],
                )
            )

            tasks.append(
                RoadmapTaskDefinition(
                    title="Complete Udyam registration on official portal",
                    description="Complete the Udyam registration form on the official government portal.",
                    category=TaskCategory.VISIT_OFFICIAL_PORTAL,
                    priority=TaskPriority.HIGH,
                    completion_criteria="Registration submitted on udyamregistration.gov.in",
                    official_portal_url="https://udyamregistration.gov.in",
                    workflow_step_id="udyam_submit",
                )
            )

        elif "gst_registration" in service_type:
            tasks.append(
                RoadmapTaskDefinition(
                    title="Review official GST registration requirements",
                    description="Review the official GST portal requirements before proceeding.",
                    category=TaskCategory.REVIEW_REQUIREMENT,
                    priority=TaskPriority.HIGH,
                    completion_criteria="Requirements reviewed on official portal",
                    official_portal_url="https://www.gst.gov.in",
                    evidence_references=[
                        EvidenceReference(
                            source_id="gst_official",
                            source_type="government_source",
                            description="Official GST registration requirements",
                            retrieved_at=datetime.now(UTC),
                        )
                    ],
                )
            )

            tasks.append(
                RoadmapTaskDefinition(
                    title="Complete GST registration on official portal",
                    description="Complete the GST registration form on the official government portal.",
                    category=TaskCategory.VISIT_OFFICIAL_PORTAL,
                    priority=TaskPriority.HIGH,
                    completion_criteria="Registration submitted on gst.gov.in",
                    official_portal_url="https://www.gst.gov.in",
                    workflow_step_id="gst_submit",
                )
            )

        elif "msme" in service_type or "scheme" in service_type:
            tasks.append(
                RoadmapTaskDefinition(
                    title="Review applicable MSME schemes on official portal",
                    description="Review available MSME schemes and their requirements on the official portal.",
                    category=TaskCategory.REVIEW_REQUIREMENT,
                    priority=TaskPriority.HIGH,
                    completion_criteria="Schemes reviewed on official portal",
                    official_portal_url="https://www.msme.gov.in",
                    evidence_references=[
                        EvidenceReference(
                            source_id="msme_official",
                            source_type="government_source",
                            description="Official MSME schemes listing",
                            retrieved_at=datetime.now(UTC),
                        )
                    ],
                )
            )

        return tasks

    def _generate_evidence_review_tasks(
        self,
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Generate tasks to review supporting evidence."""
        tasks = []

        for evidence in context.evidence_references:
            if evidence.source_type == "government_source":
                tasks.append(
                    RoadmapTaskDefinition(
                        title=f"Review {evidence.description}",
                        description=f"Review the official guidance from {evidence.source_id} to understand requirements.",
                        category=TaskCategory.REVIEW_REQUIREMENT,
                        priority=TaskPriority.MEDIUM,
                        completion_criteria="Evidence reviewed and understood",
                        evidence_references=[evidence],
                    )
                )

        return tasks

    # ------------------------------------------------------------------
    # Task Sorting and Dependency Resolution
    # ------------------------------------------------------------------

    def _sort_tasks(
        self,
        tasks: list[RoadmapTaskDefinition],
        context: RoadmapGenerationContext,
    ) -> list[RoadmapTaskDefinition]:
        """Sort tasks by priority and logical order.

        Priority order:
        1. CRITICAL (conflicts, mandatory info)
        2. HIGH (required for workflow, eligibility)
        3. MEDIUM (evidence review, optional info)
        4. LOW (follow-up, supplementary)
        """
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }

        return sorted(tasks, key=lambda t: priority_order.get(t.priority, 99))

    async def generate_roadmap(
        self,
        context: RoadmapGenerationContext,
    ) -> RoadmapGenerationResult:
        """Generate a complete roadmap.

        Args:
            context: Generation context.

        Returns:
            RoadmapGenerationResult with tasks and metadata.
        """
        tasks = await self.generate(context)

        return RoadmapGenerationResult(
            roadmap_id=uuid4(),
            version=1,
            tasks_created=len(tasks),
            tasks_updated=0,
            tasks_preserved=0,
            tasks_archived=0,
            warnings=[],
        )
