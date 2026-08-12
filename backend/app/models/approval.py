from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApprovalDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT_BACK = "SENT_BACK"
    MISMATCH = "MISMATCH"
    REVISION_REQUIRED = "REVISION_REQUIRED"


class ApprovalType(StrEnum):
    PROPERTY = "PROPERTY"
    SECURITY_DEPOSIT = "SECURITY_DEPOSIT"
    LOA = "LOA"
    AGREEMENT = "AGREEMENT"
    QUOTATION = "QUOTATION"
    ACCOUNTS = "ACCOUNTS"
    INVOICE = "INVOICE"
    CC = "CC"
    MD = "MD"
    PAYMENT = "PAYMENT"


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (
        Index("ix_approvals_opening_type", "branch_opening_id", "approval_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str | None] = mapped_column(String(64), index=True)
    approval_type: Mapped[ApprovalType] = mapped_column(String(40), index=True)
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approver: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    decision: Mapped[ApprovalDecision | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    comments: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))