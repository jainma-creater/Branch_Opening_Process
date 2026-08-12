from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.approval import ApprovalDecision, ApprovalType


class ApprovalRequest(BaseModel):
    entity_type: str = Field(min_length=1, max_length=60)
    entity_id: str | None = Field(default=None, max_length=64)
    approval_type: ApprovalType
    amount: float | None = None
    comments: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decision: ApprovalDecision
    comments: str | None = None
    amount: float | None = None


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    entity_type: str
    entity_id: str | None
    approval_type: ApprovalType
    requested_by: int | None = None
    approver: int | None = None
    requested_at: datetime
    decision: ApprovalDecision | None = None
    decision_at: datetime | None = None
    comments: str | None = None
    amount: float | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_opening_id: int
    stage: str
    task_type: str
    assigned_to: int | None = None
    status: str
    created_at: datetime
    due_at: datetime | None = None
    completed_at: datetime | None = None
    completed_by: int | None = None
    remarks: str | None = None


class TaskComplete(BaseModel):
    remarks: str | None = None


class TransitionRequest(BaseModel):
    target_stage: str = Field(min_length=1, max_length=40)
    comments: str | None = None


class SendBackRequest(BaseModel):
    comments: str | None = None