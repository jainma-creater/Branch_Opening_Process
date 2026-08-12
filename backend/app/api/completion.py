from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.completion import (
    FitoutCreate,
    FitoutRead,
    FitoutUpdate,
    OpeningRecordCreate,
    OpeningRecordRead,
    ReadinessItemCreate,
    ReadinessItemRead,
    ReadinessItemUpdate,
)
from app.services.completion import CompletionService

router = APIRouter(prefix="/completion", tags=["Completion"])

MANAGERS = (
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.REGIONAL_ADMIN.value,
)


@router.post(
    "/openings/{opening_id}/fitouts",
    response_model=FitoutRead,
    status_code=status.HTTP_201_CREATED,
)
def create_fitout(
    opening_id: int,
    data: FitoutCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> FitoutRead:
    return CompletionService(db).create_fitout(opening_id, data, actor=user)


@router.get("/openings/{opening_id}/fitouts", response_model=list[FitoutRead])
def list_fitouts(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[FitoutRead]:
    return CompletionService(db).list_fitouts(opening_id)


@router.patch("/fitouts/{fitout_id}", response_model=FitoutRead)
def update_fitout(
    fitout_id: int,
    data: FitoutUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> FitoutRead:
    return CompletionService(db).update_fitout(fitout_id, data, actor=user)


@router.post(
    "/openings/{opening_id}/readiness",
    response_model=ReadinessItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_readiness(
    opening_id: int,
    data: ReadinessItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> ReadinessItemRead:
    return CompletionService(db).create_readiness(opening_id, data, actor=user)


@router.get("/openings/{opening_id}/readiness", response_model=list[ReadinessItemRead])
def list_readiness(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ReadinessItemRead]:
    return CompletionService(db).list_readiness(opening_id)


@router.patch("/readiness/{item_id}", response_model=ReadinessItemRead)
def update_readiness(
    item_id: int,
    data: ReadinessItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> ReadinessItemRead:
    return CompletionService(db).update_readiness(item_id, data, actor=user)


@router.post(
    "/openings/{opening_id}/opening-record",
    response_model=OpeningRecordRead,
    status_code=status.HTTP_201_CREATED,
)
def create_opening_record(
    opening_id: int,
    data: OpeningRecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> OpeningRecordRead:
    return CompletionService(db).create_opening_record(opening_id, data, actor=user)


@router.get("/openings/{opening_id}/opening-record", response_model=OpeningRecordRead)
def get_opening_record(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OpeningRecordRead:
    return CompletionService(db).get_opening_record(opening_id)
