from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Area, Branch, BranchOpening, Region, Role, User, WorkflowStageDefinition


def test_core_schema_contains_phase_two_tables() -> None:
    expected = {
        "regions",
        "areas",
        "branches",
        "roles",
        "users",
        "branch_openings",
        "workflow_stage_definitions",
        "workflow_instances",
    }

    assert expected.issubset(Base.metadata.tables.keys())


def test_create_branch_opening_with_organization_and_requester() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role = Role(name="ADMIN")
        region = Region(name="Madhya Pradesh", rent_limit=Decimal("85000.00"))
        session.add_all([role, region])
        session.flush()

        area = Area(region_id=region.id, name="Indore", rent_limit=Decimal("25000.00"))
        session.add(area)
        session.flush()

        user = User(
            employee_code="5288",
            name="Sanjay Gupta",
            email="sanjay@example.com",
            role_id=role.id,
            region_id=region.id,
            area_id=area.id,
        )
        session.add(user)
        session.flush()

        branch = Branch(
            area_id=area.id,
            name="Khandwa",
            branch_code="SMHFC_B00145",
            rent_limit=Decimal("12000.00"),
        )
        session.add(branch)
        session.flush()

        opening = BranchOpening(
            opening_number="BO-2026-0001",
            branch_id=branch.id,
            project_type="NEW_BRANCH",
            business_reason="Business expansion",
            requested_by=user.id,
            requested_date=date(2026, 8, 11),
        )
        session.add(opening)
        session.commit()

        saved = session.scalar(select(BranchOpening).where(BranchOpening.opening_number == "BO-2026-0001"))
        assert saved is not None
        assert saved.branch.name == "Khandwa"
        assert saved.requested_by == user.id
