from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.agreement import AgreementStatus, PartyType


class PartyCreate(BaseModel):
    party_type: PartyType
    name: str = Field(min_length=1, max_length=200)
    details: str | None = Field(default=None, max_length=500)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)


class AgreementCreate(BaseModel):
    agreement_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    tenure: str | None = Field(default=None, max_length=120)
    monthly_rent: float | None = Field(default=None, ge=0)
    annual_increment: float | None = Field(default=None, ge=0)
    security_deposit: float | None = Field(default=None, ge=0)
    lock_in: str | None = Field(default=None, max_length=120)
    fitout_period: str | None = Field(default=None, max_length=120)
    remarks: str | None = None
    parties: list[PartyCreate] = []


class AgreementUpdate(BaseModel):
    agreement_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    tenure: str | None = None
    monthly_rent: float | None = None
    annual_increment: float | None = None
    security_deposit: float | None = None
    lock_in: str | None = None
    fitout_period: str | None = None
    remarks: str | None = None


class AgreementStatusUpdate(BaseModel):
    status: AgreementStatus
    remarks: str | None = None


class PartyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    party_type: PartyType
    name: str
    details: str | None = None
    email: str | None = None
    phone: str | None = None


class AgreementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    agreement_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    tenure: str | None = None
    monthly_rent: float | None = None
    annual_increment: float | None = None
    security_deposit: float | None = None
    lock_in: str | None = None
    fitout_period: str | None = None
    status: AgreementStatus
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime
    parties: list[PartyRead] = []