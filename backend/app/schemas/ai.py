"""AI-related Pydantic schemas."""

from typing import Any

from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    """Request schema for AI text generation."""

    prompt: str = Field(..., min_length=1, max_length=10000)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=1, le=8192)
    system_instruction: str | None = Field(default=None, max_length=5000)


class AIResponse(BaseModel):
    """Response schema for AI text generation."""

    text: str
    model: str
    usage: dict[str, int] | None = None


class AIJSONRequest(BaseModel):
    """Request schema for AI JSON generation."""

    prompt: str = Field(..., min_length=1, max_length=10000)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=1, le=8192)
    system_instruction: str | None = Field(default=None, max_length=5000)


class AIJSONResponse(BaseModel):
    """Response schema for AI JSON generation."""

    data: dict[str, Any]
    model: str


class AIStructuredRequest(BaseModel):
    """Request schema for AI structured output generation."""

    prompt: str = Field(..., min_length=1, max_length=10000)
    response_schema: dict[str, Any]
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=1, le=8192)
    system_instruction: str | None = Field(default=None, max_length=5000)


class AIStructuredResponse(BaseModel):
    """Response schema for AI structured output generation."""

    data: dict[str, Any]
    model: str


class AIHealthResponse(BaseModel):
    """Response schema for AI health check."""

    enabled: bool
    model: str | None
    available: bool


class AITestRequest(BaseModel):
    """Request schema for AI test endpoint."""

    prompt: str = Field(..., min_length=1, max_length=2000)
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)


class AITestResponse(BaseModel):
    """Response schema for AI test endpoint."""

    text: str
    model: str
