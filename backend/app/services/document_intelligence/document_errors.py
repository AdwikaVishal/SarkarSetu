"""Document Intelligence error types.

Structured error categories and error types for the document intelligence
integration layer.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID


class DocumentIntelligenceErrorCategory(StrEnum):
    """Categories of document intelligence errors."""

    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    PROVIDER_ERROR = "provider_error"
    NORMALIZATION_ERROR = "normalization_error"
    PROVENANCE_ERROR = "provenance_error"
    VERIFICATION_ERROR = "verification_error"
    INTERNAL_ERROR = "internal_error"


class DocumentIntelligenceError(Exception):
    """Base structured error for document intelligence."""

    def __init__(
        self,
        code: str,
        message: str,
        category: DocumentIntelligenceErrorCategory = DocumentIntelligenceErrorCategory.INTERNAL_ERROR,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.category = category
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "context": self.context,
        }


class ExtractionValidationError(DocumentIntelligenceError):
    """Raised when extraction provider payload fails validation."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged = dict(context) if context else {}
        if field:
            merged["field"] = field
        super().__init__(
            code="extraction_validation_error",
            message=message,
            category=DocumentIntelligenceErrorCategory.VALIDATION_ERROR,
            context=merged,
        )


class DocumentNotFoundError(DocumentIntelligenceError):
    """Raised when a document is not found."""

    def __init__(self, document_id: UUID) -> None:
        super().__init__(
            code="document_not_found",
            message=f"Document {document_id} not found.",
            category=DocumentIntelligenceErrorCategory.NOT_FOUND,
            context={"document_id": str(document_id)},
        )


class DocumentAccessForbiddenError(DocumentIntelligenceError):
    """Raised when user tries to access another user's document."""

    def __init__(self, document_id: UUID, user_id: UUID) -> None:
        super().__init__(
            code="document_access_forbidden",
            message=f"Document {document_id} is not owned by user {user_id}.",
            category=DocumentIntelligenceErrorCategory.FORBIDDEN,
            context={"document_id": str(document_id), "user_id": str(user_id)},
        )


class BusinessProfileMismatchError(DocumentIntelligenceError):
    """Raised when document's business profile doesn't match request."""

    def __init__(
        self,
        document_id: UUID,
        document_business_profile_id: UUID | None,
        request_business_profile_id: UUID | None,
    ) -> None:
        super().__init__(
            code="business_profile_mismatch",
            message="Document business profile does not match requested business profile.",
            category=DocumentIntelligenceErrorCategory.CONFLICT,
            context={
                "document_id": str(document_id),
                "document_business_profile_id": str(document_business_profile_id)
                if document_business_profile_id
                else None,
                "request_business_profile_id": str(request_business_profile_id)
                if request_business_profile_id
                else None,
            },
        )


class NormalizationError(DocumentIntelligenceError):
    """Raised when field normalization fails."""

    def __init__(
        self,
        message: str,
        field_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged = dict(context) if context else {}
        if field_type:
            merged["field_type"] = field_type
        super().__init__(
            code="normalization_error",
            message=message,
            category=DocumentIntelligenceErrorCategory.NORMALIZATION_ERROR,
            context=merged,
        )


class ProvenanceError(DocumentIntelligenceError):
    """Raised when provenance rules are violated."""

    def __init__(
        self,
        message: str,
        field_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged = dict(context) if context else {}
        if field_type:
            merged["field_type"] = field_type
        super().__init__(
            code="provenance_error",
            message=message,
            category=DocumentIntelligenceErrorCategory.PROVENANCE_ERROR,
            context=merged,
        )


class VerificationError(DocumentIntelligenceError):
    """Raised when verification policy is violated."""

    def __init__(
        self,
        message: str,
        field_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged = dict(context) if context else {}
        if field_type:
            merged["field_type"] = field_type
        super().__init__(
            code="verification_error",
            message=message,
            category=DocumentIntelligenceErrorCategory.VERIFICATION_ERROR,
            context=merged,
        )


class ConflictResolutionError(DocumentIntelligenceError):
    """Raised when conflict resolution fails."""

    def __init__(
        self,
        message: str,
        review_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged = dict(context) if context else {}
        if review_id:
            merged["review_id"] = str(review_id)
        super().__init__(
            code="conflict_resolution_error",
            message=message,
            category=DocumentIntelligenceErrorCategory.CONFLICT,
            context=merged,
        )


class ProviderError(DocumentIntelligenceError):
    """Raised when extraction provider returns an error or malformed response."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged = dict(context) if context else {}
        if provider:
            merged["provider"] = provider
        super().__init__(
            code="provider_error",
            message=message,
            category=DocumentIntelligenceErrorCategory.PROVIDER_ERROR,
            context=merged,
        )


class DuplicateExtractionError(DocumentIntelligenceError):
    """Raised when duplicate extraction result is received for same document."""

    def __init__(self, document_id: UUID) -> None:
        super().__init__(
            code="duplicate_extraction",
            message=f"Extraction result already exists for document {document_id}.",
            category=DocumentIntelligenceErrorCategory.CONFLICT,
            context={"document_id": str(document_id)},
        )
