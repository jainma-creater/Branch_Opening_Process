from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, BranchOpening, User
from app.models.approval import ApprovalDecision, ApprovalType
from app.models.cc import CCRequest, CCRequestItem, CCRequestStatus
from app.schemas.cc import CCRequestCreate, CCReview
from app.services.approvals import ApprovalService
from app.services.workflow import WorkflowService


def _next_request_code(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.scalar(
        select(CCRequest.id).where(CCRequest.request_code.like(f"CC-{year}-%"))
    )
    sequence = (count or 0) + 1
    return f"CC-{year}-{sequence:04d}"


class CCService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.approvals = ApprovalService(db)
        self.workflow = WorkflowService(db)

    # -- lifecycle ---------------------------------------------------------
    def create(self, data: CCRequestCreate, actor: User) -> CCRequest:
        if not data.items:
            raise HTTPException(status_code=422, detail="Add at least one branch opening item")
        request = CCRequest(
            request_code=_next_request_code(self.db),
            status=CCRequestStatus.DRAFT,
            requested_by=actor.id,
            remarks=data.remarks,
        )
        for item in data.items:
            request.items.append(
                CCRequestItem(
                    branch_opening_id=item.branch_opening_id,
                    requested_amount=item.requested_amount,
                    remarks=item.remarks,
                )
            )
        self.db.add(request)
        self.db.flush()
        self.db.add(
            AuditEvent(
                entity_type="cc_requests",
                entity_id=str(request.id),
                action="CC_REQUEST_CREATED",
                user_id=actor.id,
                new_value=request.request_code,
            )
        )
        self.db.commit()
        self.db.refresh(request)
        return request

    def get(self, request_id: int) -> CCRequest:
        request = self.db.scalar(
            select(CCRequest)
            .where(CCRequest.id == request_id)
        )
        if request is None:
            raise HTTPException(status_code=404, detail="CC request not found")
        return request

    def list_all(self) -> list[CCRequest]:
        return list(
            self.db.scalars(select(CCRequest).order_by(CCRequest.id)).all()
        )

    def _openings(self, request: CCRequest) -> list[BranchOpening]:
        return [
            self.db.get(BranchOpening, item.branch_opening_id)
            for item in request.items
        ]

    def _advance_all(self, request: CCRequest, target: str, actor: User) -> None:
        for opening in self._openings(request):
            if opening is None:
                continue
            self.workflow.transition(opening, target, actor)

    def _send_back_all(self, request: CCRequest, actor: User) -> None:
        for opening in self._openings(request):
            if opening is None:
                continue
            self.workflow.send_back(opening, actor)

    def submit(self, request_id: int, actor: User) -> CCRequest:
        request = self.get(request_id)
        if request.status != CCRequestStatus.DRAFT:
            raise HTTPException(
                status_code=409, detail="Only draft CC requests can be submitted"
            )
        request.status = CCRequestStatus.SUBMITTED
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    # -- CC review ---------------------------------------------------------
    def cc_review(self, request_id: int, data: CCReview, actor: User) -> CCRequest:
        request = self.get(request_id)
        self._assert_no_decision(request_id, ApprovalType.CC)
        if data.decision not in ("APPROVED", "REJECTED", "SENT_BACK"):
            raise HTTPException(status_code=422, detail="Invalid CC decision")

        approval = self.approvals.request(
            opening_id=request.items[0].branch_opening_id,
            entity_type="cc_requests",
            entity_id=str(request_id),
            approval_type=ApprovalType.CC,
            requested_by=actor,
            comments=data.comments,
        )
        self.approvals.decide(
            approval, ApprovalDecision(data.decision), actor, comments=data.comments
        )

        if data.decision == "APPROVED":
            for item in request.items:
                match = next(
                    (d for d in data.items if d.branch_opening_id == item.branch_opening_id),
                    None,
                )
                item.approved_amount = match.approved_amount if match else item.requested_amount
            request.status = CCRequestStatus.CC_APPROVED
            request.cc_reviewer_id = actor.id
            self.db.add_all(request.items)
            self._advance_all(request, "MD_APPROVAL", actor)
        elif data.decision == "SENT_BACK":
            request.status = CCRequestStatus.SENT_BACK
            self._send_back_all(request, actor)
        else:
            request.status = CCRequestStatus.REJECTED
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    # -- MD review ---------------------------------------------------------
    def md_review(self, request_id: int, data: CCReview, actor: User) -> CCRequest:
        request = self.get(request_id)
        self._assert_no_decision(request_id, ApprovalType.MD)
        if data.decision not in ("APPROVED", "REJECTED", "SENT_BACK"):
            raise HTTPException(status_code=422, detail="Invalid MD decision")

        approval = self.approvals.request(
            opening_id=request.items[0].branch_opening_id,
            entity_type="cc_requests",
            entity_id=str(request_id),
            approval_type=ApprovalType.MD,
            requested_by=actor,
            comments=data.comments,
        )
        self.approvals.decide(
            approval, ApprovalDecision(data.decision), actor, comments=data.comments
        )

        if data.decision == "APPROVED":
            request.status = CCRequestStatus.MD_APPROVED
            request.md_reviewer_id = actor.id
            self._advance_all(request, "PAYMENT", actor)
        elif data.decision == "SENT_BACK":
            request.status = CCRequestStatus.SENT_BACK
            self._send_back_all(request, actor)
        else:
            request.status = CCRequestStatus.REJECTED
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def _assert_no_decision(self, request_id: int, approval_type: ApprovalType) -> None:
        from app.models import Approval

        decided = self.db.scalar(
            select(Approval).where(
                Approval.entity_type == "cc_requests",
                Approval.entity_id == str(request_id),
                Approval.approval_type == approval_type,
                Approval.decision.is_not(None),
            )
        )
        if decided is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{approval_type.value} decision already recorded; decisions are immutable",
            )
