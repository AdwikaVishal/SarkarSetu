"""Business profile service layer.

Provides conversation and message management operations.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import BusinessProfile
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.ownership import OwnershipService


class ConversationService:
    """Service for conversation and message management.

    Handles all CRUD operations for conversations and messages,
    ensuring proper ownership validation and data integrity.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ownership = OwnershipService(db)

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        business_profile_id: uuid.UUID | None = None,
        title: str = "New Conversation",
    ) -> Conversation:
        """Create a new conversation for a user.

        Args:
            user_id: ID of the user creating the conversation.
            business_profile_id: Optional business profile ID to associate.
            title: Title of the conversation.

        Returns:
            The created conversation.

        Raises:
            ValueError: If business profile doesn't exist or isn't owned by user.
        """
        # Verify business profile ownership if provided
        if business_profile_id:
            result = await self.db.execute(
                select(BusinessProfile).where(
                    BusinessProfile.id == business_profile_id,
                    BusinessProfile.user_id == user_id,
                    BusinessProfile.is_deleted == False,  # noqa: E712
                )
            )
            profile = result.scalar_one_or_none()
            if profile is None:
                raise ValueError(
                    "Business profile not found or not owned by user"
                )

        conversation = Conversation(
            user_id=user_id,
            business_profile_id=business_profile_id,
            title=title,
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Conversation | None:
        """Get a conversation owned by the user.

        Args:
            user_id: ID of the authenticated user.
            conversation_id: ID of the conversation.

        Returns:
            The conversation if found and owned by user, else None.
        """
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Conversation]:
        """List all non-archived conversations for a user.

        Args:
            user_id: ID of the authenticated user.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of conversation objects.
        """
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,  # noqa: E712
            )
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
        status: str | None = None,
    ) -> Conversation | None:
        """Update a conversation's title or status.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the authenticated user.
            title: New title (optional).
            status: New status (optional).

        Returns:
            The updated conversation, or None if not found.
        """
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            return None

        if title is not None:
            conversation.title = title
        if status is not None:
            conversation.status = status

        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def archive_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        """Archive (soft-delete) a conversation.

        Args:
            user_id: ID of the authenticated user.
            conversation_id: ID of the conversation.

        Returns:
            The archived conversation, or None if not found.
        """
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            return None

        conversation.status = "archived"
        conversation.is_deleted = True
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def restore_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        """Restore an archived conversation.

        Args:
            user_id: ID of the authenticated user.
            conversation_id: ID of the conversation.

        Returns:
            The restored conversation, or None if not found.
        """
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            return None

        conversation.status = "active"
        conversation.is_deleted = False
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        content: str,
        intent: str | None = None,
        message_metadata: dict | None = None,
    ) -> Message | None:
        """Create a message in a conversation.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the user creating the message.
            role: Role of the message sender ('user', 'assistant', 'system').
            content: Message content.
            intent: Optional intent classification.
            message_metadata: Optional metadata dict.

        Returns:
            The created message, or None if conversation not found.
        """
        # Verify conversation belongs to user
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            return None

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=intent,
            metadata=message_metadata,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def persist_user_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        intent: str | None = None,
        message_metadata: dict | None = None,
    ) -> Message | None:
        """Persist a user message through a trusted internal path.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the user creating the message.
            content: Message content.
            intent: Optional intent classification.
            message_metadata: Optional metadata dict.

        Returns:
            The created message, or None if conversation not found.
        """
        return await self.create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=content,
            intent=intent,
            message_metadata=message_metadata,
        )

    async def persist_assistant_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        intent: str | None = None,
        message_metadata: dict | None = None,
    ) -> Message | None:
        """Persist an assistant message through a trusted internal path.

        Used by the AI orchestrator to store assistant responses.
        Not accessible through the public API.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the user owning the conversation.
            content: Message content.
            intent: Optional intent classification.
            message_metadata: Optional metadata dict.

        Returns:
            The created message, or None if conversation not found.
        """
        return await self.create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=content,
            intent=intent,
            message_metadata=message_metadata,
        )

    async def persist_system_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        intent: str | None = None,
        message_metadata: dict | None = None,
    ) -> Message | None:
        """Persist a system message through a trusted internal path.

        Used by backend services for system-generated messages.
        Not accessible through the public API.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the user owning the conversation.
            content: Message content.
            intent: Optional intent classification.
            message_metadata: Optional metadata dict.

        Returns:
            The created message, or None if conversation not found.
        """
        return await self.create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="system",
            content=content,
            intent=intent,
            message_metadata=message_metadata,
        )

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Message]:
        """Get messages for a conversation.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the authenticated user.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of messages ordered by created_at ascending.
        """
        # First verify conversation ownership
        conversation = await self.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            return []

        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
