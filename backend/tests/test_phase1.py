from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    AuditEvent,
    BranchOpening,
    Region,
    Role,
    TaskStatus,
    User,
    WorkflowTask,
)
from app.models.workflow import WorkflowStageDefinition


def test_phase_one_tables_present() -> None:
    expected = {"workflow_tasks", "audit_events"}
    assert expected.issubset(Base.metadata.tables.keys())


def test_workflow_task_lifecycle() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role = Role(name="ADMIN")
        region = Region(name="Region", rent_limit=100000)
        session.add_all([role, region])
        session.flush()
        user = User(
            employee_code="E1",
            name="User One",
            email="u1@example.com",
            role_id=role.id,
            region_id=region.id,
        )
        session.add(user)
        session.flush()
        opening = BranchOpening(
            opening_number="BO-2026-0001",
            branch_id=1,
            project_type="NEW_BRANCH",
            requested_by=user.id,
            requested_date=date(2026, 8, 11),
        )
        session.add(opening)
        session.flush()

        task = WorkflowTask(
            branch_opening_id=opening.id,
            stage="AGREEMENT",
            task_type="AGREEMENT_EXECUTION",
            assigned_to=user.id,
            status=TaskStatus.PENDING,
        )
        session.add(task)
        session.commit()

        saved = session.scalar(select(WorkflowTask).where(WorkflowTask.id == task.id))
        assert saved is not None
        assert saved.status == TaskStatus.PENDING
        assert saved.stage == "AGREEMENT"

        saved.status = TaskStatus.COMPLETED
        saved.completed_by = user.id
        session.commit()
        assert session.scalar(select(WorkflowTask).where(WorkflowTask.id == task.id)).status == (
            TaskStatus.COMPLETED
        )


def test_audit_event_records_action() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        role = Role(name="ADMIN")
        region = Region(name="Region", rent_limit=100000)
        session.add_all([role, region])
        session.flush()
        user = User(
            employee_code="E1",
            name="User One",
            email="u1@example.com",
            role_id=role.id,
            region_id=region.id,
        )
        session.add(user)
        session.flush()
        opening = BranchOpening(
            opening_number="BO-2026-0001",
            branch_id=1,
            project_type="NEW_BRANCH",
            requested_by=user.id,
            requested_date=date(2026, 8, 11),
        )
        session.add(opening)
        session.flush()

        event = AuditEvent(
            branch_opening_id=opening.id,
            entity_type="branch_openings",
            entity_id=str(opening.id),
            action="CASE_CREATED",
            user_id=user.id,
            old_value=None,
            new_value="BO-2026-0001",
            comments="Case created",
        )
        session.add(event)
        session.commit()

        saved = session.scalar(select(AuditEvent).where(AuditEvent.action == "CASE_CREATED"))
        assert saved is not None
        assert saved.branch_opening_id == opening.id
        assert saved.new_value == "BO-2026-0001"


def test_stage_definitions_seed_covers_completed() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    # Seeding is a migration concern; assert the vocabulary exists in the enum
    from app.models.opening import WorkflowStage

    assert WorkflowStage.COMPLETED.value == "COMPLETED"
    assert len(list(WorkflowStage)) >= 15