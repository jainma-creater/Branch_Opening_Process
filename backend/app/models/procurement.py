from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ItemCategory(StrEnum):
    FIXED_ASSETS = "FIXED_ASSETS"
    COMPLIANCE_ASSETS = "COMPLIANCE_ASSETS"
    RENOVATION = "RENOVATION"
    ELECTRICAL = "ELECTRICAL"
    TRANSPORTATION = "TRANSPORTATION"
    OTHER = "OTHER"


class QuotationRequestStatus(StrEnum):
    OPEN = "OPEN"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class QuotationStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    contact_person: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    quotations: Mapped[list["Quotation"]] = relationship(back_populates="vendor")


class QuotationRequest(Base):
    __tablename__ = "quotation_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    request_date: Mapped[date | None] = mapped_column(Date)
    required_date: Mapped[date | None] = mapped_column(Date)
    scope_description: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[QuotationRequestStatus] = mapped_column(
        String(30), default=QuotationRequestStatus.OPEN, server_default="OPEN"
    )
    selected_vendor_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendors.id", ondelete="RESTRICT")
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["QuotationRequestItem"]] = relationship(
        back_populates="request", cascade="all, delete-orphan", order_by="QuotationRequestItem.id"
    )
    quotations: Mapped[list["Quotation"]] = relationship(
        back_populates="request", cascade="all, delete-orphan", order_by="Quotation.id"
    )


class QuotationRequestItem(Base):
    __tablename__ = "quotation_request_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("quotation_requests.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[ItemCategory] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=1, server_default="1")
    unit: Mapped[str | None] = mapped_column(String(30))

    request: Mapped[QuotationRequest] = relationship(back_populates="items")


class Quotation(Base):
    __tablename__ = "quotations"
    __table_args__ = (
        UniqueConstraint("request_id", "vendor_id", name="uq_quotation_request_vendor"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("quotation_requests.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id", ondelete="RESTRICT"), index=True
    )
    quotation_date: Mapped[date | None] = mapped_column(Date)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), server_default="0"
    )
    status: Mapped[QuotationStatus] = mapped_column(
        String(30), default=QuotationStatus.SUBMITTED, server_default="SUBMITTED"
    )
    remarks: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    request: Mapped[QuotationRequest] = relationship(back_populates="quotations")
    vendor: Mapped[Vendor] = relationship(back_populates="quotations")
    items: Mapped[list["QuotationItem"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan", order_by="QuotationItem.id"
    )


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[ItemCategory] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=1, server_default="1")
    unit: Mapped[str | None] = mapped_column(String(30))
    rate: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, server_default="0")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, server_default="0")
    tax: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0, server_default="0")
    final_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, server_default="0")

    quotation: Mapped[Quotation] = relationship(back_populates="items")