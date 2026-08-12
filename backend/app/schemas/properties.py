from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.property import PropertyStatus


class PropertyCreate(BaseModel):
    address: str = Field(min_length=1, max_length=500)
    area_sqft: float | None = None
    rent: float | None = Field(default=None, ge=0)
    deposit: float | None = Field(default=None, ge=0)
    annual_increment: float | None = Field(default=None, ge=0)
    entrance: str | None = Field(default=None, max_length=20)
    restroom: str | None = Field(default=None, max_length=20)
    possession_status: str | None = Field(default=None, max_length=40)
    remarks: str | None = None
    status: PropertyStatus = PropertyStatus.UNDER_REVIEW


class PropertyUpdate(BaseModel):
    address: str | None = None
    area_sqft: float | None = None
    rent: float | None = None
    deposit: float | None = None
    annual_increment: float | None = None
    entrance: str | None = None
    restroom: str | None = None
    possession_status: str | None = None
    remarks: str | None = None
    status: PropertyStatus | None = None


class PropertyStatusUpdate(BaseModel):
    status: PropertyStatus
    remarks: str | None = None


class PropertyCancel(BaseModel):
    remarks: str | None = None


class PropertyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    option_sequence: int
    address: str
    area_sqft: float | None = None
    rent: float | None = None
    deposit: float | None = None
    annual_increment: float | None = None
    entrance: str | None = None
    restroom: str | None = None
    possession_status: str | None = None
    remarks: str | None = None
    status: PropertyStatus
    rent_limit_check: str | None = None
    applicable_rent_limit: float | None = None
    created_at: datetime
    updated_at: datetime