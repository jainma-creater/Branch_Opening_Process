from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserRead"


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, description="Employee code or email")
    password: str = Field(min_length=1)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code: str
    name: str
    email: str
    role: "RoleRead | None" = None
    region_id: int | None = None
    area_id: int | None = None
    is_active: bool


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class UserCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role_id: int
    region_id: int | None = None
    area_id: int | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role_id: int | None = None
    region_id: int | None = None
    area_id: int | None = None
    is_active: bool | None = None


TokenResponse.model_rebuild()