from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import DepositPayment, DepositPayee, User
from app.models.roles import RoleCode
from app.schemas.deposit import (
    DepositCreate,
    DepositPayeeCreate,
    DepositPaymentCreate,
    DepositRead,
    DepositPaymentRead,
    PayeeRead,
)
from app.services.deposit import DepositService

router = APIRouter(prefix="/deposits", tags=["Security Deposits"])

MANAGERS = (
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.SD.value,
    RoleCode.ACCOUNTS.value,
)


def _payee_read(payee: DepositPayee, db: Session) -> PayeeRead:
    paid = sum(float(p.amount) for p in payee.payments if p.status == "PAID")
    return PayeeRead(
        id=payee.id,
        name=payee.name,
        amount=payee.amount,
        status=payee.status,
        paid_amount=paid,
        remarks=payee.remarks,
    )


def _deposit_read(deposit, db: Session) -> DepositRead:
    paid = sum(
        float(p.amount)
        for payee in deposit.payees
        for p in payee.payments
        if p.status == "PAID"
    )
    return DepositRead(
        id=deposit.id,
        branch_opening_id=deposit.branch_opening_id,
        total_amount=deposit.total_amount,
        status=deposit.status,
        paid_amount=paid,
        remarks=deposit.remarks,
        payees=[_payee_read(p, db) for p in deposit.payees],
    )


@router.post("/openings/{opening_id}", response_model=DepositRead, status_code=status.HTTP_201_CREATED)
def create_deposit(
    opening_id: int,
    data: DepositCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> DepositRead:
    deposit = DepositService(db).create(opening_id, data, actor=user)
    return _deposit_read(deposit, db)


@router.get("/openings/{opening_id}", response_model=list[DepositRead])
def list_deposits(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DepositRead]:
    service = DepositService(db)
    return [_deposit_read(d, db) for d in service.list_for_opening(opening_id)]


@router.get("/{deposit_id}", response_model=DepositRead)
def get_deposit(
    deposit_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DepositRead:
    return _deposit_read(DepositService(db).get(deposit_id), db)


@router.post("/{deposit_id}/payees", response_model=PayeeRead, status_code=status.HTTP_201_CREATED)
def add_payee(
    deposit_id: int,
    data: DepositPayeeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PayeeRead:
    return _payee_read(DepositService(db).add_payee(deposit_id, data, actor=user), db)


@router.post("/payees/{payee_id}/payments", response_model=DepositPaymentRead, status_code=status.HTTP_201_CREATED)
def record_payment(
    payee_id: int,
    data: DepositPaymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> DepositPaymentRead:
    payment: DepositPayment = DepositService(db).record_payment(payee_id, data, actor=user)
    return DepositPaymentRead(
        id=payment.id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        reference=payment.reference,
        status=payment.status,
        created_by=payment.created_by,
        created_at=payment.created_at,
    )