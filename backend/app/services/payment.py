from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Approval, AuditEvent, BranchOpening, Invoice, User, Vendor
from app.models.approval import ApprovalDecision, ApprovalType
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentReview
from app.services.approvals import ApprovalService
from app.services.workflow import WorkflowService

PAYMENT_TEAM = ("ACCOUNTS", "SUPER_ADMIN", "ADMIN")


class PaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.approvals = ApprovalService(db)
        self.workflow = WorkflowService(db)

    def create(self, opening_id: int, data: PaymentCreate, actor: User) -> Payment:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        if data.invoice_id is not None:
            invoice = self.db.get(Invoice, data.invoice_id)
            if invoice is None:
                raise HTTPException(status_code=422, detail="Invoice does not exist")
        if data.vendor_id is not None:
            vendor = self.db.get(Vendor, data.vendor_id)
            if vendor is None:
                raise HTTPException(status_code=422, detail="Vendor does not exist")

        payment = Payment(
            branch_opening_id=opening_id,
            invoice_id=data.invoice_id,
            vendor_id=data.vendor_id,
            amount=data.amount,
            mode=data.mode,
            reference_no=data.reference_no,
            payment_date=data.payment_date,
            status=PaymentStatus.DRAFT,
            requested_by=actor.id,
            remarks=data.remarks,
        )
        self.db.add(payment)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="payments",
                entity_id=str(payment.id),
                action="PAYMENT_CREATED",
                user_id=actor.id,
                new_value=str(data.amount),
            )
        )
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get(self, payment_id: int) -> Payment:
        payment = self.db.get(Payment, payment_id)
        if payment is None:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment

    def list_for_opening(self, opening_id: int) -> list[Payment]:
        return list(
            self.db.scalars(
                select(Payment)
                .where(Payment.branch_opening_id == opening_id)
                .order_by(Payment.id)
            ).all()
        )

    def submit(self, payment_id: int, actor: User) -> Payment:
        payment = self.get(payment_id)
        if payment.status != PaymentStatus.DRAFT:
            raise HTTPException(
                status_code=409, detail="Only draft payments can be submitted"
            )
        payment.status = PaymentStatus.SUBMITTED
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def review(self, payment_id: int, data: PaymentReview, actor: User) -> Payment:
        payment = self.get(payment_id)
        if payment.status not in (PaymentStatus.SUBMITTED, PaymentStatus.APPROVED):
            raise HTTPException(
                status_code=409, detail="Payment must be submitted before review"
            )
        if data.decision not in ("APPROVED", "REJECTED"):
            raise HTTPException(status_code=422, detail="Decision must be APPROVED/REJECTED")

        decided = self.db.scalar(
            select(Approval).where(
                Approval.entity_type == "payments",
                Approval.entity_id == str(payment_id),
                Approval.approval_type == ApprovalType.PAYMENT,
                Approval.decision.is_not(None),
            )
        )
        if decided is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment approval already recorded; decisions are immutable",
            )

        approval = self.approvals.request(
            opening_id=payment.branch_opening_id,
            entity_type="payments",
            entity_id=str(payment_id),
            approval_type=ApprovalType.PAYMENT,
            requested_by=actor,
            amount=float(payment.amount),
            comments=data.comments,
        )
        self.approvals.decide(
            approval, ApprovalDecision(data.decision), actor, comments=data.comments
        )
        if data.decision == "APPROVED":
            payment.status = PaymentStatus.APPROVED
            payment.approved_by = actor.id
        else:
            payment.status = PaymentStatus.REJECTED
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def mark_paid(self, payment_id: int, actor: User) -> Payment:
        payment = self.get(payment_id)
        if payment.status != PaymentStatus.APPROVED:
            raise HTTPException(
                status_code=409, detail="Only approved payments can be marked paid"
            )
        payment.status = PaymentStatus.PAID
        self.db.add(payment)
        opening = self.db.get(BranchOpening, payment.branch_opening_id)
        if opening is not None:
            self.workflow.transition(opening, "INFRASTRUCTURE", actor)
        self.db.commit()
        self.db.refresh(payment)
        return payment
