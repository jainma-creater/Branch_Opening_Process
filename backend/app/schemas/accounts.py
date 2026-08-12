from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.accounts import AccountReviewDecision, InvoiceStatus


class QuotationAccountsReview(BaseModel):
    decision: AccountReviewDecision
    approved_amount: float | None = Field(default=None, ge=0)
    comments: str | None = Field(default=None, max_length=1000)


class InvoiceCreate(BaseModel):
    vendor_id: int
    invoice_number: str = Field(min_length=1, max_length=60)
    invoice_date: date | None = None
    amount: float = Field(ge=0)
    tax: float = Field(default=0, ge=0)
    remarks: str | None = Field(default=None, max_length=1000)


class InvoiceReview(BaseModel):
    decision: AccountReviewDecision
    remarks: str | None = Field(default=None, max_length=1000)


class InvoiceRevise(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=60)
    invoice_date: date | None = None
    amount: float = Field(ge=0)
    tax: float = Field(default=0, ge=0)
    remarks: str | None = Field(default=None, max_length=1000)


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    vendor_id: int
    invoice_number: str
    invoice_date: date | None = None
    amount: float
    tax: float
    total_amount: float
    status: InvoiceStatus
    version: int
    parent_invoice_id: int | None = None
    remarks: str | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime
