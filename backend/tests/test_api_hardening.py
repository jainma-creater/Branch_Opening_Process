from starlette.requests import Request

from app.core.config import settings
from app.core.ratelimit import reset_rate_limits
from app.main import generic_exception_handler


def test_security_headers_present(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "no-referrer"


def test_request_id_header_echoed(client) -> None:
    response = client.get("/api/v1/health")
    assert response.headers.get("x-request-id")


def test_request_body_size_limit(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "max_request_body_bytes", 100)
    response = client.post(
        "/api/v1/auth/login",
        json={"login": "x@example.com", "password": "p" * 500},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "Request body too large"


def test_rate_limit_returns_429(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_requests", 3)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 3600)
    monkeypatch.setattr(settings, "rate_limit_trusted_hosts", "")
    try:
        statuses = []
        for _ in range(4):
            response = client.get("/api/v1/reports/summary")
            statuses.append(response.status_code)
        assert statuses == [401, 401, 401, 429]
    finally:
        reset_rate_limits()


def test_generic_500_handler_does_not_leak_details() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/boom",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
        "server": ("test", 80),
    }
    request = Request(scope)
    response = generic_exception_handler(request, RuntimeError("internal-detail"))
    assert response.status_code == 500
    body = response.body.decode()
    assert "Internal server error" in body
    assert "internal-detail" not in body


def test_health_db_reachable(client) -> None:
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "reachable"


def test_user_password_min_length(client) -> None:
    token = admin_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/v1/auth/users",
        json={
            "employee_code": "newbie1",
            "name": "New User",
            "email": "newbie1@example.com",
            "password": "short",
            "role_id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 422


def admin_login(client) -> str:
    from conftest import admin_token

    return admin_token(client)