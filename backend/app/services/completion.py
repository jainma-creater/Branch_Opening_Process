from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, BranchOpening, User, Vendor
from app.models.completion import (
    Fitout,
    FitoutStatus,
    OpeningRecord,
    ReadinessItem,
    ReadinessStatus,
)
from app.schemas.completion import (
    FitoutCreate,
    FitoutUpdate,
    OpeningRecordCreate,
    ReadinessItemCreate,
    ReadinessItemUpdate,
)
from app.services.workflow import WorkflowService


class CompletionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.workflow = WorkflowService(db)

    # -- Fit-out -----------------------------------------------------------
    def create_fitout(self, opening_id: int, data: FitoutCreate, actor: User) -> Fitout:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        if data.vendor_id is not None:
            if self.db.get(Vendor, data.vendor_id) is None:
                raise HTTPException(status_code=422, detail="Vendor does not exist")
        fitout = Fitout(
            branch_opening_id=opening_id,
            vendor_id=data.vendor_id,
            scope=data.scope,
            start_date=data.start_date,
            expected_end_date=data.expected_end_date,
            status=FitoutStatus.PLANNED,
            remarks=data.remarks,
        )
        self.db.add(fitout)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="fitouts",
                entity_id=str(fitout.id),
                action="FITOUT_CREATED",
                user_id=actor.id,
            )
        )
        self.db.commit()
        self.db.refresh(fitout)
        return fitout

    def list_fitouts(self, opening_id: int) -> list[Fitout]:
        return list(
            self.db.scalars(
                select(Fitout)
                .where(Fitout.branch_opening_id == opening_id)
                .order_by(Fitout.id)
            ).all()
        )

    def update_fitout(self, fitout_id: int, data: FitoutUpdate, actor: User) -> Fitout:
        fitout = self.db.get(Fitout, fitout_id)
        if fitout is None:
            raise HTTPException(status_code=404, detail="Fitout not found")
        fitout.status = data.status
        fitout.remarks = data.remarks
        if data.status == FitoutStatus.COMPLETED:
            fitout.completion_date = data.completion_date
        self.db.add(fitout)
        self.db.flush()

        if data.status == FitoutStatus.COMPLETED:
            pending = self.db.scalar(
                select(Fitout.id).where(
                    Fitout.branch_opening_id == fitout.branch_opening_id,
                    Fitout.status != FitoutStatus.COMPLETED,
                )
            )
            if pending is None:
                opening = self.db.get(BranchOpening, fitout.branch_opening_id)
                if opening is not None:
                    self.workflow.transition(opening, "OPERATIONAL_READINESS", actor)
        self.db.commit()
        self.db.refresh(fitout)
        return fitout

    # -- Operational readiness --------------------------------------------
    def create_readiness(self, opening_id: int, data: ReadinessItemCreate, actor: User) -> ReadinessItem:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        item = ReadinessItem(
            branch_opening_id=opening_id,
            item_name=data.item_name,
            status=ReadinessStatus.PENDING,
            remarks=data.remarks,
        )
        self.db.add(item)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="readiness_items",
                entity_id=str(item.id),
                action="READINESS_ITEM_CREATED",
                user_id=actor.id,
            )
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_readiness(self, opening_id: int) -> list[ReadinessItem]:
        return list(
            self.db.scalars(
                select(ReadinessItem)
                .where(ReadinessItem.branch_opening_id == opening_id)
                .order_by(ReadinessItem.id)
            ).all()
        )

    def update_readiness(self, item_id: int, data: ReadinessItemUpdate, actor: User) -> ReadinessItem:
        item = self.db.get(ReadinessItem, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Readiness item not found")
        item.status = data.status
        item.remarks = data.remarks
        self.db.add(item)
        self.db.flush()

        if data.status == ReadinessStatus.DONE:
            pending = self.db.scalar(
                select(ReadinessItem.id).where(
                    ReadinessItem.branch_opening_id == item.branch_opening_id,
                    ReadinessItem.status == ReadinessStatus.PENDING,
                )
            )
            if pending is None:
                opening = self.db.get(BranchOpening, item.branch_opening_id)
                if opening is not None:
                    self.workflow.transition(opening, "OPENING", actor)
        self.db.commit()
        self.db.refresh(item)
        return item

    # -- Opening / completion ---------------------------------------------
    def create_opening_record(self, opening_id: int, data: OpeningRecordCreate, actor: User) -> OpeningRecord:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        existing = self.db.scalar(
            select(OpeningRecord).where(OpeningRecord.branch_opening_id == opening_id)
        )
        if existing is not None:
            raise HTTPException(status_code=409, detail="Opening record already exists")
        record = OpeningRecord(
            branch_opening_id=opening_id,
            opening_date=data.opening_date,
            inaugurated_by=data.inaugurated_by,
            remarks=data.remarks,
        )
        self.db.add(record)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="opening_records",
                entity_id=str(record.id),
                action="OPENING_RECORD_CREATED",
                user_id=actor.id,
            )
        )
        self.workflow.transition(opening, "COMPLETED", actor)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_opening_record(self, opening_id: int) -> OpeningRecord:
        record = self.db.scalar(
            select(OpeningRecord).where(OpeningRecord.branch_opening_id == opening_id)
        )
        if record is None:
            raise HTTPException(status_code=404, detail="Opening record not found")
        return record
