from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentReview
from app.services.payment import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])

MANAGERS = (
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.REGIONAL_ADMIN.value,
)
PAYMENT_TEAM = (
    RoleCode.ACCOUNTS.value,
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
)


@router.post(
    "/openings/{opening_id}",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    opening_id: int,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PaymentRead:
    return PaymentService(db).create(opening_id, data, actor=user)


@router.get("/openings/{opening_id}", response_model=list[PaymentRead])
def list_payments(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PaymentRead]:
    return PaymentService(db).list_for_opening(opening_id)


@router.post("/{payment_id}/submit", response_model=PaymentRead)
def submit_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PaymentRead:
    return PaymentService(db).submit(payment_id, actor=user)


@router.post("/{payment_id}/review", response_model=PaymentRead)
def review_payment(
    payment_id: int,
    data: PaymentReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*PAYMENT_TEAM)),
) -> PaymentRead:
    return PaymentService(db).review(payment_id, data, actor=user)


@router.post("/{payment_id}/mark-paid", response_model=PaymentRead)
def mark_paid(
    payment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PaymentRead:
    return PaymentService(db).mark_paid(payment_id, actor=user)
