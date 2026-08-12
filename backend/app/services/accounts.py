from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Approval, AuditEvent, BranchOpening, QuotationRequest, User, Vendor
from app.models.accounts import AccountReviewDecision, Invoice, InvoiceStatus
from app.models.approval import ApprovalDecision, ApprovalType
from app.models.procurement import QuotationRequestStatus
from app.models.roles import RoleCode
from app.schemas.accounts import (
    InvoiceCreate,
    InvoiceReview,
    InvoiceRevise,
    QuotationAccountsReview,
)
from app.services.approvals import ApprovalService
from app.services.workflow import WorkflowService

ACCOUNTS_ROLES = (
    RoleCode.ACCOUNTS.value,
    RoleCode.SUPER_ADMIN.value,
    RoleCode.ADMIN.value,
)

#: Map accounts review decisions to recorded approval decisions.
_DECISION_MAP = {
    AccountReviewDecision.APPROVED: ApprovalDecision.APPROVED,
    AccountReviewDecision.REJECTED: ApprovalDecision.REJECTED,
    AccountReviewDecision.SENT_BACK: ApprovalDecision.SENT_BACK,
    AccountReviewDecision.MISMATCH: ApprovalDecision.MISMATCH,
    AccountReviewDecision.REVISION_REQUIRED: ApprovalDecision.REVISION_REQUIRED,
}


class AccountsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.approvals = ApprovalService(db)
        self.workflow = WorkflowService(db)

    # -- Quotation accounts review ---------------------------------------
    def review_quotation_request(
        self,
        opening_id: int,
        request_id: int,
        data: QuotationAccountsReview,
        actor: User,
    ) -> QuotationRequest:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        request = self.db.scalar(
            select(QuotationRequest).where(
                QuotationRequest.id == request_id,
                QuotationRequest.branch_opening_id == opening_id,
            )
        )
        if request is None:
            raise HTTPException(status_code=404, detail="Quotation request not found")

        approval = self.approvals.request(
            opening_id=opening_id,
            entity_type="quotation_requests",
            entity_id=str(request_id),
            approval_type=ApprovalType.ACCOUNTS,
            requested_by=actor,
            amount=data.approved_amount,
            comments=data.comments,
        )
        self.approvals.decide(
            approval, _DECISION_MAP[data.decision], actor, comments=data.comments
        )

        if data.decision == AccountReviewDecision.SENT_BACK:
            self.workflow.transition(opening, "QUOTATION", actor, comments=data.comments)
            request.status = QuotationRequestStatus.OPEN
            self.db.add(request)
            self.db.commit()
            self.db.refresh(request)
            return request

        if data.decision == AccountReviewDecision.APPROVED:
            if data.approved_amount is None:
                raise HTTPException(
                    status_code=422, detail="Approved amount is required on approval"
                )
            request.approved_amount = Decimal(str(data.approved_amount))
            self.db.add(request)
            self.workflow.transition(opening, "CC_APPROVAL", actor, comments=data.comments)
            self.db.refresh(request)
            return request

        # MISMATCH / REJECTED / REVISION_REQUIRED: no stage change, just the
        # immutable approval record stands.
        self.db.refresh(request)
        return request

    # -- Invoices ---------------------------------------------------------
    def create_invoice(
        self, opening_id: int, data: InvoiceCreate, actor: User
    ) -> Invoice:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        vendor = self.db.get(Vendor, data.vendor_id)
        if vendor is None:
            raise HTTPException(status_code=422, detail="Vendor does not exist")
        amount = Decimal(str(data.amount))
        tax = Decimal(str(data.tax))
        invoice = Invoice(
            branch_opening_id=opening_id,
            vendor_id=data.vendor_id,
            invoice_number=data.invoice_number.strip(),
            invoice_date=data.invoice_date,
            amount=amount,
            tax=tax,
            total_amount=amount + tax,
            status=InvoiceStatus.DRAFT,
            version=1,
            created_by=actor.id,
            remarks=data.remarks,
        )
        self.db.add(invoice)
        self.db.flush()
        self.db.add(
            AuditEvent(  # type: ignore[name-defined]  # imported below
                branch_opening_id=opening_id,
                entity_type="invoices",
                entity_id=str(invoice.id),
                action="INVOICE_CREATED",
                user_id=actor.id,
                new_value=invoice.invoice_number,
            )
        )
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.db.scalar(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice

    def list_for_opening(self, opening_id: int) -> list[Invoice]:
        return list(
            self.db.scalars(
                select(Invoice)
                .where(Invoice.branch_opening_id == opening_id)
                .order_by(Invoice.id)
            ).all()
        )

    def submit_invoice(self, invoice_id: int, actor: User) -> Invoice:
        invoice = self.get_invoice(invoice_id)
        if invoice.status != InvoiceStatus.DRAFT:
            raise HTTPException(
                status_code=409, detail="Only draft invoices can be submitted"
            )
        invoice.status = InvoiceStatus.SUBMITTED
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def review_invoice(
        self, invoice_id: int, data: InvoiceReview, actor: User
    ) -> Invoice:
        invoice = self.get_invoice(invoice_id)
        if invoice.status not in (InvoiceStatus.SUBMITTED, InvoiceStatus.UNDER_REVIEW):
            raise HTTPException(
                status_code=409,
                detail="Invoice must be submitted before accounts review",
            )
        decision = data.decision
        if decision not in (
            AccountReviewDecision.APPROVED,
            AccountReviewDecision.MISMATCH,
            AccountReviewDecision.REVISION_REQUIRED,
            AccountReviewDecision.REJECTED,
        ):
            raise HTTPException(
                status_code=422,
                detail="Invoice review must be APPROVED/MISMATCH/REVISION_REQUIRED/REJECTED",
            )

        approval = self.approvals.request(
            opening_id=invoice.branch_opening_id,
            entity_type="invoices",
            entity_id=str(invoice.id),
            approval_type=ApprovalType.INVOICE,
            requested_by=actor,
            amount=float(invoice.total_amount),
            comments=data.remarks,
        )
        self.approvals.decide(
            approval, _DECISION_MAP[decision], actor, comments=data.remarks
        )

        if decision == AccountReviewDecision.APPROVED:
            invoice.status = InvoiceStatus.APPROVED
        elif decision == AccountReviewDecision.REVISION_REQUIRED:
            invoice.status = InvoiceStatus.REVISION_REQUIRED
        elif decision == AccountReviewDecision.MISMATCH:
            invoice.status = InvoiceStatus.MISMATCH
        else:
            invoice.status = InvoiceStatus.REJECTED
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def revise_invoice(
        self, invoice_id: int, data: InvoiceRevise, actor: User
    ) -> Invoice:
        old = self.get_invoice(invoice_id)
        if old.status not in (
            InvoiceStatus.MISMATCH,
            InvoiceStatus.REVISION_REQUIRED,
            InvoiceStatus.REJECTED,
        ):
            raise HTTPException(
                status_code=409,
                detail="Only mismatched, revision-required or rejected invoices can be revised",
            )
        amount = Decimal(str(data.amount))
        tax = Decimal(str(data.tax))
        revised = Invoice(
            branch_opening_id=old.branch_opening_id,
            vendor_id=old.vendor_id,
            invoice_number=data.invoice_number.strip(),
            invoice_date=data.invoice_date,
            amount=amount,
            tax=tax,
            total_amount=amount + tax,
            status=InvoiceStatus.REVISED,
            version=old.version + 1,
            parent_invoice_id=old.id,
            created_by=actor.id,
            remarks=data.remarks,
        )
        self.db.add(revised)
        self.db.flush()
        self.db.add(
            AuditEvent(  # type: ignore[name-defined]
                branch_opening_id=old.branch_opening_id,
                entity_type="invoices",
                entity_id=str(revised.id),
                action="INVOICE_REVISED",
                user_id=actor.id,
                old_value=str(old.id),
                new_value=revised.invoice_number,
            )
        )
        self.db.commit()
        self.db.refresh(revised)
        return revised

    def history(self, invoice_id: int) -> list[Invoice]:
        invoice = self.get_invoice(invoice_id)
        root = invoice
        while root.parent_invoice_id is not None:
            parent = self.db.get(Invoice, root.parent_invoice_id)
            if parent is None:
                break
            root = parent
        chain: list[Invoice] = [root]
        seen = {root.id}
        queue = [root.id]
        while queue:
            current_id = queue.pop(0)
            children = list(
                self.db.scalars(
                    select(Invoice)
                    .where(Invoice.parent_invoice_id == current_id)
                    .order_by(Invoice.id)
                ).all()
            )
            for child in children:
                if child.id not in seen:
                    seen.add(child.id)
                    chain.append(child)
                    queue.append(child.id)
        return chain
