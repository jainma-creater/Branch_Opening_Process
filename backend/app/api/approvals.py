from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.workflow import (
    ApprovalDecisionRequest,
    ApprovalRead,
    ApprovalRequest,
)
from app.services.approvals import ApprovalService

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.post("", response_model=ApprovalRead, status_code=status.HTTP_201_CREATED)
def request_approval(
    opening_id: int,
    data: ApprovalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApprovalRead:
    return ApprovalService(db).request(
        opening_id=opening_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        approval_type=data.approval_type,
        requested_by=user,
        amount=data.amount,
        comments=data.comments,
    )


@router.get("/{approval_id}", response_model=ApprovalRead)
def get_approval(
    approval_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ApprovalRead:
    return ApprovalService(db).get(approval_id)


@router.post("/{approval_id}/decision", response_model=ApprovalRead)
def decide_approval(
    approval_id: int,
    data: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApprovalRead:
    approval = ApprovalService(db).get(approval_id)
    return ApprovalService(db).decide(approval, data.decision, user, data.comments, data.amount)