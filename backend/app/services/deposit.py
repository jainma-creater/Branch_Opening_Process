from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AuditEvent,
    BranchOpening,
    DepositPayment,
    DepositPayee,
    LOARequest,
    SecurityDeposit,
    User,
)
from app.models.deposit import (
    DepositPaymentStatus,
    DepositStatus,
    LOAStatus,
    PayeeStatus,
)
from app.schemas.deposit import (
    DepositCreate,
    DepositPayeeCreate,
    DepositPaymentCreate,
    LOARequestCreate,
    LOARequestUpdate,
)

LOA_NEXT: dict[str, str] = {
    LOAStatus.REQUESTED.value: LOAStatus.APPROVED.value,
    LOAStatus.APPROVED.value: LOAStatus.ISSUED.value,
    LOAStatus.ISSUED.value: LOAStatus.EXECUTED.value,
}


class DepositService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, opening_id: int, data: DepositCreate, actor: User) -> SecurityDeposit:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        deposit = SecurityDeposit(
            branch_opening_id=opening_id,
            total_amount=data.total_amount,
            remarks=data.remarks,
        )
        self.db.add(deposit)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="security_deposits",
                entity_id=str(deposit.id),
                action="DEPOSIT_CREATED",
                stage=opening.current_stage,
                user_id=actor.id,
                new_value=str(data.total_amount),
            )
        )
        self.db.commit()
        self.db.refresh(deposit)
        return deposit

    def get(self, deposit_id: int) -> SecurityDeposit:
        deposit = self.db.scalar(
            select(SecurityDeposit)
            .options(
                selectinload(SecurityDeposit.payees).selectinload(DepositPayee.payments)
            )
            .where(SecurityDeposit.id == deposit_id)
        )
        if deposit is None:
            raise HTTPException(status_code=404, detail="Deposit not found")
        return deposit

    def list_for_opening(self, opening_id: int) -> list[SecurityDeposit]:
        return list(
            self.db.scalars(
                select(SecurityDeposit)
                .where(SecurityDeposit.branch_opening_id == opening_id)
                .order_by(SecurityDeposit.id)
            ).all()
        )

    def add_payee(
        self, deposit_id: int, data: DepositPayeeCreate, actor: User
    ) -> DepositPayee:
        deposit = self.get(deposit_id)
        if deposit.status == DepositStatus.CANCELLED:
            raise HTTPException(status_code=409, detail="Deposit is cancelled")
        allocated = self.db.scalar(
            select(func.coalesce(func.sum(DepositPayee.amount), 0)).where(
                DepositPayee.deposit_id == deposit_id
            )
        )
        if (allocated or Decimal(0)) + Decimal(str(data.amount)) > deposit.total_amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payee allocation exceeds deposit total",
            )
        payee = DepositPayee(
            deposit_id=deposit_id,
            name=data.name,
            amount=data.amount,
            remarks=data.remarks,
        )
        self.db.add(payee)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=deposit.branch_opening_id,
                entity_type="deposit_payees",
                entity_id=str(payee.id),
                action="DEPOSIT_PAYEE_ADDED",
                user_id=actor.id,
                new_value=f"{data.name}: {data.amount}",
            )
        )
        self.db.commit()
        self.db.refresh(payee)
        return payee

    def record_payment(
        self, payee_id: int, data: DepositPaymentCreate, actor: User
    ) -> DepositPayment:
        payee = self.db.get(DepositPayee, payee_id)
        if payee is None:
            raise HTTPException(status_code=404, detail="Payee not found")
        paid = self.db.scalar(
            select(func.coalesce(func.sum(DepositPayment.amount), 0)).where(
                DepositPayment.payee_id == payee_id,
                DepositPayment.status == DepositPaymentStatus.PAID.value,
            )
        )
        if (paid or Decimal(0)) + Decimal(str(data.amount)) > payee.amount:
            raise HTTPException(
                status_code=409,
                detail="Payment exceeds payee amount",
            )

        payment = DepositPayment(
            payee_id=payee_id,
            amount=data.amount,
            payment_date=data.payment_date or date.today(),
            reference=data.reference,
            status=DepositPaymentStatus.PAID,
            created_by=actor.id,
        )
        self.db.add(payment)

        total_paid = (paid or Decimal(0)) + Decimal(str(data.amount))
        payee.status = PayeeStatus.PAID if total_paid >= payee.amount else PayeeStatus.APPROVED
        self.db.flush()

        deposit = self.db.get(SecurityDeposit, payee.deposit_id)
        deposit_paid = self._deposit_paid_total(deposit.id)
        if deposit_paid >= deposit.total_amount:
            deposit.status = DepositStatus.PAID
        elif deposit_paid > 0:
            deposit.status = DepositStatus.PARTIALLY_PAID

        self.db.add(
            AuditEvent(
                branch_opening_id=deposit.branch_opening_id,
                entity_type="deposit_payments",
                entity_id=str(payment.id),
                action="DEPOSIT_PAYMENT_RECORDED",
                user_id=actor.id,
                new_value=str(data.amount),
                comments=data.reference,
            )
        )
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def _deposit_paid_total(self, deposit_id: int) -> Decimal:
        return self.db.scalar(
            select(func.coalesce(func.sum(DepositPayment.amount), 0))
            .join(DepositPayee, DepositPayment.payee_id == DepositPayee.id)
            .where(
                DepositPayee.deposit_id == deposit_id,
                DepositPayment.status == DepositPaymentStatus.PAID.value,
            )
        ) or Decimal(0)


class LOAService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, opening_id: int, data: LOARequestCreate) -> LOARequest:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        loa = LOARequest(
            branch_opening_id=opening_id,
            employee=data.employee,
            employee_code=data.employee_code,
            request_date=data.request_date or date.today(),
            execution_date=data.execution_date,
            agreement_tenure=data.agreement_tenure,
            remarks=data.remarks,
        )
        self.db.add(loa)
        self.db.commit()
        self.db.refresh(loa)
        return loa

    def get(self, loa_id: int) -> LOARequest:
        loa = self.db.get(LOARequest, loa_id)
        if loa is None:
            raise HTTPException(status_code=404, detail="LOA not found")
        return loa

    def latest_for_opening(self, opening_id: int) -> LOARequest | None:
        return self.db.scalar(
            select(LOARequest)
            .where(LOARequest.branch_opening_id == opening_id)
            .order_by(LOARequest.id.desc())
            .limit(1)
        )

    def update(self, loa_id: int, data: LOARequestUpdate, actor: User) -> LOARequest:
        loa = self.get(loa_id)
        new_status = data.status
        current = str(loa.status)
        if new_status == LOAStatus.REJECTED or new_status == current or (
            LOA_NEXT.get(current) == new_status.value
        ):
            loa.status = new_status
        else:
            allowed = LOA_NEXT.get(current)
            raise HTTPException(
                status_code=409,
                detail=f"Invalid LOA transition from {current} to {new_status.value}"
                + (f"; expected {allowed}" if allowed else ""),
            )
        if data.issued_date:
            loa.issued_date = data.issued_date
        if data.execution_date:
            loa.execution_date = data.execution_date
        if data.remarks:
            loa.remarks = data.remarks
        if new_status == LOAStatus.ISSUED and loa.issued_date is None:
            loa.issued_date = date.today()
        self.db.add(
            AuditEvent(
                branch_opening_id=loa.branch_opening_id,
                entity_type="loa_requests",
                entity_id=str(loa.id),
                action=f"LOA_{new_status.value}",
                user_id=actor.id,
                new_value=new_status.value,
            )
        )
        self.db.commit()
        self.db.refresh(loa)
        return loa