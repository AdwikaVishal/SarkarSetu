"""Document Intelligence integration for SarkarSetu AI.

Provides backend integration for connecting uploaded documents and externally
extracted document information to business profiles, conversations, workflows,
and the deterministic eligibility engine.

Components:
- DocumentIntelligenceService - Main orchestration service
- ExtractionProvider - Interface for external extraction providers
- FieldMapper - Maps extracted fields to business profile
- Normalizer - Deterministic field normalization
- ProvenanceTracker - Tracks data provenance
- VerificationService - Manages document verification lifecycle
- Validation - Validates extraction provider payloads
"""

from app.services.document_intelligence.document_errors import (
    DocumentIntelligenceError,
    DocumentIntelligenceErrorCategory,
)
from app.services.document_intelligence.document_service import DocumentIntelligenceService
from app.services.document_intelligence.field_mapper import FieldMapper
from app.services.document_intelligence.normalizer import (
    normalize_extraction_result,
    normalize_field,
)
from app.services.document_intelligence.provenance import (
    AuditEvent,
    AuditEventType,
    DataProvenance,
    DocumentVerificationLifecycle,
    DocumentVerificationService,
    ProvenanceTracker,
    VerificationPolicy,
)
from app.services.document_intelligence.provider import (
    ExtractionProvider,
    MockExtractionProvider,
    get_provider,
)
from app.services.document_intelligence.schemas import (
    DocumentCategory,
    DocumentExtractionResult,
    DocumentVerificationStatus,
    ExtractedField,
    ExtractionProviderPayload,
    ExtractionStatus,
    FieldConflict,
    FieldType,
    NormalizedField,
)
from app.services.document_intelligence.validation import (
    ExtractionValidator,
    validate_extraction_payload,
)

__all__ = [
    # Errors
    "DocumentIntelligenceError",
    "DocumentIntelligenceErrorCategory",
    # Service
    "DocumentIntelligenceService",
    # Provider
    "ExtractionProvider",
    "MockExtractionProvider",
    "get_provider",
    # Schemas
    "DocumentCategory",
    "DocumentExtractionResult",
    "DocumentVerificationStatus",
    "ExtractionProviderPayload",
    "ExtractionStatus",
    "ExtractedField",
    "FieldConflict",
    "FieldType",
    "NormalizedField",
    # Field Mapper
    "FieldMapper",
    # Normalizer
    "normalize_extraction_result",
    "normalize_field",
    # Provenance
    "AuditEvent",
    "AuditEventType",
    "DataProvenance",
    "DocumentVerificationLifecycle",
    "DocumentVerificationService",
    "ProvenanceTracker",
    "VerificationPolicy",
    # Validation
    "ExtractionValidator",
    "validate_extraction_payload",
]
