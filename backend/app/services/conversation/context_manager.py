"""Conversation context management.

Builds context for AI services from conversation history.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conversation.conversation_service import ConversationService


class ConversationContextManager:
    """Builds context for AI services from conversation history.

    Provides methods to retrieve recent conversation history and build
    context strings that can be passed to AI agents.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.conversation_service = ConversationService(db)

    async def get_conversation_context(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        max_messages: int = 10,
    ) -> dict[str, object]:
        """Build a complete context dictionary for AI processing.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the authenticated user.
            max_messages: Maximum number of recent messages to include.

        Returns:
            Dictionary with conversation, messages, business_profile info.
        """
        conversation = await self.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            return {}

        messages = await self.conversation_service.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=max_messages,
        )

        return {
            "conversation_id": str(conversation.id),
            "title": conversation.title,
            "business_profile_id": (
                str(conversation.business_profile_id)
                if conversation.business_profile_id
                else None
            ),
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "intent": m.intent,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }

    async def build_conversation_context_string(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        max_messages: int = 10,
    ) -> str:
        """Build a text context string for AI prompts.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the authenticated user.
            max_messages: Maximum number of recent messages.

        Returns:
            Formatted context string.
        """
        conversation = await self.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            return ""

        messages = await self.conversation_service.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=max_messages,
        )

        lines = [f"Conversation: {conversation.title}"]
        if conversation.business_profile_id:
            lines.append(f"Business Profile ID: {conversation.business_profile_id}")
        lines.append("")
        lines.append("Conversation History:")
        if messages:
            for msg in messages:
                parts = [f"{msg.role}: {msg.content}"]
                if msg.intent:
                    parts.append(f"  [Intent: {msg.intent}]")
                lines.append("\n".join(parts))
                lines.append("")
        else:
            lines.append("No previous messages.")

        return "\n".join(lines)


class ContextManager:
    """High-level context manager for AI agents.

    Provides conversation context building with additional logic
    for clarification state and business context integration.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.conversation_service = ConversationService(db)
        self.conversation_context_manager = ConversationContextManager(db)

    async def build_context(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        max_messages: int = 10,
    ) -> dict[str, object]:
        """Build context dictionary for AI processing.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the authenticated user.
            max_messages: Maximum number of recent messages.

        Returns:
            Dictionary with conversation context.
        """
        return await self.conversation_context_manager.get_conversation_context(
            conversation_id=conversation_id,
            user_id=user_id,
            max_messages=max_messages,
        )

    async def build_context_string(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        max_messages: int = 10,
    ) -> str:
        """Build a text context string for AI prompts.

        Args:
            conversation_id: ID of the conversation.
            user_id: ID of the authenticated user.
            max_messages: Maximum number of recent messages.

        Returns:
            Formatted context string.
        """
        return await self.conversation_context_manager.build_conversation_context_string(
            conversation_id=conversation_id,
            user_id=user_id,
            max_messages=max_messages,
        )
