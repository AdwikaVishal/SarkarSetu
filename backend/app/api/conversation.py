"""Conversation API router.

Provides conversation management endpoints:
- POST /api/v1/conversations - Create conversation
- GET /api/v1/conversations - List conversations
- GET /api/v1/conversations/{conversation_id} - Get conversation
- PATCH /api/v1/conversations/{conversation_id} - Update conversation
- DELETE /api/v1/conversations/{conversation_id} - Archive conversation
- POST /api/v1/conversations/{conversation_id}/restore - Restore conversation
- POST /api/v1/conversations/{conversation_id}/messages - Create message
- GET /api/v1/conversations/{conversation_id}/messages - Get messages
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.services.conversation.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def get_conversation_service(
    db: AsyncSession = Depends(get_db),
) -> ConversationService:
    """Dependency to get ConversationService instance."""
    return ConversationService(db)


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
    description="Create a new conversation for the authenticated user.",
)
async def create_conversation(
    conversation_data: ConversationCreate,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_active_user),
) -> ConversationResponse:
    """Create a new conversation."""
    conversation = await conversation_service.create_conversation(
        user_id=current_user.id,
        business_profile_id=conversation_data.business_profile_id,
        title=conversation_data.title,
    )
    return ConversationResponse.model_validate(conversation)


@router.get(
    "/",
    response_model=list[ConversationResponse],
    summary="List conversations",
    description="List all active conversations for the authenticated user.",
)
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_active_user),
) -> list[ConversationResponse]:
    """List all active conversations for the current user."""
    conversations = await conversation_service.list_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation",
    description="Retrieve a specific conversation owned by the user.",
)
async def get_conversation(
    conversation_id: UUID,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_active_user),
) -> ConversationResponse:
    """Get a conversation by ID owned by the current user."""
    conversation = await conversation_service.get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return ConversationResponse.model_validate(conversation)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation",
    description="Update conversation title or status.",
)
async def update_conversation(
    conversation_id: UUID,
    update_data: ConversationUpdate,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_active_user),
) -> ConversationResponse:
    """Update a conversation's title or status."""
    conversation = await conversation_service.update_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        title=update_data.title,
        status=update_data.status,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return ConversationResponse.model_validate(conversation)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive conversation",
    description="Archive (soft-delete) a conversation.",
)
async def archive_conversation(
    conversation_id: UUID,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Archive (soft-delete) a conversation owned by the current user."""
    conversation = await conversation_service.archive_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )


@router.post(
    "/{conversation_id}/restore",
    response_model=ConversationResponse,
    summary="Restore archived conversation",
    description="Restore an archived conversation owned by the user.",
)
async def restore_conversation(
    conversation_id: UUID,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_active_user),
) -> ConversationResponse:
    """Restore an archived conversation owned by the current user."""
    conversation = await conversation_service.restore_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return ConversationResponse.model_validate(conversation)


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create message",
    description="Create a new message in a conversation.",
)
async def create_message(
    conversation_id: UUID,
    message_data: MessageCreate,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_active_user),
) -> MessageResponse:
    """Create a new user message in a conversation owned by the user."""
    message = await conversation_service.persist_user_message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=message_data.content,
        intent=message_data.intent,
        message_metadata=message_data.message_metadata,
    )
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return MessageResponse.model_validate(message)


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
    summary="List messages",
    description="List messages in a conversation owned by the user.",
)
async def list_messages(
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 50,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_active_user),
) -> list[MessageResponse]:
    """List messages in a conversation owned by the current user."""
    messages = await conversation_service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return [MessageResponse.model_validate(m) for m in messages]
