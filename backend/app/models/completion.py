from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FitoutStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class ReadinessStatus(StrEnum):
    PENDING = "PENDING"
    DONE = "DONE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Fitout(Base):
    __tablename__ = "fitouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendors.id", ondelete="RESTRICT")
    )
    scope: Mapped[str] = mapped_column(String(500))
    status: Mapped[FitoutStatus] = mapped_column(
        String(20), default=FitoutStatus.PLANNED, server_default="PLANNED", index=True
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    expected_end_date: Mapped[date | None] = mapped_column(Date)
    completion_date: Mapped[date | None] = mapped_column(Date)
    remarks: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ReadinessItem(Base):
    __tablename__ = "readiness_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    item_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[ReadinessStatus] = mapped_column(
        String(20), default=ReadinessStatus.PENDING, server_default="PENDING", index=True
    )
    remarks: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OpeningRecord(Base):
    __tablename__ = "opening_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), unique=True, index=True
    )
    opening_date: Mapped[date | None] = mapped_column(Date)
    inaugurated_by: Mapped[str | None] = mapped_column(String(200))
    remarks: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
