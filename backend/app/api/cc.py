from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.cc import CCRequestCreate, CCRequestRead, CCReview
from app.services.cc import CCService

router = APIRouter(prefix="/cc-approvals", tags=["CC & MD Approvals"])

MANAGERS = (
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.REGIONAL_ADMIN.value,
)
CC_TEAM = (RoleCode.CC.value, RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)
MD_TEAM = (RoleCode.MD.value, RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


@router.post(
    "/requests",
    response_model=CCRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    data: CCRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> CCRequestRead:
    return CCService(db).create(data, actor=user)


@router.get("/requests", response_model=list[CCRequestRead])
def list_requests(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CCRequestRead]:
    return CCService(db).list_all()


@router.get("/requests/{request_id}", response_model=CCRequestRead)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CCRequestRead:
    return CCService(db).get(request_id)


@router.post("/requests/{request_id}/submit", response_model=CCRequestRead)
def submit_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> CCRequestRead:
    return CCService(db).submit(request_id, actor=user)


@router.post("/requests/{request_id}/cc-review", response_model=CCRequestRead)
def cc_review(
    request_id: int,
    data: CCReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*CC_TEAM)),
) -> CCRequestRead:
    return CCService(db).cc_review(request_id, data, actor=user)


@router.post("/requests/{request_id}/md-review", response_model=CCRequestRead)
def md_review(
    request_id: int,
    data: CCReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MD_TEAM)),
) -> CCRequestRead:
    return CCService(db).md_review(request_id, data, actor=user)
