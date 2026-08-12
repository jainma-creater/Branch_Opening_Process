from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.deposit import LOARequestCreate, LOARequestRead, LOARequestUpdate
from app.services.deposit import LOAService

router = APIRouter(prefix="/loa", tags=["LOA"])

MANAGERS = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


@router.post("/openings/{opening_id}", response_model=LOARequestRead, status_code=status.HTTP_201_CREATED)
def create_loa(
    opening_id: int,
    data: LOARequestCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*MANAGERS)),
) -> LOARequestRead:
    return LOAService(db).create(opening_id, data)


@router.get("/openings/{opening_id}", response_model=list[LOARequestRead])
def list_loa(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[LOARequestRead]:
    from sqlalchemy import select

    from app.models import LOARequest

    return list(
        db.scalars(
            select(LOARequest)
            .where(LOARequest.branch_opening_id == opening_id)
            .order_by(LOARequest.id)
        ).all()
    )


@router.get("/{loa_id}", response_model=LOARequestRead)
def get_loa(
    loa_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LOARequestRead:
    return LOAService(db).get(loa_id)


@router.patch("/{loa_id}", response_model=LOARequestRead)
def update_loa(
    loa_id: int,
    data: LOARequestUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> LOARequestRead:
    return LOAService(db).update(loa_id, data, actor=user)