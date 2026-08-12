from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import create_access_token
from app.db.session import get_db
from app.models import User
from app.models.roles import RoleCode
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserRead, UserUpdate
from app.services.users import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])

ADMIN_ROLES = (RoleCode.SUPER_ADMIN.value, RoleCode.ADMIN.value)


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        employee_code=user.employee_code,
        name=user.name,
        email=user.email,
        role=user.role,
        region_id=user.region_id,
        area_id=user.area_id,
        is_active=user.is_active,
    )


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.name if user.role else ""),
        user=_user_read(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = UserService(db).authenticate(data)
    return _token_response(user)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return _user_read(current_user)


@router.get("/users", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ROLES)),
) -> list[UserRead]:
    return [_user_read(u) for u in UserService(db).repo.list_users()]


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ROLES)),
) -> UserRead:
    return _user_read(UserService(db).create_user(data))


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ROLES)),
) -> UserRead:
    return _user_read(UserService(db).update_user(user_id, data))