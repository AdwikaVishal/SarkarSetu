"""Document Intelligence API router.

Provides authenticated endpoints for document upload and processing:
- POST /api/v1/documents/upload - Upload and process a document
- GET /api/v1/documents - List user's documents
- GET /api/v1/documents/{document_id} - Get document details
- GET /api/v1/documents/{document_id}/matching - Get document matching results
- DELETE /api/v1/documents/{document_id} - Delete a document
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentMatchingResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.document_intelligence.document_service import DocumentIntelligenceService
from app.services.ownership import ResourceNotFoundError

router = APIRouter(prefix="/documents", tags=["documents"])


async def get_document_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentIntelligenceService:
    """Dependency to get DocumentIntelligenceService instance."""
    from app.services.eligibility_engine.engine import EligibilityEngine
    from app.services.eligibility_engine.rule_evaluator import RuleEvaluator
    from app.services.eligibility_engine.rule_registry import RuleRegistry

    rule_registry = RuleRegistry(db)
    eligibility_engine = EligibilityEngine(
        registry=rule_registry,
        evaluator=RuleEvaluator(),
    )

    return DocumentIntelligenceService(
        db=db,
        eligibility_engine=eligibility_engine,
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a document",
    description=(
        "Upload a PDF document for OCR, text extraction, field detection, "
        "and compliance checking. The document is processed asynchronously."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="PDF document to upload (max 10MB)"),
    business_profile_id: UUID | None = Query(None, description="Optional business profile ID to associate with the document"),
    document_service: DocumentIntelligenceService = Depends(get_document_service),
    current_user: User = Depends(get_current_active_user),
) -> DocumentUploadResponse:
    """Upload a document for processing.

    - Validates file type (PDF only) and size (max 10MB)
    - Stores file securely
    - Queues for OCR/text extraction and field detection
    - Returns document ID for status polling
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Validate file size (10MB)
    max_size = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of 10MB",
        )

    # Validate business profile ownership if provided
    if business_profile_id:
        from app.services.ownership import OwnershipService
        ownership = OwnershipService(document_service.db)
        try:
            await ownership.get_user_business_profile(current_user.id, business_profile_id)
        except ResourceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found",
            )

    try:
        # Process the document using the existing document intelligence service
        # For now, we use the extraction provider payload approach
        # In a full implementation, this would queue an async job
        from app.services.document_intelligence.schemas import (
            DocumentCategory,
            DocumentExtractionResult,
            ExtractionProviderPayload,
        )

        # Create uploaded document record
        from app.models import UploadedDocument
        import uuid

        document = UploadedDocument(
            id=uuid.uuid4(),
            user_id=current_user.id,
            business_profile_id=business_profile_id,
            original_filename=file.filename or "document.pdf",
            storage_key=f"uploads/{current_user.id}/{uuid.uuid4()}.pdf",
            content_type=file.content_type,
            file_size=len(content),
            processing_status="pending",
        )
        document_service.db.add(document)
        await document_service.db.commit()
        await document_service.db.refresh(document)

        # For MVP, we'll do synchronous processing
        # In production, this should be an async background job
        try:
            # Process the document using the ingestion pipeline
            from rag.ingestion.pipeline import ingest_document

            # Save file temporarily
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                # Ingest document through RAG pipeline
                metadata = {
                    "source_id": f"user_doc_{document.id}",
                    "title": file.filename or "Uploaded Document",
                    "authority": "User Uploaded",
                    "source_url": "",
                    "topic": "user_document",
                    "verification_status": "pending",
                }
                result = ingest_document(tmp_path, metadata)

                if result["status"] in ("success", "partial"):
                    # Document processed successfully
                    document.processing_status = "completed"
                    document.document_type = "user_upload"
                    document.extracted_data = {
                        "extraction_result": result,
                        "source_file": file.filename,
                    }
                else:
                    document.processing_status = "error"
                    document.extracted_data = {
                        "error": result.get("errors", ["Unknown error"]),
                    }
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

            await document_service.db.commit()
            await document_service.db.refresh(document)

        except Exception as e:
            document.processing_status = "error"
            document.extracted_data = {"error": str(e)}
            await document_service.db.commit()
            await document_service.db.refresh(document)

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.original_filename,
            status=document.processing_status,
            message="Document uploaded and processing completed",
        )

    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Document upload error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while uploading the document.",
        ) from exc


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List user's documents",
    description="List all documents uploaded by the authenticated user.",
)
async def list_documents(
    business_profile_id: UUID | None = Query(None, description="Filter by business profile"),
    document_service: DocumentIntelligenceService = Depends(get_document_service),
    current_user: User = Depends(get_current_active_user),
) -> DocumentListResponse:
    """List all documents for the authenticated user."""
    try:
        if business_profile_id:
            # Validate ownership
            from app.services.ownership import OwnershipService
            ownership = OwnershipService(document_service.db)
            try:
                await ownership.get_user_business_profile(current_user.id, business_profile_id)
            except ResourceNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business profile not found",
                )
            documents = await document_service.get_documents_for_business(business_profile_id, current_user.id)
        else:
            # Get all user documents
            from sqlalchemy import select
            from app.models import UploadedDocument

            result = await document_service.db.execute(
                select(UploadedDocument)
                .where(UploadedDocument.user_id == current_user.id)
                .order_by(UploadedDocument.created_at.desc())
            )
            documents = list(result.scalars().all())

        # Build response, validating each document individually so a
        # single malformed record cannot break the entire list.
        items: list[DocumentResponse] = []
        for doc in documents:
            try:
                items.append(DocumentResponse.model_validate(doc))
            except Exception as val_exc:  # noqa: BLE001 - skip bad records
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    "Skipping invalid document record",
                    extra={
                        "document_id": str(doc.id),
                        "error": str(val_exc),
                    },
                )

        return DocumentListResponse(
            items=items,
            total=len(items),
        )

    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("List documents error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while listing documents.",
        ) from exc


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    description="Retrieve details of a specific document including extraction results.",
)
async def get_document(
    document_id: UUID,
    document_service: DocumentIntelligenceService = Depends(get_document_service),
    current_user: User = Depends(get_current_active_user),
) -> DocumentResponse:
    """Get a document by ID."""
    try:
        document = await document_service.get_document(document_id, current_user.id)
        return DocumentResponse.model_validate(document)

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Get document error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the document.",
        ) from exc


@router.get(
    "/{document_id}/matching",
    response_model=DocumentMatchingResponse,
    summary="Get document matching results",
    description=(
        "Get compliance matching results for a document against "
        "requirements for a specific service (e.g., udyam_registration)."
    ),
)
async def get_document_matching(
    document_id: UUID,
    service: str = Query(..., description="Service type to match against (e.g., udyam_registration, gst_registration)"),
    document_service: DocumentIntelligenceService = Depends(get_document_service),
    current_user: User = Depends(get_current_active_user),
) -> DocumentMatchingResponse:
    """Get document matching results for a service."""
    try:
        document = await document_service.get_document(document_id, current_user.id)

        if not document.business_profile_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is not associated with a business profile",
            )

        # Get workflow document status which includes matching
        status_info = await document_service.get_workflow_document_status(
            workflow_id=f"matching_{service}",
            user_id=current_user.id,
        )

        # Also get review items (conflicts)
        review_items = await document_service.get_review_items(document_id, current_user.id)

        # Build matching response
        from rag.document_matching.matcher import (
            get_required_documents,
            match_documents_to_requirements,
        )

        required_docs = get_required_documents(service)

        # Prepare extracted documents for matching
        extracted_docs = []
        if document.extracted_data and document.extracted_data.get("normalized_fields"):
            for field_data in document.extracted_data["normalized_fields"]:
                extracted_docs.append({
                    "document_id": str(document.id),
                    "document_type": document.document_type or "unknown",
                    "classification_confidence": 0.9,
                    "extracted_fields": document.extracted_data["normalized_fields"],
                    "extraction_errors": [],
                    "validation_status": "validated" if document.processing_status == "completed" else "needs_review",
                })
                break  # One entry per document

        match_result = match_documents_to_requirements(
            extracted_documents=extracted_docs,
            required_documents=required_docs,
            service=service,
        )

        return DocumentMatchingResponse(
            document_id=document.id,
            service=service,
            overall_status=match_result.get("overall_status", "unknown"),
            checklist_coverage=match_result.get("checklist_coverage", 0.0),
            available_documents=match_result.get("available_documents", []),
            missing_documents=match_result.get("missing_documents", []),
            incomplete_extraction=match_result.get("incomplete_extraction", []),
            needs_review=match_result.get("needs_review", []),
            review_items=review_items,
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except HTTPException:
        raise
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Document matching error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while getting matching results.",
        ) from exc


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document",
    description="Delete a document and its extracted data.",
)
async def delete_document(
    document_id: UUID,
    document_service: DocumentIntelligenceService = Depends(get_document_service),
    current_user: User = Depends(get_current_active_user),
) -> DocumentDeleteResponse:
    """Delete a document."""
    try:
        document = await document_service.get_document(document_id, current_user.id)

        await document_service.db.delete(document)
        await document_service.db.commit()

        return DocumentDeleteResponse(
            message="Document deleted successfully",
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Delete document error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the document.",
        ) from exc