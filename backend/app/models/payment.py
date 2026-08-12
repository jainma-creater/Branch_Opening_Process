from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentMode(StrEnum):
    NEFT = "NEFT"
    RTGS = "RTGS"
    CHEQUE = "CHEQUE"
    CASH = "CASH"
    UPI = "UPI"


class PaymentStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="RESTRICT")
    )
    vendor_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendors.id", ondelete="RESTRICT")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    mode: Mapped[PaymentMode] = mapped_column(String(20), default=PaymentMode.NEFT)
    reference_no: Mapped[str | None] = mapped_column(String(120))
    payment_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[PaymentStatus] = mapped_column(
        String(20), default=PaymentStatus.DRAFT, server_default="DRAFT", index=True
    )
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    remarks: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
