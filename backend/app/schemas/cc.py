from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.cc import CCRequestStatus


class CCRequestItemCreate(BaseModel):
    branch_opening_id: int
    requested_amount: float = Field(ge=0)
    remarks: str | None = Field(default=None, max_length=500)


class CCRequestCreate(BaseModel):
    remarks: str | None = Field(default=None, max_length=1000)
    items: list[CCRequestItemCreate] = []


class CCItemDecision(BaseModel):
    branch_opening_id: int
    approved_amount: float = Field(ge=0)


class CCReview(BaseModel):
    decision: str  # APPROVED | REJECTED | SENT_BACK
    items: list[CCItemDecision] = []
    comments: str | None = Field(default=None, max_length=1000)


class CCRequestItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cc_request_id: int
    branch_opening_id: int
    requested_amount: float
    approved_amount: float | None = None
    remarks: str | None = None


class CCRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_code: str | None = None
    status: CCRequestStatus
    requested_by: int | None = None
    cc_reviewer_id: int | None = None
    md_reviewer_id: int | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[CCRequestItemRead] = []
