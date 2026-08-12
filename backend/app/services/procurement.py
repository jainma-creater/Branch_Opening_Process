from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AuditEvent,
    BranchOpening,
    Quotation,
    QuotationItem,
    QuotationRequest,
    QuotationRequestItem,
    User,
    Vendor,
)
from app.models.approval import ApprovalType
from app.models.procurement import QuotationRequestStatus, QuotationStatus
from app.schemas.procurement import (
    QuotationCreate,
    QuotationRequestCreate,
    RequestItemCreate,
    SelectVendorRequest,
    VendorComparison,
    VendorComparisonRow,
    VendorCreate,
)
from app.services.approvals import ApprovalService


class VendorService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: VendorCreate) -> Vendor:
        existing = self.db.scalar(
            select(Vendor).where(Vendor.name == data.name.strip())
        )
        if existing:
            raise HTTPException(status_code=409, detail="Vendor already exists")
        vendor = Vendor(
            name=data.name.strip(),
            contact_person=data.contact_person,
            phone=data.phone,
            email=data.email,
            address=data.address,
        )
        self.db.add(vendor)
        self.db.commit()
        self.db.refresh(vendor)
        return vendor

    def get(self, vendor_id: int) -> Vendor:
        vendor = self.db.get(Vendor, vendor_id)
        if vendor is None:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return vendor

    def list_active(self) -> list[Vendor]:
        return list(
            self.db.scalars(
                select(Vendor).where(Vendor.is_active.is_(True)).order_by(Vendor.name)
            ).all()
        )


class QuotationRequestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.approvals = ApprovalService(db)

    def create(
        self, opening_id: int, data: QuotationRequestCreate, actor: User
    ) -> QuotationRequest:
        opening = self.db.get(BranchOpening, opening_id)
        if opening is None:
            raise HTTPException(status_code=404, detail="Opening not found")
        request = QuotationRequest(
            branch_opening_id=opening_id,
            request_date=data.request_date or date.today(),
            required_date=data.required_date,
            scope_description=data.scope_description,
            created_by=actor.id,
        )
        for item in data.items:
            request.items.append(
                QuotationRequestItem(
                    category=item.category,
                    description=item.description,
                    quantity=item.quantity,
                    unit=item.unit,
                )
            )
        self.db.add(request)
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=opening_id,
                entity_type="quotation_requests",
                entity_id=str(request.id),
                action="QUOTATION_REQUEST_CREATED",
                stage=opening.current_stage,
                user_id=actor.id,
            )
        )
        self.db.commit()
        return self.get(request.id)

    def get(self, request_id: int) -> QuotationRequest:
        request = self.db.scalar(
            select(QuotationRequest)
            .options(
                selectinload(QuotationRequest.items),
                selectinload(QuotationRequest.quotations)
                .selectinload(Quotation.items),
                selectinload(QuotationRequest.quotations).selectinload(Quotation.vendor),
            )
            .where(QuotationRequest.id == request_id)
        )
        if request is None:
            raise HTTPException(status_code=404, detail="Quotation request not found")
        return request

    def list_for_opening(self, opening_id: int) -> list[QuotationRequest]:
        return list(
            self.db.scalars(
                select(QuotationRequest)
                .options(selectinload(QuotationRequest.quotations))
                .where(QuotationRequest.branch_opening_id == opening_id)
                .order_by(QuotationRequest.id)
            ).all()
        )

    def add_item(self, request_id: int, data: RequestItemCreate) -> QuotationRequest:
        request = self.get(request_id)
        request.items.append(
            QuotationRequestItem(
                category=data.category,
                description=data.description,
                quantity=data.quantity,
                unit=data.unit,
            )
        )
        self.db.commit()
        return self.get(request_id)

    def add_quotation(self, request_id: int, data: QuotationCreate, actor: User) -> Quotation:
        request = self.get(request_id)
        if not request.items:
            raise HTTPException(
                status_code=409, detail="Add request items before submitting quotations"
            )
        vendor = self.db.get(Vendor, data.vendor_id)
        if vendor is None:
            raise HTTPException(status_code=422, detail="Vendor does not exist")
        duplicate = self.db.scalar(
            select(Quotation.id).where(
                Quotation.request_id == request_id,
                Quotation.vendor_id == data.vendor_id,
            )
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="Vendor already quoted for this request")

        quotation = Quotation(
            request_id=request_id,
            vendor_id=data.vendor_id,
            quotation_date=data.quotation_date or date.today(),
            remarks=data.remarks,
        )
        total = Decimal("0")
        for item in data.items:
            amount = Decimal(str(item.quantity)) * Decimal(str(item.rate))
            final = amount + (amount * (Decimal(str(item.tax)) / Decimal("100")))
            total += final
            quotation.items.append(
                QuotationItem(
                    category=item.category,
                    description=item.description,
                    quantity=item.quantity,
                    unit=item.unit,
                    rate=item.rate,
                    amount=amount,
                    tax=item.tax,
                    final_amount=final,
                )
            )
        quotation.total_amount = total
        self.db.add(quotation)
        request.status = QuotationRequestStatus.SUBMITTED
        self.db.flush()
        self.db.add(
            AuditEvent(
                branch_opening_id=request.branch_opening_id,
                entity_type="quotations",
                entity_id=str(quotation.id),
                action="QUOTATION_SUBMITTED",
                user_id=actor.id,
                new_value=str(total),
            )
        )
        self.db.commit()
        return quotation

    def comparison(self, request_id: int) -> VendorComparison:
        request = self.get(request_id)
        rows = []
        for quotation in request.quotations:
            rows.append(
                VendorComparisonRow(
                    quotation_id=quotation.id,
                    vendor=quotation.vendor,
                    total_amount=float(quotation.total_amount or 0),
                    status=str(quotation.status),
                )
            )
        rows.sort(key=lambda r: r.total_amount)
        for index, row in enumerate(rows):
            row.rank = index + 1

        amounts = [r.total_amount for r in rows if r.total_amount > 0]
        response = VendorComparison(
            request_id=request_id,
            rows=rows,
            selected_vendor_id=request.selected_vendor_id,
        )
        if amounts:
            response.lowest_amount = amounts[0]
            response.highest_amount = amounts[-1]
            response.difference = amounts[-1] - amounts[0]
            response.average_amount = sum(amounts) / len(amounts)
            response.savings_from_l1 = round(
                (amounts[-1] - amounts[0]) / amounts[-1] * 100, 2
            ) if amounts[-1] else None
        return response

    def select_vendor(
        self, request_id: int, data: SelectVendorRequest, actor: User
    ) -> QuotationRequest:
        request = self.get(request_id)
        vendor = self.db.get(Vendor, data.vendor_id)
        if vendor is None:
            raise HTTPException(status_code=422, detail="Vendor does not exist")
        quoted = self.db.scalar(
            select(Quotation.id).where(
                Quotation.request_id == request_id,
                Quotation.vendor_id == data.vendor_id,
            )
        )
        if quoted is None:
            raise HTTPException(
                status_code=409,
                detail="Selected vendor has no quotation for this request",
            )
        old = request.selected_vendor_id
        request.selected_vendor_id = data.vendor_id
        request.status = QuotationRequestStatus.APPROVED
        for quotation in request.quotations:
            if quotation.vendor_id == data.vendor_id:
                quotation.status = QuotationStatus.ACCEPTED
        self.approvals.request(
            opening_id=request.branch_opening_id,
            entity_type="quotation_requests",
            entity_id=str(request_id),
            approval_type=ApprovalType.QUOTATION,
            requested_by=actor,
            amount=float(next(q.total_amount for q in request.quotations if q.vendor_id == data.vendor_id)),
            comments=data.comments,
        )
        self.db.add(
            AuditEvent(
                branch_opening_id=request.branch_opening_id,
                entity_type="quotation_requests",
                entity_id=str(request_id),
                action="VENDOR_SELECTED",
                user_id=actor.id,
                old_value=str(old) if old else None,
                new_value=str(data.vendor_id),
                comments=data.comments,
            )
        )
        self.db.commit()
        return self.get(request_id)