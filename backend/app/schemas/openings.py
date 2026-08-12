from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.opening import CaseStatus, WorkflowStage


class OpeningCreate(BaseModel):
    branch_id: int
    project_type: str = Field(min_length=1, max_length=30)
    business_reason: str | None = Field(default=None, max_length=500)
    requested_by: int | None = None
    requested_date: date
    tentative_operations_date: date | None = None
    agreement_commencement_date: date | None = None


class OpeningUpdate(BaseModel):
    project_type: str | None = None
    business_reason: str | None = None
    tentative_operations_date: date | None = None
    agreement_commencement_date: date | None = None


class OpeningStatusUpdate(BaseModel):
    case_status: CaseStatus


class OpeningAssign(BaseModel):
    assigned_to: int


class WorkflowInstanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stage: "WorkflowStageDefRead | None" = None
    status: str
    assigned_to: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WorkflowStageDefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    sequence: int


class StageStatusRead(WorkflowStageDefRead):
    status: str
    assigned_to: int | None = None


class BranchBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    branch_code: str


class AreaBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class RegionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class OpeningRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    opening_number: str
    branch: BranchBrief
    region: "RegionBrief | None" = None
    area: "AreaBrief | None" = None
    project_type: str
    business_reason: str | None = None
    requested_by: int | None = None
    assigned_to: int | None = None
    requested_date: date
    tentative_operations_date: date | None = None
    agreement_commencement_date: date | None = None
    actual_opening_date: date | None = None
    current_stage: WorkflowStage
    case_status: CaseStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    workflow_instances: list[WorkflowInstanceRead] = []


class OpeningDetailed(OpeningRead):
    pending_stages: list[StageStatusRead] = []
    completed_stages: list[StageStatusRead] = []
    pending_tasks: int = 0
