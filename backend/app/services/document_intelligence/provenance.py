"""Data provenance and verification lifecycle for document intelligence.

Implements the provenance categories and verification lifecycle states
for document-derived data.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class DataProvenance(StrEnum):
    """Provenance of input data used in workflow evaluation.

    Matches the existing workflow context provenance categories.
    """

    BUSINESS_PROFILE = "BUSINESS_PROFILE"
    USER_CONFIRMED = "USER_CONFIRMED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    UNKNOWN = "UNKNOWN"


class DocumentVerificationLifecycle(StrEnum):
    """Document verification lifecycle states.

    RECEIVED -> EXTRACTION_PENDING -> EXTRACTED -> VALIDATION_PENDING
    -> VERIFIED | REJECTED | NEEDS_REVIEW
    """

    RECEIVED = "received"
    EXTRACTION_PENDING = "extraction_pending"
    EXTRACTED = "extracted"
    VALIDATION_PENDING = "validation_pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class FieldVerificationStatus(StrEnum):
    """Verification status of individual extracted fields."""

    UNVERIFIED = "unverified"
    USER_CONFIRMED = "user_confirmed"
    DOCUMENT_VERIFIED = "document_verified"
    REJECTED = "rejected"


class VerificationPolicy:
    """Policy for determining when a field can be marked as verified."""

    # Minimum confidence threshold for auto-verification
    MIN_CONFIDENCE_AUTO_VERIFY = 0.95

    # Fields that require explicit user confirmation regardless of confidence
    REQUIRES_EXPLICIT_CONFIRMATION = {
        "pan",
        "gstin",
        "udyam_number",
        "business_name",
        "establishment_date",
    }

    # Fields that can be auto-verified with high confidence
    AUTO_VERIFIABLE = {
        "pincode",
        "state",
        "city",
        "business_activity",
    }

    @classmethod
    def can_auto_verify(cls, field_type: str, confidence: float | None) -> bool:
        """Check if a field can be automatically verified."""
        if field_type in cls.REQUIRES_EXPLICIT_CONFIRMATION:
            return False
        if field_type in cls.AUTO_VERIFIABLE:
            if confidence is None:
                return False
            return confidence >= cls.MIN_CONFIDENCE_AUTO_VERIFY
        return False

    @classmethod
    def get_required_verification_level(cls, field_type: str) -> str:
        """Get the required verification level for a field type."""
        if field_type in cls.REQUIRES_EXPLICIT_CONFIRMATION:
            return "explicit_user_confirmation"
        if field_type in cls.AUTO_VERIFIABLE:
            return "auto_or_explicit"
        return "explicit_user_confirmation"


class ProvenanceTracker:
    """Tracks provenance for document-derived data."""

    def __init__(self) -> None:
        self._field_provenance: dict[str, DataProvenance] = {}

    def set_provenance(self, field_key: str, provenance: DataProvenance) -> None:
        """Set provenance for a field."""
        self._field_provenance[field_key] = provenance

    def get_provenance(self, field_key: str) -> DataProvenance:
        """Get provenance for a field."""
        return self._field_provenance.get(field_key, DataProvenance.UNKNOWN)

    def can_override(self, field_key: str, new_provenance: DataProvenance) -> bool:
        """Check if a field's provenance can be upgraded.

        Provenance hierarchy (higher can override lower):
        BUSINESS_PROFILE > USER_CONFIRMED > DOCUMENT_VERIFIED > UNKNOWN

        Actually, BUSINESS_PROFILE should NOT be overridden by document data.
        USER_CONFIRMED can upgrade DOCUMENT_VERIFIED and UNKNOWN.
        """
        current = self.get_provenance(field_key)

        # BUSINESS_PROFILE is highest - never override
        if current == DataProvenance.BUSINESS_PROFILE:
            return False

        # USER_CONFIRMED can override DOCUMENT_VERIFIED and UNKNOWN
        if current == DataProvenance.USER_CONFIRMED:
            return new_provenance == DataProvenance.USER_CONFIRMED

        # DOCUMENT_VERIFIED can override UNKNOWN
        if current == DataProvenance.DOCUMENT_VERIFIED:
            return new_provenance in (
                DataProvenance.USER_CONFIRMED,
                DataProvenance.DOCUMENT_VERIFIED,
            )

        # UNKNOWN can be upgraded to anything except BUSINESS_PROFILE
        if current == DataProvenance.UNKNOWN:
            return new_provenance != DataProvenance.BUSINESS_PROFILE

        return False

    def upgrade_provenance(
        self, field_key: str, new_provenance: DataProvenance, reason: str
    ) -> bool:
        """Attempt to upgrade field provenance.

        Returns True if upgrade was successful.
        """
        if self.can_override(field_key, new_provenance):
            self._field_provenance[field_key] = new_provenance
            return True
        return False


class DocumentVerificationService:
    """Service for managing document verification lifecycle."""

    def __init__(self) -> None:
        self._document_states: dict[UUID, DocumentVerificationLifecycle] = {}

    def get_state(self, document_id: UUID) -> DocumentVerificationLifecycle:
        """Get current verification state of a document."""
        return self._document_states.get(document_id, DocumentVerificationLifecycle.RECEIVED)

    def set_state(
        self, document_id: UUID, state: DocumentVerificationLifecycle
    ) -> None:
        """Set verification state of a document."""
        self._document_states[document_id] = state

    def can_transition(
        self, document_id: UUID, new_state: DocumentVerificationLifecycle
    ) -> bool:
        """Check if a state transition is valid."""
        current = self.get_state(document_id)

        valid_transitions = {
            DocumentVerificationLifecycle.RECEIVED: {
                DocumentVerificationLifecycle.EXTRACTION_PENDING,
                DocumentVerificationLifecycle.FAILED,
            },
            DocumentVerificationLifecycle.EXTRACTION_PENDING: {
                DocumentVerificationLifecycle.EXTRACTED,
                DocumentVerificationLifecycle.FAILED,
            },
            DocumentVerificationLifecycle.EXTRACTED: {
                DocumentVerificationLifecycle.VALIDATION_PENDING,
                DocumentVerificationLifecycle.REJECTED,
                DocumentVerificationLifecycle.NEEDS_REVIEW,
            },
            DocumentVerificationLifecycle.VALIDATION_PENDING: {
                DocumentVerificationLifecycle.VERIFIED,
                DocumentVerificationLifecycle.REJECTED,
                DocumentVerificationLifecycle.NEEDS_REVIEW,
            },
            DocumentVerificationLifecycle.NEEDS_REVIEW: {
                DocumentVerificationLifecycle.VERIFIED,
                DocumentVerificationLifecycle.REJECTED,
            },
            DocumentVerificationLifecycle.VERIFIED: set(),  # Terminal
            DocumentVerificationLifecycle.REJECTED: set(),  # Terminal
            DocumentVerificationLifecycle.FAILED: set(),  # Terminal
        }

        return new_state in valid_transitions.get(current, set())

    def transition(
        self, document_id: UUID, new_state: DocumentVerificationLifecycle
    ) -> bool:
        """Transition document to new state if valid."""
        if self.can_transition(document_id, new_state):
            self._document_states[document_id] = new_state
            return True
        return False


class AuditEventType(StrEnum):
    """Types of audit events for document intelligence."""

    EXTRACTION_RECEIVED = "extraction_received"
    FIELD_NORMALIZED = "field_normalized"
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"
    FIELD_VERIFIED = "field_verified"
    FIELD_REJECTED = "field_rejected"
    PROFILE_UPDATED = "profile_updated"
    PROVENANCE_UPGRADED = "provenance_upgraded"
    PROVENANCE_DENIED = "provenance_denied"
    DOCUMENT_STATE_CHANGED = "document_state_changed"


class AuditEvent(BaseModel):
    """Audit event for document intelligence operations."""

    event_type: AuditEventType
    document_id: UUID
    user_id: UUID
    business_profile_id: UUID | None
    field_type: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    provenance: DataProvenance | None = None
    reason: str | None = None
    metadata: dict[str, Any] | None = None
