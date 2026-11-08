"""Document Intelligence service.

Main service orchestrating document extraction integration, business profile
updates, conflict resolution, and eligibility/workflow integration.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BusinessProfile, UploadedDocument
from app.services.document_intelligence.document_errors import (
    BusinessProfileMismatchError,
    ConflictResolutionError,
    DocumentNotFoundError,
    DuplicateExtractionError,
    ExtractionValidationError,
    VerificationError,
)
from app.services.document_intelligence.field_mapper import FieldMapper
from app.services.document_intelligence.normalizer import normalize_extraction_result
from app.services.document_intelligence.provenance import (
    AuditEvent,
    AuditEventType,
    DataProvenance,
    DocumentVerificationLifecycle,
    DocumentVerificationService,
    ProvenanceTracker,
)
from app.services.document_intelligence.schemas import (
    DocumentCategory,
    DocumentExtractionResult,
    ExtractionProviderPayload,
    FieldConflict,
    NormalizedField,
)
from app.services.document_intelligence.validation import (
    ExtractionValidator,
)
from app.services.eligibility_engine.engine import EligibilityEngine
from app.services.ownership import OwnershipService, ResourceNotFoundError
from app.services.workflows.engine import WorkflowEngine
from app.services.workflows.state_manager import WorkflowStateManager

logger = logging.getLogger(__name__)


class DocumentIntelligenceService:
    """Main service for document intelligence integration."""

    def __init__(
        self,
        db: AsyncSession,
        eligibility_engine: EligibilityEngine | None = None,
        workflow_engine: WorkflowEngine | None = None,
        ownership_service: OwnershipService | None = None,
    ) -> None:
        self.db = db
        self.eligibility_engine = eligibility_engine
        self.workflow_engine = workflow_engine
        self.ownership = ownership_service or OwnershipService(db)

        self.field_mapper = FieldMapper()
        self.validator = ExtractionValidator()
        self.provenance_tracker = ProvenanceTracker()
        self.verification_service = DocumentVerificationService()

    # ------------------------------------------------------------------
    # Extraction Result Processing
    # ------------------------------------------------------------------

    async def process_extraction_result(
        self,
        payload: ExtractionProviderPayload,
        user_id: UUID,
    ) -> tuple[DocumentExtractionResult, list[FieldConflict]]:
        """Process an extraction result from an external provider.

        This is the main entry point for receiving extracted document data.

        Args:
            payload: Validated extraction provider payload.
            user_id: Authenticated user ID.

        Returns:
            Tuple of (processed result, detected conflicts).

        Raises:
            DocumentNotFoundError: If document doesn't exist.
            DocumentAccessForbiddenError: If user doesn't own document.
            BusinessProfileMismatchError: If business profile mismatch.
            ExtractionValidationError: If payload validation fails.
            DuplicateExtractionError: If extraction already exists.
        """
        # Validate payload
        self._validate_payload(payload)

        # Get and validate document ownership
        document = await self._get_owned_document(payload.document_id, user_id)

        # Validate business profile if specified
        if payload.result.business_profile_id:
            await self._validate_business_profile(
                payload.result.business_profile_id, user_id
            )
            if document.business_profile_id != payload.result.business_profile_id:
                raise BusinessProfileMismatchError(
                    document_id=payload.document_id,
                    document_business_profile_id=document.business_profile_id,
                    request_business_profile_id=payload.result.business_profile_id,
                )

        # Check for duplicate extraction
        if document.processing_status == "completed" and document.extracted_data:
            raise DuplicateExtractionError(payload.document_id)

        # Normalize extracted fields
        normalized_fields = normalize_extraction_result(payload.result)

        # Update document record
        await self._update_document_with_extraction(
            document, payload.result, normalized_fields
        )

        # Detect conflicts if business profile associated
        conflicts = []
        if document.business_profile_id:
            profile = await self._get_business_profile(document.business_profile_id)
            conflicts = self.field_mapper.detect_conflicts(profile, normalized_fields)

            # Create review items for conflicts
            if conflicts:
                await self._create_review_items(document, profile, conflicts)
                # Update document state to needs_review
                self.verification_service.transition(
                    document.id, DocumentVerificationLifecycle.NEEDS_REVIEW
                )
            else:
                # No conflicts - can proceed to validation
                self.verification_service.transition(
                    document.id, DocumentVerificationLifecycle.VALIDATION_PENDING
                )
        else:
            self.verification_service.transition(
                document.id, DocumentVerificationLifecycle.VALIDATION_PENDING
            )

        await self.db.commit()

        # Log audit event
        self._log_audit_event(
            AuditEvent(
                event_type=AuditEventType.EXTRACTION_RECEIVED,
                document_id=document.id,
                user_id=user_id,
                business_profile_id=document.business_profile_id,
                metadata={
                    "provider": payload.result.provider,
                    "provider_version": payload.result.provider_version,
                    "field_count": len(normalized_fields),
                    "conflict_count": len(conflicts),
                },
            )
        )

        return payload.result, conflicts

    # ------------------------------------------------------------------
    # Business Profile Integration
    # ------------------------------------------------------------------

    async def apply_verified_fields(
        self,
        document_id: UUID,
        user_id: UUID,
        field_types: list[str],
        confirmed: bool = True,
    ) -> BusinessProfile:
        """Apply user-confirmed extracted fields to business profile.

        Args:
            document_id: Document ID.
            user_id: Authenticated user ID.
            field_types: List of field types to apply.
            confirmed: Whether user explicitly confirmed (True) or rejected (False).

        Returns:
            Updated business profile.

        Raises:
            DocumentNotFoundError: If document not found.
            DocumentAccessForbiddenError: If user doesn't own document.
            ProvenanceError: If provenance rules violated.
        """
        document = await self._get_owned_document(document_id, user_id)

        if not document.business_profile_id:
            raise VerificationError(
                "Document is not associated with a business profile",
                context={"document_id": str(document_id)},
            )

        profile = await self._get_business_profile(document.business_profile_id)

        # Verify ownership of business profile
        await self.ownership.get_user_business_profile(user_id, profile.id)

        # Get normalized fields from document
        if not document.extracted_data:
            raise VerificationError("No extracted data available for this document")

        # Re-normalize fields
        from app.services.document_intelligence.schemas import DocumentExtractionResult

        extraction_result = DocumentExtractionResult.model_validate(document.extracted_data)
        normalized_fields = normalize_extraction_result(extraction_result)

        # Filter to requested field types
        requested_types = set(field_types)
        fields_to_process = [
            f for f in normalized_fields if f.field_type.value in requested_types
        ]

        if not fields_to_process:
            return profile

        # Detect conflicts
        conflicts = self.field_mapper.detect_conflicts(profile, fields_to_process)
        conflicted_types = {c.field_type for c in conflicts}

        # Apply non-conflicted fields that user confirmed
        applied_fields = []
        for field in fields_to_process:
            if field.field_type in conflicted_types:
                # Conflicted fields need explicit resolution
                continue

            if not self.field_mapper.is_supported_for_update(field.field_type):
                continue

            if not field.format_valid:
                logger.warning(
                    f"Skipping field {field.field_type} due to invalid format"
                )
                continue

            # Apply the field
            await self._apply_field_to_profile(profile, field, confirmed)
            applied_fields.append(field)

            # Upgrade provenance
            self.provenance_tracker.upgrade_provenance(
                field.field_type.value, DataProvenance.USER_CONFIRMED, "user_confirmed"
            )

            # Log audit event
            self._log_audit_event(
                AuditEvent(
                    event_type=AuditEventType.PROFILE_UPDATED,
                    document_id=document_id,
                    user_id=user_id,
                    business_profile_id=profile.id,
                    field_type=field.field_type.value,
                    new_value=field.value,
                    provenance=DataProvenance.USER_CONFIRMED,
                    reason="user_confirmed" if confirmed else "user_rejected",
                )
            )

        await self.db.commit()
        await self.db.refresh(profile)

        # If all fields applied and no conflicts, verify document
        if not conflicts and applied_fields:
            self.verification_service.transition(
                document.id, DocumentVerificationLifecycle.VERIFIED
            )
            await self.db.commit()

        # Trigger eligibility re-assessment if profile changed
        if applied_fields and self.eligibility_engine:
            await self._trigger_eligibility_reassessment(profile, user_id)

        return profile

    async def resolve_conflict(
        self,
        document_id: UUID,
        user_id: UUID,
        field_type: str,
        resolution: str,  # "accept_extracted", "keep_existing", "manual_value"
        manual_value: str | None = None,
    ) -> BusinessProfile:
        """Resolve a field conflict.

        Args:
            document_id: Document ID.
            user_id: Authenticated user ID.
            field_type: Field type to resolve.
            resolution: Resolution type.
            manual_value: Manual value if resolution is "manual_value".

        Returns:
            Updated business profile.

        Raises:
            ConflictResolutionError: If resolution fails.
        """
        document = await self._get_owned_document(document_id, user_id)

        if not document.business_profile_id:
            raise ConflictResolutionError(
                "Document not associated with business profile",
                context={"document_id": str(document_id)},
            )

        profile = await self._get_business_profile(document.business_profile_id)
        await self.ownership.get_user_business_profile(user_id, profile.id)

        # Get the conflict
        if not document.extracted_data:
            raise ConflictResolutionError("No extracted data available")

        from app.services.document_intelligence.schemas import DocumentExtractionResult

        extraction_result = DocumentExtractionResult.model_validate(document.extracted_data)
        normalized_fields = normalize_extraction_result(extraction_result)
        conflicts = self.field_mapper.detect_conflicts(profile, normalized_fields)

        target_conflict = next(
            (c for c in conflicts if c.field_type.value == field_type), None
        )

        if not target_conflict:
            raise ConflictResolutionError(
                f"No conflict found for field {field_type}",
                context={"field_type": field_type},
            )

        # Apply resolution
        if resolution == "accept_extracted":
            # Find the extracted field
            field = next(
                (f for f in normalized_fields if f.field_type.value == field_type), None
            )
            if field:
                await self._apply_field_to_profile(profile, field, True)
        elif resolution == "keep_existing":
            # Do nothing - keep existing value
            pass
        elif resolution == "manual_value" and manual_value:
            # Apply manual value
            from app.services.document_intelligence.schemas import NormalizedField

            manual_field = NormalizedField(
                field_type=target_conflict.field_type,
                value=manual_value,
                confidence=None,
                provenance="USER_CONFIRMED",
                source_document_id=document_id,
                source_field_raw_value=manual_value,
                format_valid=True,
                verified=True,
            )
            await self._apply_field_to_profile(profile, manual_field, True)
        else:
            raise ConflictResolutionError(
                f"Invalid resolution type: {resolution}",
                context={"resolution": resolution},
            )

        # Log audit event
        self._log_audit_event(
            AuditEvent(
                event_type=AuditEventType.CONFLICT_RESOLVED,
                document_id=document_id,
                user_id=user_id,
                business_profile_id=profile.id,
                field_type=field_type,
                old_value=target_conflict.existing_value,
                new_value=manual_value or target_conflict.normalized_value,
                provenance=DataProvenance.USER_CONFIRMED,
                reason=resolution,
            )
        )

        await self.db.commit()
        await self.db.refresh(profile)

        # Trigger eligibility re-assessment
        if self.eligibility_engine:
            await self._trigger_eligibility_reassessment(profile, user_id)

        return profile

    # ------------------------------------------------------------------
    # Eligibility Integration
    # ------------------------------------------------------------------

    async def _trigger_eligibility_reassessment(
        self, profile: BusinessProfile, user_id: UUID
    ) -> None:
        """Trigger eligibility reassessment after profile update.

        This creates a new assessment with document-derived values
        marked with appropriate provenance.
        """
        if not self.eligibility_engine:
            return

        try:
            from app.services.eligibility import EligibilityAssessmentRequest

            # Build business attributes from profile
            business_attributes = self._build_business_attributes(profile)

            # Determine which schemes to reassess based on updated fields
            # For now, trigger for all relevant schemes
            schemes = ["udyam_registration", "gst_registration"]

            for scheme in schemes:
                request = EligibilityAssessmentRequest(
                    user_id=user_id,
                    business_profile_id=profile.id,
                    scheme_name=scheme,
                    registration_type=scheme,
                    business_attributes=business_attributes,
                    missing_information=[],
                    context={
                        "trigger": "document_update",
                        "profile_id": str(profile.id),
                    },
                )

                try:
                    result = await self.eligibility_engine.evaluate(request)
                    logger.info(
                        f"Eligibility reassessment triggered for {scheme}: {result.assessment_status}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Eligibility reassessment failed for {scheme}: {e}"
                    )
        except Exception as e:
            logger.warning(f"Failed to trigger eligibility reassessment: {e}")

    def _build_business_attributes(self, profile: BusinessProfile) -> dict[str, Any]:
        """Build business attributes dictionary from profile."""
        attrs = {
            "business_name": profile.business_name,
            "business_type": profile.business_type,
            "industry": profile.industry,
            "state": profile.state,
            "district": profile.district,
            "business_structure": profile.business_structure,
            "business_stage": profile.business_stage,
            "sales_channels": profile.sales_channels,
        }

        if profile.annual_turnover is not None:
            attrs["annual_turnover"] = str(profile.annual_turnover)
        if profile.employee_count is not None:
            attrs["employee_count"] = str(profile.employee_count)
        if profile.city:
            attrs["city"] = profile.city
        if profile.pincode:
            attrs["pincode"] = profile.pincode
        if profile.udyam_number:
            attrs["udyam_number"] = profile.udyam_number
        if profile.gstin:
            attrs["gstin"] = profile.gstin
        if profile.date_of_establishment:
            attrs["establishment_date"] = profile.date_of_establishment.isoformat()
        if profile.products_services:
            attrs["products_services"] = profile.products_services
        if profile.operating_mode:
            attrs["operating_mode"] = profile.operating_mode

        return attrs

    # ------------------------------------------------------------------
    # Workflow Integration
    # ------------------------------------------------------------------

    async def get_workflow_document_status(
        self,
        workflow_id: str,
        user_id: UUID,
    ) -> dict[str, Any]:
        """Get document status for a workflow execution.

        Used by workflows to identify available documents and missing info.

        Args:
            workflow_id: Workflow execution ID.
            user_id: Authenticated user ID.

        Returns:
            Dictionary with document status information.
        """
        # Get workflow execution
        state_manager = WorkflowStateManager(self.db)
        execution = await state_manager.get_workflow_execution(workflow_id, user_id)

        if not execution:
            return {"error": "Workflow not found"}

        if not execution.business_profile_id:
            return {"documents": [], "message": "No business profile associated"}

        # Get all documents for this business profile
        documents = await self.get_documents_for_business(
            execution.business_profile_id, user_id
        )

        # Categorize by workflow relevance
        workflow_docs = self._categorize_documents_for_workflow(
            documents, execution.service_type
        )

        return {
            "workflow_id": workflow_id,
            "service_type": execution.service_type,
            "documents": workflow_docs,
            "missing_documents": self._identify_missing_documents(
                execution.service_type, workflow_docs
            ),
        }

    def _categorize_documents_for_workflow(
        self, documents: list[UploadedDocument], service_type: str
    ) -> list[dict[str, Any]]:
        """Categorize documents by relevance to workflow."""
        relevant_categories = {
            "udyam_registration": [DocumentCategory.UDYAM, DocumentCategory.PAN, DocumentCategory.AADHAAR],
            "gst_registration": [DocumentCategory.GST, DocumentCategory.PAN, DocumentCategory.BUSINESS_REGISTRATION],
            "msme_schemes": [DocumentCategory.UDYAM, DocumentCategory.BUSINESS_REGISTRATION, DocumentCategory.BANK],
        }

        categories = relevant_categories.get(service_type, [])
        categorized = []

        for doc in documents:
            if doc.document_type and doc.document_type in [c.value for c in categories]:
                categorized.append({
                    "document_id": str(doc.id),
                    "filename": doc.original_filename,
                    "document_type": doc.document_type,
                    "processing_status": doc.processing_status,
                    "verification_state": self.verification_service.get_state(doc.id).value,
                    "extracted_fields": list(doc.extracted_data.get("extracted_fields", {}).keys()) if doc.extracted_data else [],
                })

        return categorized

    def _identify_missing_documents(
        self, service_type: str, available_docs: list[dict[str, Any]]
    ) -> list[str]:
        """Identify which document categories are missing for a workflow."""
        required_categories = {
            "udyam_registration": ["udyam", "pan"],
            "gst_registration": ["gst", "pan"],
            "msme_schemes": ["udyam", "business_registration"],
        }

        required = required_categories.get(service_type, [])
        available_types = {d["document_type"] for d in available_docs}

        return [c for c in required if c not in available_types]

    # ------------------------------------------------------------------
    # Document Query Methods
    # ------------------------------------------------------------------

    async def get_document(
        self, document_id: UUID, user_id: UUID
    ) -> UploadedDocument:
        """Get a document by ID with ownership validation."""
        return await self._get_owned_document(document_id, user_id)

    async def get_documents_for_business(
        self, business_profile_id: UUID, user_id: UUID
    ) -> list[UploadedDocument]:
        """Get all documents for a business profile."""
        # Validate business profile ownership
        await self.ownership.get_user_business_profile(user_id, business_profile_id)

        result = await self.db.execute(
            select(UploadedDocument).where(
                UploadedDocument.business_profile_id == business_profile_id
            ).order_by(UploadedDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_review_items(
        self, document_id: UUID, user_id: UUID
    ) -> list[dict[str, Any]]:
        """Get review items (conflicts) for a document."""
        document = await self._get_owned_document(document_id, user_id)

        # In a full implementation, this would query a review_items table
        # For now, re-detect conflicts
        if not document.business_profile_id or not document.extracted_data:
            return []

        profile = await self._get_business_profile(document.business_profile_id)
        from app.services.document_intelligence.schemas import DocumentExtractionResult

        extraction_result = DocumentExtractionResult.model_validate(document.extracted_data)
        normalized_fields = normalize_extraction_result(extraction_result)
        conflicts = self.field_mapper.detect_conflicts(profile, normalized_fields)

        return [
            {
                "field_type": c.field_type.value,
                "existing_value": c.existing_value,
                "extracted_value": c.extracted_value,
                "normalized_value": c.normalized_value,
                "confidence": c.confidence,
                "conflict_reason": c.conflict_reason,
                "severity": c.severity,
                "document_id": str(c.source_document_id),
            }
            for c in conflicts
        ]

    # ------------------------------------------------------------------
    # Private Helper Methods
    # ------------------------------------------------------------------

    def _validate_payload(self, payload: ExtractionProviderPayload) -> None:
        """Validate extraction payload."""
        errors = self.validator.validate_payload(payload)
        if errors:
            raise ExtractionValidationError(
                f"Payload validation failed: {'; '.join(errors)}",
                context={"errors": errors},
            )

    async def _get_owned_document(
        self, document_id: UUID, user_id: UUID
    ) -> UploadedDocument:
        """Get document and validate ownership."""
        result = await self.db.execute(
            select(UploadedDocument).where(
                UploadedDocument.id == document_id,
                UploadedDocument.user_id == user_id,
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise DocumentNotFoundError(document_id)
        return document

    async def _validate_business_profile(
        self, business_profile_id: UUID, user_id: UUID
    ) -> BusinessProfile:
        """Validate business profile ownership."""
        return await self.ownership.get_user_business_profile(user_id, business_profile_id)

    async def _get_business_profile(
        self, business_profile_id: UUID
    ) -> BusinessProfile:
        """Get business profile by ID."""
        result = await self.db.execute(
            select(BusinessProfile).where(BusinessProfile.id == business_profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ResourceNotFoundError("Business profile not found")
        return profile

    async def _update_document_with_extraction(
        self,
        document: UploadedDocument,
        extraction_result: DocumentExtractionResult,
        normalized_fields: list[NormalizedField],
    ) -> None:
        """Update document record with extraction results."""
        document.processing_status = "completed"
        document.document_type = extraction_result.document_category.value
        document.extracted_data = {
            "extraction_result": extraction_result.model_dump(),
            "normalized_fields": [
                {
                    "field_type": f.field_type.value,
                    "value": f.value,
                    "confidence": f.confidence,
                    "provenance": f.provenance,
                    "source_document_id": str(f.source_document_id),
                    "format_valid": f.format_valid,
                    "verified": f.verified,
                }
                for f in normalized_fields
            ],
            "extraction_timestamp": extraction_result.extraction_timestamp.isoformat(),
            "provider": extraction_result.provider,
            "provider_version": extraction_result.provider_version,
        }
        self.db.add(document)

    async def _apply_field_to_profile(
        self,
        profile: BusinessProfile,
        field: NormalizedField,
        confirmed: bool,
    ) -> None:
        """Apply a single field to business profile."""
        updates = self.field_mapper.prepare_profile_updates(profile, [field])

        for attr, value in updates.items():
            setattr(profile, attr, value)

        profile.updated_at = datetime.now(UTC)
        self.db.add(profile)

    async def _create_review_items(
        self,
        document: UploadedDocument,
        profile: BusinessProfile,
        conflicts: list[FieldConflict],
    ) -> None:
        """Create review items for detected conflicts.

        Args:
            document: The uploaded document.
            profile: The business profile.
            conflicts: List of detected conflicts.
        """
        # In a full implementation, this would create DocumentReviewItem records
        # For now, we log the conflicts and store them in the document's extracted_data
        if not document.extracted_data:
            document.extracted_data = {}

        document.extracted_data["review_items"] = [
            {
                "field_type": c.field_type.value,
                "existing_value": c.existing_value,
                "extracted_value": c.extracted_value,
                "normalized_value": c.normalized_value,
                "confidence": c.confidence,
                "conflict_reason": c.conflict_reason,
                "severity": c.severity,
                "status": "pending",
            }
            for c in conflicts
        ]

    def _log_audit_event(self, event: AuditEvent) -> None:
        """Log audit event (in production, would persist to audit table)."""
        logger.info(
            "Document intelligence audit event",
            extra={
                "event_type": event.event_type.value,
                "document_id": str(event.document_id),
                "user_id": str(event.user_id),
                "business_profile_id": str(event.business_profile_id)
                if event.business_profile_id
                else None,
                "field_type": event.field_type,
                "provenance": event.provenance.value if event.provenance else None,
                "reason": event.reason,
                "metadata": event.metadata,
            },
        )
