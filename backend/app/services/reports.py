from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Approval, BranchOpening, CCRequest, Invoice, Payment
from app.models.accounts import InvoiceStatus
from app.models.cc import CCRequestStatus
from app.models.opening import CaseStatus
from app.models.payment import PaymentStatus

APPROVAL_STAGES = ("ACCOUNTS", "CC_APPROVAL", "MD_APPROVAL")


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self) -> dict:
        total = self.db.scalar(select(func.count(BranchOpening.id))) or 0
        by_stage_rows = self.db.execute(
            select(BranchOpening.current_stage, func.count(BranchOpening.id))
            .group_by(BranchOpening.current_stage)
        ).all()
        by_status_rows = self.db.execute(
            select(BranchOpening.case_status, func.count(BranchOpening.id))
            .group_by(BranchOpening.case_status)
        ).all()
        completed = (
            self.db.scalar(
                select(func.count(BranchOpening.id)).where(
                    BranchOpening.case_status == CaseStatus.COMPLETED
                )
            )
            or 0
        )
        return {
            "total_openings": total,
            "completed_openings": completed,
            "openings_by_stage": {stage: count for stage, count in by_stage_rows},
            "openings_by_status": {status: count for status, count in by_status_rows},
        }

    def pending_approvals(self) -> list[dict]:
        pending = self.db.scalars(
            select(Approval)
            .where(Approval.decision.is_(None))
            .order_by(Approval.requested_at)
        ).all()
        opening_ids = {a.branch_opening_id for a in pending}
        result = []
        for opening_id in opening_ids:
            opening = self.db.get(BranchOpening, opening_id)
            if opening is None:
                continue
            result.append(
                {
                    "opening_id": opening.id,
                    "opening_number": opening.opening_number,
                    "branch_name": opening.branch.name if opening.branch else None,
                    "current_stage": opening.current_stage,
                    "pending_approval_types": sorted(
                        {
                            a.approval_type
                            for a in pending
                            if a.branch_opening_id == opening_id
                        }
                    ),
                }
            )
        return result

    def spend(self) -> dict:
        total_invoiced = (
            self.db.scalar(select(func.coalesce(func.sum(Invoice.total_amount), 0))) or 0
        )
        approved_invoiced = (
            self.db.scalar(
                select(func.coalesce(func.sum(Invoice.total_amount), 0)).where(
                    Invoice.status == InvoiceStatus.APPROVED
                )
            )
            or 0
        )
        paid = (
            self.db.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.status == PaymentStatus.PAID
                )
            )
            or 0
        )
        pending_cc = (
            self.db.scalar(
                select(func.count(CCRequest.id)).where(
                    CCRequest.status.in_(
                        [CCRequestStatus.DRAFT, CCRequestStatus.SUBMITTED, CCRequestStatus.CC_APPROVED]
                    )
                )
            )
            or 0
        )
        return {
            "total_invoiced": float(total_invoiced),
            "approved_invoiced": float(approved_invoiced),
            "total_paid": float(paid),
            "pending_cc_requests": pending_cc,
        }
