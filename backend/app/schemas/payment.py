from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMode, PaymentStatus


class PaymentCreate(BaseModel):
    invoice_id: int | None = None
    vendor_id: int | None = None
    amount: float = Field(ge=0)
    mode: PaymentMode = PaymentMode.NEFT
    reference_no: str | None = Field(default=None, max_length=120)
    payment_date: date | None = None
    remarks: str | None = Field(default=None, max_length=1000)


class PaymentReview(BaseModel):
    decision: str  # APPROVED | REJECTED
    comments: str | None = Field(default=None, max_length=1000)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    invoice_id: int | None = None
    vendor_id: int | None = None
    amount: float
    mode: PaymentMode
    reference_no: str | None = None
    payment_date: date | None = None
    status: PaymentStatus
    requested_by: int | None = None
    approved_by: int | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime
