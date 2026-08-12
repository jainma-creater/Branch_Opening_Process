"""Workflow engine: stage transitions, send-back, task generation."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditEvent,
    BranchOpening,
    TaskStatus,
    User,
    WorkflowInstance,
    WorkflowStageDefinition,
    WorkflowTask,
)
from app.models.workflow import WorkflowStageStatus
from app.workflow.tasks import TASK_TEMPLATES
from app.workflow.transitions import is_allowed, previous_stage, can_role_advance

CONFLICT = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Transition is not defined for the current stage",
)


class WorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _instance_for_stage(self, opening_id: int, stage_code: str) -> WorkflowInstance | None:
        return self.db.scalar(
            select(WorkflowInstance)
            .join(WorkflowStageDefinition, WorkflowInstance.stage_id == WorkflowStageDefinition.id)
            .where(
                WorkflowInstance.opening_id == opening_id,
                WorkflowStageDefinition.code == stage_code,
            )
        )

    def _stage_definition(self, code: str) -> WorkflowStageDefinition:
        stage = self.db.scalar(
            select(WorkflowStageDefinition).where(WorkflowStageDefinition.code == code)
        )
        if stage is None:
            raise HTTPException(status_code=500, detail="Stage definition missing")
        return stage

    def start_stage(self, opening_id: int, stage_code: str) -> None:
        instance = self._instance_for_stage(opening_id, stage_code)
        if instance and instance.status == WorkflowStageStatus.PENDING:
            instance.status = WorkflowStageStatus.IN_PROGRESS
            instance.started_at = datetime.now(timezone.utc)
            self.db.add(instance)

    def _close_stage(self, opening_id: int, stage_code: str, final_status: WorkflowStageStatus) -> None:
        instance = self._instance_for_stage(opening_id, stage_code)
        if instance is None:
            return
        instance.status = final_status
        if final_status in (
            WorkflowStageStatus.COMPLETED,
            WorkflowStageStatus.APPROVED,
        ):
            instance.completed_at = datetime.now(timezone.utc)
        self.db.add(instance)

    def _generate_tasks(self, opening_id: int, stage_code: str, actor: User) -> list[WorkflowTask]:
        created = []
        for task_type in TASK_TEMPLATES.get(stage_code, []):
            task = WorkflowTask(
                branch_opening_id=opening_id,
                stage=stage_code,
                task_type=task_type,
                assigned_to=actor.id,
                status=TaskStatus.PENDING,
            )
            self.db.add(task)
            created.append(task)
        return created

    def transition(self, opening: BranchOpening, target: str, actor: User, comments: str | None = None) -> BranchOpening:
        current = opening.current_stage
        if not is_allowed(current, target):
            raise CONFLICT
        role = actor.role.name if actor.role else ""
        if not can_role_advance(role, target):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role cannot advance the case to this stage",
            )

        self._close_stage(opening.id, current, WorkflowStageStatus.COMPLETED)
        self.start_stage(opening.id, target)
        opening.current_stage = target
        self._generate_tasks(opening.id, target, actor)
        if target == "COMPLETED":
            from datetime import datetime as dt

            opening.completed_at = dt.now(timezone.utc)
            from app.models.opening import CaseStatus

            opening.case_status = CaseStatus.COMPLETED
            self._close_stage(opening.id, target, WorkflowStageStatus.COMPLETED)

        self.db.add(
            AuditEvent(
                branch_opening_id=opening.id,
                entity_type="branch_openings",
                entity_id=str(opening.id),
                action="STAGE_ADVANCED",
                stage=current,
                user_id=actor.id,
                old_value=current,
                new_value=target,
                comments=comments,
            )
        )
        self.db.commit()
        self.db.refresh(opening)
        return opening

    def send_back(self, opening: BranchOpening, actor: User, comments: str | None = None) -> BranchOpening:
        current = opening.current_stage
        previous = previous_stage(current)
        if previous is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No previous stage to send back to",
            )
        role = actor.role.name if actor.role else ""
        from app.workflow.transitions import STAGE_APPROVER

        if not (
            can_role_advance(role, current)
            or role in ("ADMIN", "SUPER_ADMIN")
            or role == STAGE_APPROVER.get(current)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role cannot send this case back",
            )

        self._close_stage(opening.id, current, WorkflowStageStatus.SENT_BACK)
        self.start_stage(opening.id, previous)
        opening.current_stage = previous
        self._generate_tasks(opening.id, previous, actor)

        self.db.add(
            AuditEvent(
                branch_opening_id=opening.id,
                entity_type="branch_openings",
                entity_id=str(opening.id),
                action="STAGE_SENT_BACK",
                stage=current,
                user_id=actor.id,
                old_value=current,
                new_value=previous,
                comments=comments,
            )
        )
        self.db.commit()
        self.db.refresh(opening)
        return opening

    def available_targets(self, opening: BranchOpening) -> list[str]:
        from app.workflow.transitions import TRANSITIONS

        return list(TRANSITIONS.get(opening.current_stage, []))

    def task_list(self, opening_id: int) -> list[WorkflowTask]:
        return list(
            self.db.scalars(
                select(WorkflowTask)
                .where(WorkflowTask.branch_opening_id == opening_id)
                .order_by(WorkflowTask.id)
            ).all()
        )

    def start_task(self, task_id: int, actor: User) -> WorkflowTask:
        task = self.db.get(WorkflowTask, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.assigned_to and task.assigned_to != actor.id:
            raise HTTPException(status_code=403, detail="Task is assigned to another user")
        task.status = TaskStatus.IN_PROGRESS
        self.db.commit()
        self.db.refresh(task)
        return task

    def complete_task(self, task_id: int, actor: User, remarks: str | None = None) -> WorkflowTask:
        task = self.db.get(WorkflowTask, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.assigned_to and task.assigned_to != actor.id:
            raise HTTPException(status_code=403, detail="Task is assigned to another user")
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.completed_by = actor.id
        task.remarks = remarks
        opening = self.db.get(BranchOpening, task.branch_opening_id)
        if opening is not None:
            self.db.add(
                AuditEvent(
                    branch_opening_id=opening.id,
                    entity_type="workflow_tasks",
                    entity_id=str(task.id),
                    action="TASK_COMPLETED",
                    stage=task.stage,
                    user_id=actor.id,
                    new_value=task.task_type,
                    comments=remarks,
                )
            )
        self.db.commit()
        self.db.refresh(task)
        return task

    def my_tasks(self, actor: User, status_filter: str | None = None) -> list[WorkflowTask]:
        stmt = select(WorkflowTask).where(
            WorkflowTask.assigned_to == actor.id,
            WorkflowTask.status.in_(
                [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]
            ),
        )
        if status_filter:
            stmt = stmt.where(WorkflowTask.status == status_filter)
        return list(self.db.scalars(stmt.order_by(WorkflowTask.id)).all())