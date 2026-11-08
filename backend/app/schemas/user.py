"""User schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(..., description="User email address")
    full_name: str | None = Field(None, max_length=255, description="User full name")


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8, max_length=100, description="User password")


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: EmailStr | None = Field(None, description="User email address")
    full_name: str | None = Field(None, max_length=255, description="User full name")
    is_active: bool | None = Field(None, description="Whether user is active")
    is_verified: bool | None = Field(None, description="Whether user is verified")


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserInDB(UserResponse):
    """Schema for user with hashed password (internal use only)."""
    hashed_password: str

    model_config = {"from_attributes": True}
