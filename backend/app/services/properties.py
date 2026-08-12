from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditEvent, BranchOpening, PropertyOption, User
from app.models.approval import ApprovalType
from app.models.property import PropertyStatus, RentLimitResult
from app.schemas.properties import (
    PropertyCancel,
    PropertyCreate,
    PropertyStatusUpdate,
    PropertyUpdate,
)
from app.services.approvals import ApprovalService


class PropertyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.approvals = ApprovalService(db)

    def _next_sequence(self, opening_id: int) -> int:
        current = self.db.scalar(
            select(func.max(PropertyOption.option_sequence)).where(
                PropertyOption.branch_opening_id == opening_id
            )
        )
        return (current or 0) + 1

    def create(
        self, opening_id: int, data: PropertyCreate, actor: User
    ) -> PropertyOption:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")

        sequence = self._next_sequence(opening_id)
        has_cancelled = self.db.scalar(
            select(PropertyOption.id)
            .where(
                PropertyOption.branch_opening_id == opening_id,
                PropertyOption.status == PropertyStatus.CANCELLED,
            )
            .limit(1)
        )
        status_value = (
            PropertyStatus.REPLACEMENT if (has_cancelled and data.status == PropertyStatus.UNDER_REVIEW) else data.status
        )

        option = PropertyOption(
            branch_opening_id=opening_id,
            option_sequence=sequence,
            address=data.address,
            area_sqft=data.area_sqft,
            rent=data.rent,
            deposit=data.deposit,
            annual_increment=data.annual_increment,
            entrance=data.entrance,
            restroom=data.restroom,
            possession_status=data.possession_status,
            remarks=data.remarks,
            status=status_value,
        )
        self.db.add(option)
        self.db.flush()

        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="property_options",
                entity_id=str(option.id),
                action="PROPERTY_ADDED",
                stage=opening.current_stage,
                user_id=actor.id,
                new_value=f"option {sequence}",
                comments=data.remarks,
            )
        )
        self.db.commit()
        self.db.refresh(option)
        return option

    def get(self, property_id: int) -> PropertyOption:
        option = self.db.get(PropertyOption, property_id)
        if option is None:
            raise HTTPException(status_code=404, detail="Property not found")
        return option

    def list_for_opening(self, opening_id: int) -> list[PropertyOption]:
        return list(
            self.db.scalars(
                select(PropertyOption)
                .where(PropertyOption.branch_opening_id == opening_id)
                .order_by(PropertyOption.option_sequence)
            ).all()
        )

    def update(self, property_id: int, data: PropertyUpdate, actor: User) -> PropertyOption:
        option = self.get(property_id)
        old_status = option.status
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(option, field, value)
        if data.status is not None and data.status != old_status:
            self._record_status_change(option, old_status, actor)
        self.db.commit()
        self.db.refresh(option)
        return option

    def set_status(
        self, property_id: int, data: PropertyStatusUpdate, actor: User
    ) -> PropertyOption:
        option = self.get(property_id)
        old_status = option.status
        option.status = data.status
        if data.remarks:
            option.remarks = data.remarks
        self._record_status_change(option, old_status, actor)
        self.db.commit()
        self.db.refresh(option)
        return option

    def cancel(self, property_id: int, data: PropertyCancel, actor: User) -> PropertyOption:
        option = self.get(property_id)
        if option.status == PropertyStatus.CANCELLED:
            return option
        old_status = option.status
        option.status = PropertyStatus.CANCELLED
        if data.remarks:
            option.remarks = data.remarks
        self._record_status_change(option, old_status, actor)
        self.db.commit()
        self.db.refresh(option)
        return option

    def request_approval(
        self, property_id: int, actor: User, amount: float | None = None, comments: str | None = None
    ) -> PropertyOption:
        option = self.get(property_id)
        if option.status == PropertyStatus.CANCELLED:
            raise HTTPException(status_code=409, detail="Cancelled property cannot be approved")
        if option.status != PropertyStatus.APPROVED:
            old_status = option.status
            option.status = PropertyStatus.UNDER_APPROVAL
            self._record_status_change(option, old_status, actor)
            self.db.commit()
            self.db.refresh(option)
        self.approvals.request(
            opening_id=option.branch_opening_id,
            entity_type="property_options",
            entity_id=str(option.id),
            approval_type=ApprovalType.PROPERTY,
            requested_by=actor,
            amount=amount or option.rent,
            comments=comments,
        )
        return option

    def approve(self, property_id: int, actor: User, comments: str | None = None) -> PropertyOption:
        option = self.get(property_id)
        old_status = option.status
        option.status = PropertyStatus.APPROVED
        self._record_status_change(option, old_status, actor)
        self.approvals.request(
            opening_id=option.branch_opening_id,
            entity_type="property_options",
            entity_id=str(option.id),
            approval_type=ApprovalType.PROPERTY,
            requested_by=actor,
            amount=option.rent,
            comments=comments,
        )
        self.db.commit()
        self.db.refresh(option)
        return option

    def rent_limit_check(self, option: PropertyOption) -> tuple[Decimal | None, str | None]:
        """Applicable limit: branch -> area -> region (most specific first)."""
        opening = self.db.get(BranchOpening, option.branch_opening_id)
        if opening is None or option.rent is None:
            return None, None
        branch = opening.branch
        limit = branch.rent_limit or (branch.area.rent_limit if branch.area else None) or (
            branch.area.region.rent_limit if branch.area and branch.area.region else None
        )
        if limit is None:
            return None, None
        result = RentLimitResult.WITHIN_LIMIT if option.rent <= limit else RentLimitResult.ABOVE_LIMIT
        return limit, result.value

    def _record_status_change(self, option: PropertyOption, old_status, actor: User) -> None:
        self.db.add(
            AuditEvent(
                branch_opening_id=option.branch_opening_id,
                entity_type="property_options",
                entity_id=str(option.id),
                action="PROPERTY_STATUS_CHANGED",
                user_id=actor.id,
                old_value=old_status.value if hasattr(old_status, "value") else old_status,
                new_value=option.status.value,
                comments=f"Option {option.option_sequence}",
            )
        )