"""Idempotent seed data shared between migrations and test fixtures."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role, WorkflowStageDefinition
from app.models.roles import ROLE_SEED

DEFAULT_STAGES = [
    ("REQUIREMENT", "Branch Requirement", 1),
    ("PROPERTY_SEARCH", "Location / Property Search", 2),
    ("PROPERTY_APPROVAL", "Property Approval", 3),
    ("SECURITY_DEPOSIT", "Security Deposit Approval", 4),
    ("LOA", "LOA Request / Issuance", 5),
    ("AGREEMENT", "Agreement Preparation / Execution", 6),
    ("QUOTATION", "Three Quotations", 7),
    ("ACCOUNTS", "Accounts Review", 8),
    ("CC_APPROVAL", "CC Approval", 9),
    ("MD_APPROVAL", "MD Approval", 10),
    ("PAYMENT", "Payment", 11),
    ("INFRASTRUCTURE", "Infrastructure / Fit-out", 12),
    ("OPERATIONAL_READINESS", "Operational Readiness", 13),
    ("OPENING", "Branch Opening", 14),
    ("COMPLETED", "Completed", 15),
]


def seed_stage_definitions(db: Session) -> None:
    existing = {
        r.code for r in db.scalars(select(WorkflowStageDefinition)).all()
    }
    for code, name, sequence in DEFAULT_STAGES:
        if code not in existing:
            db.add(
                WorkflowStageDefinition(code=code, name=name, sequence=sequence)
            )
    db.commit()


def seed_roles(db: Session) -> None:
    existing = {r.name for r in db.scalars(select(Role)).all()}
    for name, description in ROLE_SEED:
        if name not in existing:
            db.add(Role(name=name, description=description))
    db.commit()


def seed_all(db: Session) -> None:
    seed_roles(db)
    seed_stage_definitions(db)