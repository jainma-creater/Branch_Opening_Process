from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RegionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    rent_limit: Decimal | None = Field(default=None, ge=0)


class RegionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    rent_limit: Decimal | None = Field(default=None, ge=0)


class RegionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rent_limit: Decimal | None
    area_count: int = 0
    branch_count: int = 0


class AreaCreate(BaseModel):
    region_id: int
    name: str = Field(min_length=1, max_length=120)
    rent_limit: Decimal | None = Field(default=None, ge=0)


class AreaUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    rent_limit: Decimal | None = Field(default=None, ge=0)


class AreaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    region_id: int
    name: str
    rent_limit: Decimal | None
    branch_count: int = 0


class BranchCreate(BaseModel):
    area_id: int
    name: str = Field(min_length=1, max_length=120)
    branch_code: str = Field(min_length=1, max_length=50)
    rent_limit: Decimal | None = Field(default=None, ge=0)


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    branch_code: str | None = Field(default=None, min_length=1, max_length=50)
    rent_limit: Decimal | None = Field(default=None, ge=0)


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    area_id: int
    name: str
    branch_code: str
    rent_limit: Decimal | None