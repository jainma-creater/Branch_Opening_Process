from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CCRequestStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CC_APPROVED = "CC_APPROVED"
    MD_APPROVED = "MD_APPROVED"
    REJECTED = "REJECTED"
    SENT_BACK = "SENT_BACK"


class CCRequest(Base):
    __tablename__ = "cc_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_code: Mapped[str | None] = mapped_column(String(60), unique=True, index=True)
    status: Mapped[CCRequestStatus] = mapped_column(
        String(30), default=CCRequestStatus.DRAFT, server_default="DRAFT", index=True
    )
    requested_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    cc_reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    md_reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    remarks: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["CCRequestItem"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="CCRequestItem.id",
    )


class CCRequestItem(Base):
    __tablename__ = "cc_request_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    cc_request_id: Mapped[int] = mapped_column(
        ForeignKey("cc_requests.id", ondelete="CASCADE"), index=True
    )
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    remarks: Mapped[str | None] = mapped_column(String(500))

    request: Mapped[CCRequest] = relationship(back_populates="items")
