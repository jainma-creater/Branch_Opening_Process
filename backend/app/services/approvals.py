from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Approval, AuditEvent, BranchOpening, User
from app.models.approval import ApprovalDecision, ApprovalType


class ApprovalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def request(
        self,
        opening_id: int,
        entity_type: str,
        entity_id: str | None,
        approval_type: ApprovalType,
        requested_by: User,
        amount=None,
        comments: str | None = None,
    ) -> Approval:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        approval = Approval(
            branch_opening_id=opening_id,
            entity_type=entity_type,
            entity_id=entity_id,
            approval_type=approval_type,
            requested_by=requested_by.id,
            amount=amount,
            comments=comments,
        )
        self.db.add(approval)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="approvals",
                entity_id=str(approval.id),
                action="APPROVAL_REQUESTED",
                stage=opening.current_stage,
                user_id=requested_by.id,
                new_value=approval_type.value,
                comments=comments,
            )
        )
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def decide(self, approval: Approval, decision: ApprovalDecision, approver: User, comments: str | None = None, amount=None) -> Approval:
        if approval.decision is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Approval already decided; decisions are immutable",
            )
        approval.decision = decision
        approval.approver = approver.id
        approval.decision_at = datetime.now(timezone.utc)
        if amount is not None:
            approval.amount = amount
        approval.comments = comments

        opening = self.db.get(BranchOpening, approval.branch_opening_id)
        if opening is not None:
            self.db.add(
                AuditEvent(
                    branch_opening_id=opening.id,
                    entity_type="approvals",
                    entity_id=str(approval.id),
                    action=f"APPROVAL_{decision.value}",
                    stage=opening.current_stage,
                    user_id=approver.id,
                    old_value="PENDING",
                    new_value=decision.value,
                    comments=comments,
                )
            )
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def get(self, approval_id: int) -> Approval:
        approval = self.db.get(Approval, approval_id)
        if approval is None:
            raise HTTPException(status_code=404, detail="Approval not found")
        return approval

    def list_for_opening(self, opening_id: int) -> list[Approval]:
        return list(
            self.db.scalars(
                select(Approval)
                .where(Approval.branch_opening_id == opening_id)
                .order_by(Approval.requested_at)
            ).all()
        )

    def pending_for_role(self, role_name: str) -> list[Approval]:
        """Approvals awaiting decisions, optionally filtered by the type the
        role is responsible for."""
        stmt = select(Approval).where(Approval.decision.is_(None))
        return list(self.db.scalars(stmt.order_by(Approval.requested_at)).all())