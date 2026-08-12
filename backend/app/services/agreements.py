from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Agreement,
    AgreementParty,
    AuditEvent,
    BranchOpening,
    User,
)
from app.models.agreement import AgreementStatus
from app.schemas.agreement import AgreementCreate, AgreementStatusUpdate, AgreementUpdate


class AgreementService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, opening_id: int, data: AgreementCreate, actor: User) -> Agreement:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        agreement = Agreement(
            branch_opening_id=opening_id,
            agreement_date=data.agreement_date,
            start_date=data.start_date,
            end_date=data.end_date,
            tenure=data.tenure,
            monthly_rent=data.monthly_rent,
            annual_increment=data.annual_increment,
            security_deposit=data.security_deposit,
            lock_in=data.lock_in,
            fitout_period=data.fitout_period,
            remarks=data.remarks,
        )
        for party in data.parties:
            agreement.parties.append(
                AgreementParty(
                    party_type=party.party_type,
                    name=party.name,
                    details=party.details,
                    email=party.email,
                    phone=party.phone,
                )
            )
        self.db.add(agreement)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="agreements",
                entity_id=str(agreement.id),
                action="AGREEMENT_CREATED",
                stage=opening.current_stage,
                user_id=actor.id,
            )
        )
        self.db.commit()
        return self.get(agreement.id)

    def get(self, agreement_id: int) -> Agreement:
        agreement = self.db.scalar(
            select(Agreement)
            .options(selectinload(Agreement.parties))
            .where(Agreement.id == agreement_id)
        )
        if agreement is None:
            raise HTTPException(status_code=404, detail="Agreement not found")
        return agreement

    def latest_for_opening(self, opening_id: int) -> Agreement | None:
        return self.db.scalar(
            select(Agreement)
            .where(Agreement.branch_opening_id == opening_id)
            .order_by(Agreement.id.desc())
            .limit(1)
        )

    def list_for_opening(self, opening_id: int) -> list[Agreement]:
        return list(
            self.db.scalars(
                select(Agreement)
                .options(selectinload(Agreement.parties))
                .where(Agreement.branch_opening_id == opening_id)
                .order_by(Agreement.id)
            ).all()
        )

    def update(self, agreement_id: int, data: AgreementUpdate, actor: User) -> Agreement:
        agreement = self.get(agreement_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "remarks":
                continue
            setattr(agreement, field, value)
        if data.remarks:
            agreement.remarks = data.remarks
        self.db.add(
            AuditEvent(
                branch_opening_id=agreement.branch_opening_id,
                entity_type="agreements",
                entity_id=str(agreement.id),
                action="AGREEMENT_UPDATED",
                user_id=actor.id,
            )
        )
        self.db.commit()
        return self.get(agreement_id)

    def set_status(
        self, agreement_id: int, data: AgreementStatusUpdate, actor: User
    ) -> Agreement:
        agreement = self.get(agreement_id)
        old = str(agreement.status)
        agreement.status = data.status
        if data.remarks:
            agreement.remarks = data.remarks
        self.db.add(
            AuditEvent(
                branch_opening_id=agreement.branch_opening_id,
                entity_type="agreements",
                entity_id=str(agreement.id),
                action=f"AGREEMENT_{data.status.value}",
                user_id=actor.id,
                old_value=old,
                new_value=data.status.value,
            )
        )
        self.db.commit()
        return self.get(agreement_id)