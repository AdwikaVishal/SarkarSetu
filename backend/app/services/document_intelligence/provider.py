"""Extraction provider interface and base implementation.

Defines the interface for external document extraction providers.
Providers can be swapped without changing business logic.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.services.document_intelligence.schemas import (
    DocumentCategory,
    DocumentExtractionResult,
    ExtractionProviderPayload,
)


class ExtractionProvider(ABC):
    """Abstract base class for document extraction providers.

    External OCR/extraction services implement this interface.
    The interface is designed to be called asynchronously.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        ...

    @property
    @abstractmethod
    def provider_version(self) -> str:
        """Version of the provider software."""
        ...

    @abstractmethod
    async def process_document(
        self,
        document_id: UUID,
        storage_key: str,
        mime_type: str,
        document_category: str | None = None,
    ) -> DocumentExtractionResult:
        """Process a document and return extracted fields.

        Args:
            document_id: Unique document identifier.
            storage_key: Storage key/path for the document.
            mime_type: MIME type of the document.
            document_category: Optional category hint.

        Returns:
            Complete extraction result with all fields.
        """
        ...

    @abstractmethod
    async def validate_payload(self, payload: ExtractionProviderPayload) -> bool:
        """Validate a payload received from the provider's webhook/callback.

        Args:
            payload: The payload to validate.

        Returns:
            True if valid, False otherwise.
        """
        ...

    @abstractmethod
    async def get_supported_categories(self) -> list[str]:
        """Get list of document categories this provider supports."""
        ...


class MockExtractionProvider(ExtractionProvider):
    """Mock provider for testing and development.

    Returns synthetic extraction results for testing.
    """

    def __init__(self) -> None:
        self._results: dict[UUID, DocumentExtractionResult] = {}

    @property
    def provider_name(self) -> str:
        return "mock_extraction_provider"

    @property
    def provider_version(self) -> str:
        return "1.0.0-test"

    async def process_document(
        self,
        document_id: UUID,
        storage_key: str,
        mime_type: str,
        document_category: str | None = None,
    ) -> DocumentExtractionResult:
        """Return a mock extraction result."""
        from datetime import UTC, datetime

        from app.services.document_intelligence.schemas import (
            DocumentCategory,
            DocumentVerificationStatus,
            ExtractedField,
            ExtractionStatus,
            FieldType,
        )

        # Return cached result if exists
        if document_id in self._results:
            return self._results[document_id]

        # Create mock result based on category
        extracted_fields = []
        if document_category == DocumentCategory.PAN.value:
            extracted_fields = [
                ExtractedField(
                    field_type=FieldType.PAN,
                    raw_value="ABCDE1234F",
                    normalized_value="ABCDE1234F",
                    confidence=0.95,
                    format_valid=True,
                    page_reference=None,
                    location=None,
                    verification_status=DocumentVerificationStatus.UNVERIFIED,
                )
            ]
        elif document_category == DocumentCategory.AADHAAR.value:
            extracted_fields = [
                ExtractedField(
                    field_type=FieldType.PAN,  # Aadhaar often contains PAN
                    raw_value="1234 5678 9012",
                    normalized_value="123456789012",
                    confidence=0.90,
                    format_valid=True,
                    page_reference=None,
                    location=None,
                    verification_status=DocumentVerificationStatus.UNVERIFIED,
                )
            ]
        elif document_category == DocumentCategory.GST.value:
            extracted_fields = [
                ExtractedField(
                    field_type=FieldType.GSTIN,
                    raw_value="29ABCDE1234F1Z5",
                    normalized_value="29ABCDE1234F1Z5",
                    confidence=0.92,
                    format_valid=True,
                    page_reference=None,
                    location=None,
                    verification_status=DocumentVerificationStatus.UNVERIFIED,
                )
            ]
        elif document_category == DocumentCategory.UDYAM.value:
            extracted_fields = [
                ExtractedField(
                    field_type=FieldType.UDYAM_NUMBER,
                    raw_value="UDYAM-KA-12-0001234",
                    normalized_value="UDYAM-KA-12-0001234",
                    confidence=0.94,
                    format_valid=True,
                    page_reference=None,
                    location=None,
                    verification_status=DocumentVerificationStatus.UNVERIFIED,
                )
            ]

        result = DocumentExtractionResult(
            document_id=document_id,
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            business_profile_id=None,
            document_category=DocumentCategory(document_category or "other"),
            filename=f"mock_{document_id}.pdf",
            mime_type=mime_type,
            extraction_status=ExtractionStatus.EXTRACTED,
            extracted_fields=extracted_fields,
            page_count=1,
            provider=self.provider_name,
            provider_version=self.provider_version,
            extraction_timestamp=datetime.now(UTC),
            source_document_reference=storage_key,
            raw_response=None,
        )

        self._results[document_id] = result
        return result

    async def validate_payload(self, payload: ExtractionProviderPayload) -> bool:
        """Mock validation - always returns True."""
        return True

    async def get_supported_categories(self) -> list[str]:
        return [c.value for c in DocumentCategory]


def get_provider(provider_name: str | None = None) -> ExtractionProvider:
    """Factory function to get an extraction provider instance.

    Args:
        provider_name: Name of provider to instantiate. Defaults to mock.

    Returns:
        Configured extraction provider instance.
    """
    if provider_name is None or provider_name == "mock":
        return MockExtractionProvider()

    # In production, this would return real provider implementations
    raise ValueError(f"Unknown extraction provider: {provider_name}")
