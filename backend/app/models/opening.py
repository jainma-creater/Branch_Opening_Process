from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CaseStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkflowStage(StrEnum):
    REQUIREMENT = "REQUIREMENT"
    PROPERTY_SEARCH = "PROPERTY_SEARCH"
    PROPERTY_APPROVAL = "PROPERTY_APPROVAL"
    SECURITY_DEPOSIT = "SECURITY_DEPOSIT"
    LOA = "LOA"
    AGREEMENT = "AGREEMENT"
    QUOTATION = "QUOTATION"
    ACCOUNTS = "ACCOUNTS"
    CC_APPROVAL = "CC_APPROVAL"
    MD_APPROVAL = "MD_APPROVAL"
    PAYMENT = "PAYMENT"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    OPERATIONAL_READINESS = "OPERATIONAL_READINESS"
    OPENING = "OPENING"
    COMPLETED = "COMPLETED"


class BranchOpening(Base):
    __tablename__ = "branch_openings"

    id: Mapped[int] = mapped_column(primary_key=True)
    opening_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"), index=True)
    project_type: Mapped[str] = mapped_column(String(30))
    business_reason: Mapped[str | None] = mapped_column(String(500))
    requested_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    requested_date: Mapped[date] = mapped_column(Date)
    tentative_operations_date: Mapped[date | None] = mapped_column(Date)
    agreement_commencement_date: Mapped[date | None] = mapped_column(Date)
    actual_opening_date: Mapped[date | None] = mapped_column(Date)
    current_stage: Mapped[WorkflowStage] = mapped_column(String(40), default=WorkflowStage.REQUIREMENT, index=True)
    case_status: Mapped[CaseStatus] = mapped_column(String(20), default=CaseStatus.DRAFT, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    branch: Mapped["Branch"] = relationship(back_populates="openings")
    workflow_instances: Mapped[list["WorkflowInstance"]] = relationship(
        back_populates="opening", cascade="all, delete-orphan"
    )
