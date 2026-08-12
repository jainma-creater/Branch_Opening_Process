from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.agreement import (
    AgreementCreate,
    AgreementRead,
    AgreementStatusUpdate,
    AgreementUpdate,
)
from app.services.agreements import AgreementService

router = APIRouter(prefix="/agreements", tags=["Agreements"])

MANAGERS = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


@router.post("/openings/{opening_id}", response_model=AgreementRead, status_code=status.HTTP_201_CREATED)
def create_agreement(
    opening_id: int,
    data: AgreementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> AgreementRead:
    return AgreementService(db).create(opening_id, data, actor=user)


@router.get("/openings/{opening_id}", response_model=list[AgreementRead])
def list_agreements(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AgreementRead]:
    return AgreementService(db).list_for_opening(opening_id)


@router.get("/{agreement_id}", response_model=AgreementRead)
def get_agreement(
    agreement_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AgreementRead:
    return AgreementService(db).get(agreement_id)


@router.patch("/{agreement_id}", response_model=AgreementRead)
def update_agreement(
    agreement_id: int,
    data: AgreementUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> AgreementRead:
    return AgreementService(db).update(agreement_id, data, actor=user)


@router.patch("/{agreement_id}/status", response_model=AgreementRead)
def set_agreement_status(
    agreement_id: int,
    data: AgreementStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> AgreementRead:
    return AgreementService(db).set_status(agreement_id, data, actor=user)