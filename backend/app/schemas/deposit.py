from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.deposit import DepositStatus, LOAStatus, PayeeStatus


class DepositCreate(BaseModel):
    total_amount: float = Field(gt=0)
    remarks: str | None = None


class DepositPayeeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    remarks: str | None = None


class DepositPaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    payment_date: date | None = None
    reference: str | None = Field(default=None, max_length=120)


class PayeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    amount: float
    status: PayeeStatus
    paid_amount: float = 0
    remarks: str | None = None


class DepositPaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    payment_date: date | None = None
    reference: str | None = None
    status: str
    created_by: int | None = None
    created_at: datetime


class DepositRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    total_amount: float
    status: DepositStatus
    paid_amount: float = 0
    remarks: str | None = None
    payees: list[PayeeRead] = []


class LOARequestCreate(BaseModel):
    employee: str = Field(min_length=1, max_length=200)
    employee_code: str = Field(min_length=1, max_length=50)
    request_date: date | None = None
    execution_date: date | None = None
    agreement_tenure: str | None = Field(default=None, max_length=120)
    remarks: str | None = None


class LOARequestUpdate(BaseModel):
    status: LOAStatus
    issued_date: date | None = None
    execution_date: date | None = None
    remarks: str | None = None


class LOARequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    employee: str
    employee_code: str
    request_date: date | None = None
    execution_date: date | None = None
    agreement_tenure: str | None = None
    issued_date: date | None = None
    status: LOAStatus
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime