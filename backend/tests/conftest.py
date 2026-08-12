from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models import Region, User

_TEST_ENGINE = None
_TEST_FACTORY = None


def _test_session() -> Session:
    return _TEST_FACTORY()


@pytest.fixture()
def db_engine():
    global _TEST_ENGINE, _TEST_FACTORY
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    _TEST_ENGINE = engine
    _TEST_FACTORY = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield engine
    _TEST_ENGINE = None
    _TEST_FACTORY = None


@pytest.fixture()
def client(db_engine) -> Generator[TestClient, None, None]:
    def override_get_db():
        db = _test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides.clear()
    from app.db.session import get_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def login(client: TestClient, login_id: str, password: str = "password123") -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"login": login_id, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def ensure_user(role_name: str, employee_code: str, password: str = "password123", **kwargs) -> User:
    """Create (or reset) a user in the test DB directly."""
    session = _test_session()
    try:
        from app.models import Role

        role = session.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            role = Role(name=role_name)
            session.add(role)
            session.flush()
        user = session.scalar(select(User).where(User.employee_code == employee_code))
        if user is None:
            user = User(
                employee_code=employee_code,
                name=kwargs.get("name", f"{employee_code} User"),
                email=kwargs.get("email", f"{employee_code}@example.com"),
                role_id=role.id,
                password_hash=hash_password(password),
                is_active=kwargs.get("is_active", True),
            )
            session.add(user)
        else:
            user.password_hash = hash_password(password)
            user.is_active = kwargs.get("is_active", True)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def admin_token(client: TestClient) -> str:
    ensure_user("SUPER_ADMIN", "super_admin")
    return login(client, "super_admin@example.com")


def org_structure(client: TestClient) -> dict:
    """Region -> Area -> Branch via API; returns ids + admin token."""
    token = admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/organization/regions",
        json={"name": "Madhya Pradesh", "rent_limit": 85000},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    region_id = r.json()["id"]

    r = client.post(
        "/api/v1/organization/areas",
        json={"region_id": region_id, "name": "Indore", "rent_limit": 25000},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    area_id = r.json()["id"]

    r = client.post(
        "/api/v1/organization/branches",
        json={
            "area_id": area_id,
            "name": "Khandwa",
            "branch_code": "SMHFC_B00145",
            "rent_limit": 12000,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    branch_id = r.json()["id"]

    return {"region_id": region_id, "area_id": area_id, "branch_id": branch_id, "token": token}


def seed_existing_org(**values) -> None:
    """Create org rows directly (no API) for fixture setups."""
    from app.models import Area, Branch

    session = _test_session()
    try:
        region = Region(name=values["region"], rent_limit=values.get("region_limit"))
        session.add(region)
        session.flush()
        area = Area(region_id=region.id, name=values["area"], rent_limit=values.get("area_limit"))
        session.add(area)
        session.flush()
        branch = Branch(
            area_id=area.id,
            name=values["branch"],
            branch_code=values["branch_code"],
            rent_limit=values.get("branch_limit"),
        )
        session.add(branch)
        session.commit()
        result = {"region_id": region.id, "area_id": area.id, "branch_id": branch.id}
        return result
    finally:
        session.close()