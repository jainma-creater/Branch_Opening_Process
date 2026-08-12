from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.openings import _detail
from app.db.session import get_db
from app.models import BranchOpening, User
from app.schemas.openings import OpeningDetailed
from app.schemas.workflow import (
    SendBackRequest,
    TaskComplete,
    TaskRead,
    TransitionRequest,
)
from app.services.openings import OpeningService
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/workflow", tags=["Workflow"])


@router.post("/openings/{opening_id}/transition", response_model=OpeningDetailed)
def transition(
    opening_id: int,
    data: TransitionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OpeningDetailed:
    opening = OpeningService(db).get(opening_id)
    advanced = WorkflowService(db).transition(opening, data.target_stage, user, data.comments)
    return _detail(advanced, db)


@router.post("/openings/{opening_id}/send-back", response_model=OpeningDetailed)
def send_back(
    opening_id: int,
    data: SendBackRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OpeningDetailed:
    opening = OpeningService(db).get(opening_id)
    sent = WorkflowService(db).send_back(opening, user, data.comments if data else None)
    return _detail(sent, db)


@router.get("/openings/{opening_id}/tasks", response_model=list[TaskRead])
def opening_tasks(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TaskRead]:
    OpeningService(db).get(opening_id)
    return WorkflowService(db).task_list(opening_id)


@router.get("/openings/{opening_id}/targets")
def available_targets(
    opening_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    opening = OpeningService(db).get(opening_id)
    return {
        "current_stage": opening.current_stage,
        "targets": WorkflowService(db).available_targets(opening),
    }


@router.get("/tasks/my", response_model=list[TaskRead])
def my_tasks(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskRead]:
    return WorkflowService(db).my_tasks(user, status_filter)


@router.post("/tasks/{task_id}/start", response_model=TaskRead)
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskRead:
    return WorkflowService(db).start_task(task_id, user)


@router.post("/tasks/{task_id}/complete", response_model=TaskRead)
def complete_task(
    task_id: int,
    data: TaskComplete | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskRead:
    return WorkflowService(db).complete_task(
        task_id, user, data.remarks if data else None
    )