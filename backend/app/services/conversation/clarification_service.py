"""Clarification state management service.

Handles the persistence and retrieval of clarification state for conversations,
including pending clarifications, expiration, and cancellation.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ClarificationService:
    """Service for managing clarification state in conversations.

    Handles the lifecycle of clarification states:
    - Setting a clarification question when more info is needed
    - Resolving clarifications when user provides answers
    - Expiring old clarifications
    - Canceling clarifications when no longer needed
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def set_clarification(
        self,
        conversation_id: uuid.UUID,
        question: str,
        context: dict | None = None,
        expires_in_minutes: int = 30,
    ) -> None:
        """Set a clarification question for a conversation.

        Args:
            conversation_id: ID of the conversation.
            question: The clarification question to ask the user.
            context: Optional context about what information is needed.
            expires_in_minutes: Minutes until the clarification expires.

        Raises:
            ValueError: If conversation not found.
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise ValueError("Conversation not found")

        conversation.clarification_state = "pending"
        conversation.clarification_question = question
        conversation.clarification_data = context or {}
        conversation.clarification_created_at = datetime.now(UTC)
        conversation.clarification_expires_at = datetime.now(UTC).replace(
            minute=datetime.now(UTC).minute + expires_in_minutes,
        )

        await self.db.commit()
        await self.db.refresh(conversation)

    async def resolve_clarification(
        self,
        conversation_id: uuid.UUID,
        answer: str | None = None,
        answer_data: dict | None = None,
    ) -> bool:
        """Mark a clarification as resolved with the user's answer.

        Args:
            conversation_id: ID of the conversation.
            answer: The user's answer to the clarification question.
            answer_data: Optional structured data extracted from the answer.

        Returns:
            True if clarification was resolved, False if no pending
            clarification exists.
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None or conversation.clarification_state != "pending":
            return False

        conversation.clarification_state = "resolved"
        conversation.clarification_data = {
            **(conversation.clarification_data or {}),
            "answer": answer,
            **(answer_data or {}),
        }

        await self.db.commit()
        await self.db.refresh(conversation)
        return True

    async def expire_clarification(
        self,
        conversation_id: uuid.UUID,
    ) -> bool:
        """Mark a clarification as expired.

        Args:
            conversation_id: ID of the conversation.

        Returns:
            True if clarification was expired, False if not pending.
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None or conversation.clarification_state != "pending":
            return False

        conversation.clarification_state = "expired"
        await self.db.commit()
        await self.db.refresh(conversation)
        return True

    async def cancel_clarification(
        self,
        conversation_id: uuid.UUID,
    ) -> bool:
        """Cancel a pending clarification.

        Args:
            conversation_id: ID of the conversation.

        Returns:
            True if clarification was cancelled, False if none pending.
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None or conversation.clarification_state != "pending":
            return False

        conversation.clarification_state = "cancelled"
        conversation.clarification_question = None
        conversation.clarification_data = None
        conversation.clarification_created_at = None
        conversation.clarification_expires_at = None

        await self.db.commit()
        await self.db.refresh(conversation)
        return True

    async def get_clarification_state(
        self,
        conversation_id: uuid.UUID,
    ) -> dict | None:
        """Get the current clarification state for a conversation.

        Args:
            conversation_id: ID of the conversation.

        Returns:
            Dict with clarification info or None if no pending clarification.
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None or conversation.clarification_state != "pending":
            return None

        # Check if expired
        if (
            conversation.clarification_expires_at
            and conversation.clarification_expires_at < datetime.now(UTC)
        ):
            await self.expire_clarification(conversation_id)
            return None

        return {
            "question": conversation.clarification_question,
            "data": conversation.clarification_data or {},
            "created_at": conversation.clarification_created_at,
            "expires_at": conversation.clarification_expires_at,
        }

    async def is_clarification_pending(
        self,
        conversation_id: uuid.UUID,
    ) -> bool:
        """Check if a conversation has a pending clarification.

        Args:
            conversation_id: ID of the conversation.

        Returns:
            True if there's a pending clarification, False otherwise.
        """
        result = await self.get_clarification_state(conversation_id)
        return result is not None
