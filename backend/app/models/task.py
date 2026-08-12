from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"
    __table_args__ = (
        Index("ix_workflow_tasks_opening_status", "branch_opening_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_opening_id: Mapped[int] = mapped_column(
        ForeignKey("branch_openings.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(String(40), index=True)
    task_type: Mapped[str] = mapped_column(String(80))
    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        String(20), default=TaskStatus.PENDING, server_default="PENDING", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    remarks: Mapped[str | None] = mapped_column(Text)