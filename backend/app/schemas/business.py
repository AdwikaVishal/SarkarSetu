"""BusinessProfile schemas."""
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BusinessProfileBase(BaseModel):
    """Base business profile schema."""

    business_name: str = Field(..., min_length=1, max_length=255)
    business_type: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    annual_turnover: float | None = Field(
        None,
        ge=0,
        description="Annual turnover in INR",
    )
    employee_count: int | None = Field(None, ge=0, description="Number of employees")
    sales_channels: list[str] = Field(default_factory=list)
    business_structure: str = Field(..., min_length=1, max_length=100)
    business_stage: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    city: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    udyam_number: str | None = Field(None, max_length=50)
    gstin: str | None = Field(None, max_length=15)
    website: str | None = Field(None, max_length=255)
    woman_owned: bool = Field(default=False)
    social_category: str | None = Field(None, max_length=100)
    products_services: list[str] | None = None
    operating_mode: str | None = Field(
        None,
        pattern="^(online|offline|both)$",
    )
    date_of_establishment: datetime | None = None

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str | None) -> str | None:
        if v is not None and (not v.isdigit() or len(v) != 6):
            raise ValueError("PIN code must be a 6-digit number")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str | None) -> str | None:
        if v is not None and (len(v) != 15 or not v[:2].isdigit()):
            raise ValueError("GSTIN must start with 2-digit state code")
        return v

    @field_validator("date_of_establishment")
    @classmethod
    def validate_date_of_establishment(cls, v: datetime | None) -> datetime | None:
        if v is not None and v > datetime.now(UTC):
            raise ValueError("Date of establishment cannot be in the future")
        return v


class BusinessProfileCreate(BusinessProfileBase):
    """Schema for creating a business profile."""
    pass


class BusinessProfileUpdate(BaseModel):
    """Schema for updating a business profile."""

    business_name: str | None = Field(None, min_length=1, max_length=255)
    business_type: str | None = Field(None, min_length=1, max_length=100)
    industry: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, min_length=1, max_length=100)
    district: str | None = Field(None, min_length=1, max_length=100)
    annual_turnover: float | None = Field(None, ge=0)
    employee_count: int | None = Field(None, ge=0)
    sales_channels: list[str] | None = None
    business_structure: str | None = Field(None, min_length=1, max_length=100)
    business_stage: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    city: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    udyam_number: str | None = Field(None, max_length=50)
    gstin: str | None = Field(None, max_length=15)
    website: str | None = Field(None, max_length=255)
    woman_owned: bool | None = None
    social_category: str | None = Field(None, max_length=100)
    products_services: list[str] | None = None
    operating_mode: str | None = Field(
        None,
        pattern="^(online|offline|both)$",
    )
    date_of_establishment: datetime | None = None

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str | None) -> str | None:
        if v is not None and (not v.isdigit() or len(v) != 6):
            raise ValueError("PIN code must be a 6-digit number")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str | None) -> str | None:
        if v is not None and (len(v) != 15 or not v[:2].isdigit()):
            raise ValueError("GSTIN must start with 2-digit state code")
        return v

    @field_validator("date_of_establishment")
    @classmethod
    def validate_date_of_establishment(cls, v: datetime | None) -> datetime | None:
        if v is not None and v > datetime.now(UTC):
            raise ValueError("Date of establishment cannot be in the future")
        return v


class BusinessProfileResponse(BusinessProfileBase):
    """Schema for business profile response."""

    id: UUID
    user_id: UUID
    is_deleted: bool
    deleted_at: datetime | None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BusinessProfileListResponse(BaseModel):
    """Schema for listing business profiles."""

    items: list[BusinessProfileResponse]
    total: int


class SetDefaultBusinessProfile(BaseModel):
    """Schema for setting default business profile."""

    business_id: UUID
