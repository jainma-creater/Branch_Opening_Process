from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.accounts import (
    InvoiceCreate,
    InvoiceRead,
    InvoiceReview,
    InvoiceRevise,
    QuotationAccountsReview,
)
from app.schemas.procurement import QuotationRequestRead
from app.services.accounts import AccountsService

router = APIRouter(prefix="/accounts", tags=["Accounts"])

MANAGERS = (
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
    RoleCode.REGIONAL_ADMIN.value,
)
ACCOUNTS_TEAM = (
    RoleCode.ACCOUNTS.value,
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
)


@router.post(
    "/openings/{opening_id}/quotation-requests/{request_id}/review",
    response_model=QuotationRequestRead,
)
def review_quotation_request(
    opening_id: int,
    request_id: int,
    data: QuotationAccountsReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*ACCOUNTS_TEAM)),
) -> QuotationRequestRead:
    return AccountsService(db).review_quotation_request(opening_id, request_id, data, actor=user)


@router.post(
    "/openings/{opening_id}/invoices",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice(
    opening_id: int,
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> InvoiceRead:
    return AccountsService(db).create_invoice(opening_id, data, actor=user)


@router.get("/openings/{opening_id}/invoices", response_model=list[InvoiceRead])
def list_invoices(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[InvoiceRead]:
    return AccountsService(db).list_for_opening(opening_id)


@router.post("/invoices/{invoice_id}/submit", response_model=InvoiceRead)
def submit_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> InvoiceRead:
    return AccountsService(db).submit_invoice(invoice_id, actor=user)


@router.post("/invoices/{invoice_id}/review", response_model=InvoiceRead)
def review_invoice(
    invoice_id: int,
    data: InvoiceReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*ACCOUNTS_TEAM)),
) -> InvoiceRead:
    return AccountsService(db).review_invoice(invoice_id, data, actor=user)


@router.post(
    "/invoices/{invoice_id}/revise",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
def revise_invoice(
    invoice_id: int,
    data: InvoiceRevise,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
) -> InvoiceRead:
    return AccountsService(db).revise_invoice(invoice_id, data, actor=user)


@router.get("/invoices/{invoice_id}/history", response_model=list[InvoiceRead])
def invoice_history(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[InvoiceRead]:
    return AccountsService(db).history(invoice_id)
