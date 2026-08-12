from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DepositStatus(StrEnum):
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PayeeStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    REJECTED = "REJECTED"


class DepositPaymentStatus(StrEnum):
    PAID = "PAID"
    REVERSED = "REVERSED"


class SecurityDeposit(Base):
    __tablename__ = "security_deposits"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[DepositStatus] = mapped_column(
        String(20), default=DepositStatus.PENDING, server_default="PENDING"
    )
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    payees: Mapped[list["DepositPayee"]] = relationship(
        back_populates="deposit", cascade="all, delete-orphan", order_by="DepositPayee.id"
    )


class DepositPayee(Base):
    __tablename__ = "deposit_payees"

    id: Mapped[int] = mapped_column(primary_key=True)
    deposit_id: Mapped[int] = mapped_column(
        ForeignKey("security_deposits.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[PayeeStatus] = mapped_column(
        String(20), default=PayeeStatus.PENDING, server_default="PENDING"
    )
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    deposit: Mapped[SecurityDeposit] = relationship(back_populates="payees")
    payments: Mapped[list["DepositPayment"]] = relationship(
        back_populates="payee", cascade="all, delete-orphan", order_by="DepositPayment.id"
    )


class DepositPayment(Base):
    __tablename__ = "deposit_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    payee_id: Mapped[int] = mapped_column(
        ForeignKey("deposit_payees.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    payment_date: Mapped[date | None] = mapped_column(Date)
    reference: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[DepositPaymentStatus] = mapped_column(
        String(20), default=DepositPaymentStatus.PAID, server_default="PAID"
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    payee: Mapped[DepositPayee] = relationship(back_populates="payments")


class LOAStatus(StrEnum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    ISSUED = "ISSUED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"


class LOARequest(Base):
    __tablename__ = "loa_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    employee: Mapped[str] = mapped_column(String(200))
    employee_code: Mapped[str] = mapped_column(String(50))
    request_date: Mapped[date | None] = mapped_column(Date)
    execution_date: Mapped[date | None] = mapped_column(Date)
    agreement_tenure: Mapped[str | None] = mapped_column(String(120))
    issued_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[LOAStatus] = mapped_column(
        String(20), default=LOAStatus.REQUESTED, server_default="REQUESTED", index=True
    )
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )