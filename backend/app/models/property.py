from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PropertyStatus(StrEnum):
    UNDER_REVIEW = "UNDER_REVIEW"
    UNDER_APPROVAL = "UNDER_APPROVAL"
    SELECTED = "SELECTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NOT_SELECTED = "NOT_SELECTED"
    CANCELLED = "CANCELLED"
    REPLACEMENT = "REPLACEMENT"


class RentLimitResult(StrEnum):
    WITHIN_LIMIT = "WITHIN_LIMIT"
    ABOVE_LIMIT = "ABOVE_LIMIT"


class PropertyOption(Base):
    __tablename__ = "property_options"
    __table_args__ = (
        UniqueConstraint(
            "branch_opening_id", "option_sequence", name="uq_property_option_sequence"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    option_sequence: Mapped[int] = mapped_column(default=1)
    address: Mapped[str] = mapped_column(String(500))
    area_sqft: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    rent: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    deposit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    annual_increment: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    entrance: Mapped[str | None] = mapped_column(String(20))
    restroom: Mapped[str | None] = mapped_column(String(20))
    possession_status: Mapped[str | None] = mapped_column(String(40))
    remarks: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PropertyStatus] = mapped_column(
        String(30), default=PropertyStatus.UNDER_REVIEW, server_default="UNDER_REVIEW", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )