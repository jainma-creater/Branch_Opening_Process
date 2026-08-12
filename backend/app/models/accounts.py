from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InvoiceStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    MISMATCH = "MISMATCH"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    REVISED = "REVISED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"


class AccountReviewDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MISMATCH = "MISMATCH"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    SENT_BACK = "SENT_BACK"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id", ondelete="RESTRICT"), index=True
    )
    invoice_number: Mapped[str] = mapped_column(String(60), index=True)
    invoice_date: Mapped[date | None] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0, server_default="0")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[InvoiceStatus] = mapped_column(
        String(30), default=InvoiceStatus.DRAFT, server_default="DRAFT", index=True
    )
    version: Mapped[int] = mapped_column(default=1, server_default="1")
    parent_invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="SET NULL")
    )
    remarks: Mapped[str | None] = mapped_column(String(1000))
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )