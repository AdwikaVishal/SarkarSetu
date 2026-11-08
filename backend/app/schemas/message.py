"""Message schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base message schema."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    intent: str | None = Field(None, max_length=100)
    metadata: dict | None = None


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    conversation_id: UUID


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    content: str | None = Field(None, min_length=1)
    intent: str | None = Field(None, max_length=100)
    metadata: dict | None = None


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: UUID
    conversation_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
