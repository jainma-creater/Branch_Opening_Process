from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Branch, BranchOpening, User


class OpeningRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, opening_id: int) -> BranchOpening | None:
        return self.db.scalar(
            select(BranchOpening)
            .options(selectinload(BranchOpening.branch), selectinload(BranchOpening.workflow_instances))
            .where(BranchOpening.id == opening_id)
        )

    def get_by_number(self, number: str) -> BranchOpening | None:
        return self.db.scalar(
            select(BranchOpening).where(BranchOpening.opening_number == number)
        )

    def add(self, opening: BranchOpening) -> BranchOpening:
        self.db.add(opening)
        self.db.commit()
        self.db.refresh(opening)
        return opening

    def save(self, opening: BranchOpening) -> BranchOpening:
        self.db.commit()
        self.db.refresh(opening)
        return opening

    def list(
        self,
        *,
        region_id: int | None = None,
        area_id: int | None = None,
        branch_id: int | None = None,
        case_status: str | None = None,
        current_stage: str | None = None,
        requested_by: int | None = None,
        assigned_to: int | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BranchOpening]:
        stmt = select(BranchOpening).options(
            selectinload(BranchOpening.branch)
        )
        if branch_id is not None:
            stmt = stmt.where(BranchOpening.branch_id == branch_id)
        if area_id is not None or region_id is not None:
            from app.models import Area

            stmt = stmt.join(Branch, BranchOpening.branch_id == Branch.id)
            if area_id is not None:
                stmt = stmt.where(Branch.area_id == area_id)
            if region_id is not None:
                stmt = stmt.join(Area, Branch.area_id == Area.id).where(
                    Area.region_id == region_id
                )
        if case_status:
            stmt = stmt.where(BranchOpening.case_status == case_status)
        if current_stage:
            stmt = stmt.where(BranchOpening.current_stage == current_stage)
        if requested_by is not None:
            stmt = stmt.where(BranchOpening.requested_by == requested_by)
        if assigned_to is not None:
            stmt = stmt.where(BranchOpening.assigned_to == assigned_to)
        if search:
            stmt = stmt.where(BranchOpening.opening_number.ilike(f"%{search}%"))
        stmt = stmt.order_by(BranchOpening.id.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(stmt).all())

    def count(self, **filters) -> int:
        return len(self.list(**filters))