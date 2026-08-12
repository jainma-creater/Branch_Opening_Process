from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role, User
from app.models.roles import RoleCode


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def find_by_login(self, login: str) -> User | None:
        stmt = select(User).where(
            (User.employee_code == login) | (User.email == login)
        )
        return self.db.scalar(stmt)

    def find_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def find_by_employee_code(self, code: str) -> User | None:
        return self.db.scalar(select(User).where(User.employee_code == code))

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.name)).all())

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_role(self, role_id: int) -> Role | None:
        return self.db.get(Role, role_id)

    def get_role_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))

    def ensure_roles(self) -> None:
        """Idempotent role seeding (used by tests with fresh databases)."""
        existing = {r.name for r in self.db.scalars(select(Role)).all()}
        for code in RoleCode:
            if code.value not in existing:
                self.db.add(Role(name=code.value))
        self.db.commit()