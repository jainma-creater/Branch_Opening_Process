from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgreementStatus(StrEnum):
    DRAFT = "DRAFT"
    UNDER_EXECUTION = "UNDER_EXECUTION"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


class PartyType(StrEnum):
    LICENSOR = "LICENSOR"
    LICENSEE = "LICENSEE"


class Agreement(Base):
    __tablename__ = "agreements"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    agreement_date: Mapped[date | None] = mapped_column(Date)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    tenure: Mapped[str | None] = mapped_column(String(120))
    monthly_rent: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    annual_increment: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    security_deposit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    lock_in: Mapped[str | None] = mapped_column(String(120))
    fitout_period: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[AgreementStatus] = mapped_column(
        String(20), default=AgreementStatus.DRAFT, server_default="DRAFT", index=True
    )
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parties: Mapped[list["AgreementParty"]] = relationship(
        back_populates="agreement", cascade="all, delete-orphan", order_by="AgreementParty.id"
    )


class AgreementParty(Base):
    __tablename__ = "agreement_parties"

    id: Mapped[int] = mapped_column(primary_key=True)
    agreement_id: Mapped[int] = mapped_column(
        ForeignKey("agreements.id", ondelete="CASCADE"), index=True
    )
    party_type: Mapped[PartyType] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    details: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))

    agreement: Mapped[Agreement] = relationship(back_populates="parties")