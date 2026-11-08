"""Conversation schemas."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: str = Field(..., min_length=1, max_length=500)
    business_profile_id: UUID | None = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: str | None = Field(None, min_length=1, max_length=500)
    status: str | None = Field(None, pattern="^(active|archived|deleted)$")


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    """Schema for creating a user message in a conversation.

    Only user messages can be created through the public API.
    Assistant and system messages are created through trusted
    internal service methods only.
    """

    conversation_id: UUID
    role: Literal["user"] = Field(
        default="user",
        description="Message role. Only 'user' is allowed via the public API.",
    )
    content: str = Field(..., min_length=1)
    intent: str | None = None
    message_metadata: dict | None = None


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    intent: str | None
    message_metadata: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
