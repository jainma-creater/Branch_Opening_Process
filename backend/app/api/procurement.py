from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.procurement import (
    QuotationCreate,
    QuotationRead,
    QuotationRequestCreate,
    QuotationRequestRead,
    RequestItemCreate,
    RequestItemRead,
    SelectVendorRequest,
    VendorComparison,
    VendorCreate,
    VendorRead,
)
from app.services.procurement import QuotationRequestService, VendorService

router = APIRouter(prefix="/procurement", tags=["Procurement"])

MANAGERS = (
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.REGIONAL_ADMIN.value,
)


@router.post("/vendors", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def create_vendor(
    data: VendorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*MANAGERS)),
) -> VendorRead:
    return VendorService(db).create(data)


@router.get("/vendors", response_model=list[VendorRead])
def list_vendors(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[VendorRead]:
    return VendorService(db).list_active()


@router.post(
    "/quotation-requests/openings/{opening_id}",
    response_model=QuotationRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_quotation_request(
    opening_id: int,
    data: QuotationRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> QuotationRequestRead:
    return QuotationRequestService(db).create(opening_id, data, actor=user)


@router.get("/quotation-requests/openings/{opening_id}", response_model=list[QuotationRequestRead])
def list_quotation_requests(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[QuotationRequestRead]:
    return QuotationRequestService(db).list_for_opening(opening_id)


@router.get("/quotation-requests/{request_id}", response_model=QuotationRequestRead)
def get_quotation_request(
    request_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> QuotationRequestRead:
    return QuotationRequestService(db).get(request_id)


@router.post("/quotation-requests/{request_id}/items", response_model=QuotationRequestRead)
def add_request_item(
    request_id: int,
    data: RequestItemCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*MANAGERS)),
) -> QuotationRequestRead:
    return QuotationRequestService(db).add_item(request_id, data)


@router.post(
    "/quotation-requests/{request_id}/quotations",
    response_model=QuotationRead,
    status_code=status.HTTP_201_CREATED,
)
def add_quotation(
    request_id: int,
    data: QuotationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> QuotationRead:
    return QuotationRequestService(db).add_quotation(request_id, data, actor=user)


@router.get("/quotation-requests/{request_id}/comparison", response_model=VendorComparison)
def quotation_comparison(
    request_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> VendorComparison:
    return QuotationRequestService(db).comparison(request_id)


@router.post(
    "/quotation-requests/{request_id}/select-vendor",
    response_model=QuotationRequestRead,
)
def select_vendor(
    request_id: int,
    data: SelectVendorRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> QuotationRequestRead:
    return QuotationRequestService(db).select_vendor(request_id, data, actor=user)