from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.properties import (
    PropertyCancel,
    PropertyCreate,
    PropertyRead,
    PropertyStatusUpdate,
    PropertyUpdate,
)
from app.services.openings import OpeningService
from app.services.properties import PropertyService

router = APIRouter(prefix="/properties", tags=["Properties"])

MANAGERS = (
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.REGIONAL_ADMIN.value,
)


def _read(option, db: Session) -> PropertyRead:
    service = PropertyService(db)
    limit, check = service.rent_limit_check(option)
    return PropertyRead(
        id=option.id,
        option_sequence=option.option_sequence,
        address=option.address,
        area_sqft=option.area_sqft,
        rent=option.rent,
        deposit=option.deposit,
        annual_increment=option.annual_increment,
        entrance=option.entrance,
        restroom=option.restroom,
        possession_status=option.possession_status,
        remarks=option.remarks,
        status=option.status,
        rent_limit_check=check,
        applicable_rent_limit=limit,
        created_at=option.created_at,
        updated_at=option.updated_at,
    )


@router.get("/openings/{opening_id}", response_model=list[PropertyRead])
def list_properties(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PropertyRead]:
    OpeningService(db).get(opening_id)
    service = PropertyService(db)
    return [_read(p, db) for p in service.list_for_opening(opening_id)]


@router.post("/openings/{opening_id}", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def add_property(
    opening_id: int,
    data: PropertyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PropertyRead:
    OpeningService(db).get(opening_id)
    option = PropertyService(db).create(opening_id, data, actor=user)
    return _read(option, db)


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PropertyRead:
    return _read(PropertyService(db).get(property_id), db)


@router.patch("/{property_id}", response_model=PropertyRead)
def update_property(
    property_id: int,
    data: PropertyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PropertyRead:
    return _read(PropertyService(db).update(property_id, data, actor=user), db)


@router.patch("/{property_id}/status", response_model=PropertyRead)
def set_property_status(
    property_id: int,
    data: PropertyStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PropertyRead:
    return _read(PropertyService(db).set_status(property_id, data, actor=user), db)


@router.post("/{property_id}/approval-request", response_model=PropertyRead)
def request_property_approval(
    property_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PropertyRead:
    return _read(PropertyService(db).request_approval(property_id, actor=user), db)


@router.post("/{property_id}/approve", response_model=PropertyRead)
def approve_property(
    property_id: int,
    comments: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PropertyRead:
    return _read(PropertyService(db).approve(property_id, actor=user, comments=comments), db)


@router.post("/{property_id}/cancel", response_model=PropertyRead)
def cancel_property(
    property_id: int,
    data: PropertyCancel | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> PropertyRead:
    return _read(
        PropertyService(db).cancel(property_id, data or PropertyCancel(), actor=user), db
    )