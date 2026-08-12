from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.services.reports import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    return ReportService(db).summary()


@router.get("/pending-approvals")
def pending_approvals(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    return ReportService(db).pending_approvals()


@router.get("/spend")
def spend(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    return ReportService(db).spend()
