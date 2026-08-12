from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import User
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def authenticate(self, data: LoginRequest) -> User:
        user = self.repo.find_by_login(data.login.strip())
        if user is None or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        return user

    def create_user(self, data: UserCreate) -> User:
        if self.repo.find_by_email(data.email.lower().strip()):
            raise HTTPException(status_code=409, detail="Email already registered")
        if self.repo.find_by_employee_code(data.employee_code.strip()):
            raise HTTPException(status_code=409, detail="Employee code already registered")
        if not self.repo.get_role(data.role_id):
            raise HTTPException(status_code=422, detail="Role does not exist")

        user = User(
            employee_code=data.employee_code.strip(),
            name=data.name.strip(),
            email=data.email.lower().strip(),
            password_hash=hash_password(data.password),
            role_id=data.role_id,
            region_id=data.region_id,
            area_id=data.area_id,
            is_active=data.is_active,
        )
        return self.repo.add(user)

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.repo.get(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(user, field, value)
        return self.repo.save(user)