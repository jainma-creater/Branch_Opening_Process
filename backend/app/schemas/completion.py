from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.completion import FitoutStatus, ReadinessStatus


class FitoutCreate(BaseModel):
    vendor_id: int | None = None
    scope: str = Field(min_length=1, max_length=500)
    start_date: date | None = None
    expected_end_date: date | None = None
    remarks: str | None = Field(default=None, max_length=1000)


class FitoutUpdate(BaseModel):
    status: FitoutStatus
    completion_date: date | None = None
    remarks: str | None = Field(default=None, max_length=1000)


class FitoutRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    vendor_id: int | None = None
    scope: str
    status: FitoutStatus
    start_date: date | None = None
    expected_end_date: date | None = None
    completion_date: date | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class ReadinessItemCreate(BaseModel):
    item_name: str = Field(min_length=1, max_length=200)
    remarks: str | None = Field(default=None, max_length=1000)


class ReadinessItemUpdate(BaseModel):
    status: ReadinessStatus
    remarks: str | None = Field(default=None, max_length=1000)


class ReadinessItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    item_name: str
    status: ReadinessStatus
    remarks: str | None = None
    created_at: datetime


class OpeningRecordCreate(BaseModel):
    opening_date: date | None = None
    inaugurated_by: str | None = Field(default=None, max_length=200)
    remarks: str | None = Field(default=None, max_length=1000)


class OpeningRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    opening_date: date | None = None
    inaugurated_by: str | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime
