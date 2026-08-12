from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkflowStageStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT_BACK = "SENT_BACK"
    COMPLETED = "COMPLETED"


class WorkflowStageDefinition(Base):
    __tablename__ = "workflow_stage_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    sequence: Mapped[int] = mapped_column(index=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    instances: Mapped[list["WorkflowInstance"]] = relationship(back_populates="stage")


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"
    __table_args__ = (
        Index("ix_workflow_opening_stage", "opening_id", "stage_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    opening_id: Mapped[int] = mapped_column(ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("workflow_stage_definitions.id", ondelete="RESTRICT"), index=True)
    status: Mapped[WorkflowStageStatus] = mapped_column(String(20), default=WorkflowStageStatus.PENDING, index=True)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    opening: Mapped["BranchOpening"] = relationship(back_populates="workflow_instances")
    stage: Mapped[WorkflowStageDefinition] = relationship(back_populates="instances")


from app.models.opening import BranchOpening  # noqa: E402, F401
