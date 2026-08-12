from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AuditEvent,
    Branch,
    BranchOpening,
    TaskStatus,
    User,
    WorkflowInstance,
    WorkflowStageDefinition,
    WorkflowTask,
)
from app.models.opening import CaseStatus
from app.models.workflow import WorkflowStageStatus
from app.repositories.openings import OpeningRepository
from app.schemas.openings import OpeningAssign, OpeningCreate, OpeningStatusUpdate, OpeningUpdate
from app.utils.case_numbers import next_opening_number


class OpeningService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OpeningRepository(db)

    def create(self, data: OpeningCreate, actor: User) -> BranchOpening:
        branch = self.db.get(Branch, data.branch_id)
        if branch is None:
            raise HTTPException(status_code=422, detail="Branch does not exist")

        for _ in range(3):
            number = next_opening_number(self.db)
            opening = BranchOpening(
                opening_number=number,
                branch_id=data.branch_id,
                project_type=data.project_type,
                business_reason=data.business_reason,
                requested_by=data.requested_by or actor.id,
                requested_date=data.requested_date,
                tentative_operations_date=data.tentative_operations_date,
                agreement_commencement_date=data.agreement_commencement_date,
                current_stage="REQUIREMENT",
                case_status=CaseStatus.ACTIVE,
            )
            self.db.add(opening)
            try:
                self.db.flush()
                break
            except IntegrityError:
                self.db.rollback()
                opening = None

        if opening is None:
            raise HTTPException(status_code=409, detail="Could not allocate case number")

        self._create_stage_instances(opening.id)
        self.db.add(
            AuditEvent(
                branch_opening_id=opening.id,
                entity_type="branch_openings",
                entity_id=str(opening.id),
                action="CASE_CREATED",
                stage="REQUIREMENT",
                user_id=actor.id,
                new_value=opening.opening_number,
                comments="Branch opening case created",
            )
        )
        self.db.commit()
        self.db.refresh(opening)
        return opening

    def _create_stage_instances(self, opening_id: int) -> None:
        stages = list(
            self.db.scalars(
                select(WorkflowStageDefinition)
                .where(WorkflowStageDefinition.is_active.is_(True))
                .order_by(WorkflowStageDefinition.sequence)
            ).all()
        )
        for idx, stage in enumerate(stages):
            instance = WorkflowInstance(
                opening_id=opening_id,
                stage_id=stage.id,
                status=(
                    WorkflowStageStatus.IN_PROGRESS
                    if idx == 0
                    else WorkflowStageStatus.PENDING
                ),
            )
            self.db.add(instance)

    def get(self, opening_id: int) -> BranchOpening:
        opening = self.repo.get(opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        return opening

    def get_by_number(self, number: str) -> BranchOpening:
        opening = self.repo.get_by_number(number)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        return opening

    def list(self, filters: dict) -> list[BranchOpening]:
        return self.repo.list(**filters)

    def update(self, opening_id: int, data: OpeningUpdate) -> BranchOpening:
        opening = self.get(opening_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(opening, field, value)
        return self.repo.save(opening)

    def set_status(
        self, opening_id: int, data: OpeningStatusUpdate, actor: User | None = None
    ) -> BranchOpening:
        opening = self.get(opening_id)
        old = opening.case_status
        opening.case_status = data.case_status
        if data.case_status == CaseStatus.COMPLETED:
            from datetime import datetime, timezone

            opening.completed_at = datetime.now(timezone.utc)
        self.db.add(
            AuditEvent(
                branch_opening_id=opening.id,
                entity_type="branch_openings",
                entity_id=str(opening.id),
                action="CASE_STATUS_CHANGED",
                stage=opening.current_stage,
                user_id=actor.id if actor else None,
                old_value=old,
                new_value=data.case_status,
            )
        )
        return self.repo.save(opening)

    def assign(self, opening_id: int, data: OpeningAssign, actor: User) -> BranchOpening:
        opening = self.get(opening_id)
        user = self.db.get(User, data.assigned_to)
        if user is None:
            raise HTTPException(status_code=422, detail="Assigned user does not exist")
        old = opening.assigned_to
        opening.assigned_to = data.assigned_to
        self.db.add(
            AuditEvent(
                branch_opening_id=opening.id,
                entity_type="branch_openings",
                entity_id=str(opening.id),
                action="CASE_ASSIGNED",
                stage=opening.current_stage,
                user_id=actor.id,
                old_value=str(old) if old else None,
                new_value=str(data.assigned_to),
            )
        )
        return self.repo.save(opening)