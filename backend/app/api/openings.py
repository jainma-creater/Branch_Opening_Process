from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import BranchOpening, TaskStatus, User, WorkflowTask
from app.models.opening import CaseStatus, WorkflowStage
from app.models.roles import RoleCode
from app.schemas.openings import (
    OpeningAssign,
    OpeningCreate,
    OpeningDetailed,
    OpeningRead,
    OpeningStatusUpdate,
    OpeningUpdate,
)
from app.services.openings import OpeningService

router = APIRouter(prefix="/openings", tags=["Branch Openings"])

CREATORS = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value, RoleCode.BUSINESS_TEAM.value, RoleCode.REGIONAL_ADMIN.value)
APPROVERS = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


def _detail(opening: BranchOpening, db: Session) -> OpeningDetailed:
    from app.schemas.openings import (
        AreaBrief,
        RegionBrief,
        StageStatusRead,
        WorkflowInstanceRead,
        WorkflowStageDefRead,
    )

    branch = opening.branch
    area = branch.area
    region = area.region if area else None
    instances = sorted(opening.workflow_instances, key=lambda i: i.stage.sequence)

    completed = [
        StageStatusRead(id=i.stage.id, code=i.stage.code, name=i.stage.name, sequence=i.stage.sequence, status=i.status, assigned_to=i.assigned_to)
        for i in instances
        if i.status in ("APPROVED", "COMPLETED")
    ]
    pending = [
        StageStatusRead(id=i.stage.id, code=i.stage.code, name=i.stage.name, sequence=i.stage.sequence, status=i.status, assigned_to=i.assigned_to)
        for i in instances
        if i.status not in ("APPROVED", "COMPLETED")
    ]
    pending_tasks = len(
        db.scalars(
            select(WorkflowTask).where(
                WorkflowTask.branch_opening_id == opening.id,
                WorkflowTask.status.in_([TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]),
            )
        ).all()
    )
    return OpeningDetailed(
        id=opening.id,
        opening_number=opening.opening_number,
        branch=branch,
        region=RegionBrief(id=region.id, name=region.name) if region else None,
        area=AreaBrief(id=area.id, name=area.name) if area else None,
        project_type=opening.project_type,
        business_reason=opening.business_reason,
        requested_by=opening.requested_by,
        assigned_to=opening.assigned_to,
        requested_date=opening.requested_date,
        tentative_operations_date=opening.tentative_operations_date,
        agreement_commencement_date=opening.agreement_commencement_date,
        actual_opening_date=opening.actual_opening_date,
        current_stage=opening.current_stage,
        case_status=opening.case_status,
        created_at=opening.created_at,
        updated_at=opening.updated_at,
        completed_at=opening.completed_at,
        workflow_instances=[
            WorkflowInstanceRead(id=i.id, stage=WorkflowStageDefRead(id=i.stage.id, code=i.stage.code, name=i.stage.name, sequence=i.stage.sequence), status=i.status, assigned_to=i.assigned_to, started_at=i.started_at, completed_at=i.completed_at)
            for i in instances
        ],
        pending_stages=pending,
        completed_stages=completed,
        pending_tasks=pending_tasks,
    )


@router.get("", response_model=list[OpeningRead])
def list_openings(
    region_id: int | None = None,
    area_id: int | None = None,
    branch_id: int | None = None,
    case_status: CaseStatus | None = None,
    current_stage: WorkflowStage | None = None,
    requested_by: int | None = None,
    assigned_to: int | None = None,
    search: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OpeningRead]:
    filters = {
        "region_id": region_id,
        "area_id": area_id,
        "branch_id": branch_id,
        "case_status": case_status.value if case_status else None,
        "current_stage": current_stage.value if current_stage else None,
        "requested_by": requested_by,
        "assigned_to": assigned_to,
        "search": search,
        "limit": limit,
        "offset": offset,
    }
    if user.role and user.role.name == RoleCode.REGIONAL_ADMIN.value and user.region_id:
        filters["region_id"] = user.region_id
    return _read_list(OpeningService(db).list(filters))


def _read_list(openings: list[BranchOpening]) -> list[OpeningRead]:
    from app.schemas.openings import AreaBrief, RegionBrief

    result = []
    for opening in openings:
        branch = opening.branch
        area = branch.area
        region = area.region if area else None
        result.append(
            OpeningRead(
                id=opening.id,
                opening_number=opening.opening_number,
                branch=branch,
                region=RegionBrief(id=region.id, name=region.name) if region else None,
                area=AreaBrief(id=area.id, name=area.name) if area else None,
                project_type=opening.project_type,
                business_reason=opening.business_reason,
                requested_by=opening.requested_by,
                assigned_to=opening.assigned_to,
                requested_date=opening.requested_date,
                tentative_operations_date=opening.tentative_operations_date,
                agreement_commencement_date=opening.agreement_commencement_date,
                actual_opening_date=opening.actual_opening_date,
                current_stage=opening.current_stage,
                case_status=opening.case_status,
                created_at=opening.created_at,
                updated_at=opening.updated_at,
                completed_at=opening.completed_at,
            )
        )
    return result


@router.post("", response_model=OpeningDetailed, status_code=status.HTTP_201_CREATED)
def create_opening(
    data: OpeningCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*CREATORS)),
) -> OpeningDetailed:
    return _detail(OpeningService(db).create(data, actor=user), db)


@router.get("/{opening_id}", response_model=OpeningDetailed)
def get_opening(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OpeningDetailed:
    return _detail(OpeningService(db).get(opening_id), db)


@router.patch("/{opening_id}", response_model=OpeningDetailed)
def update_opening(
    opening_id: int,
    data: OpeningUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*APPROVERS)),
) -> OpeningDetailed:
    return _detail(OpeningService(db).update(opening_id, data), db)


@router.patch("/{opening_id}/status", response_model=OpeningDetailed)
def update_opening_status(
    opening_id: int,
    data: OpeningStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*APPROVERS)),
) -> OpeningDetailed:
    return _detail(OpeningService(db).set_status(opening_id, data, actor=user), db)


@router.post("/{opening_id}/assign", response_model=OpeningDetailed)
def assign_opening(
    opening_id: int,
    data: OpeningAssign,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*APPROVERS)),
) -> OpeningDetailed:
    return _detail(OpeningService(db).assign(opening_id, data, actor=user), db)