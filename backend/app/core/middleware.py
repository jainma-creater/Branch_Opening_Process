"""Application-wide request middleware.

Pure-ASGI (not BaseHTTPMiddleware): exceptions raised downstream are
re-raised so FastAPI's exception handlers keep full control, while the
middleware still logs every request and attaches response headers.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.ratelimit import check_rate_limit

logger = logging.getLogger("app.request")


class RequestContextMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    @staticmethod
    def _client_host(scope: dict) -> str:
        client = scope.get("client")
        return client[0] if client else "unknown"

    def _rate_limited(self, client_ip: str) -> tuple[bool, HTTPException | None]:
        if not settings.rate_limit_enabled:
            return False, None
        if settings.debug:
            return False, None
        if client_ip in settings.rate_limit_trusted_host_list:
            return False, None
        try:
            check_rate_limit(
                f"api:{client_ip}",
                settings.rate_limit_requests,
                settings.rate_limit_window_seconds,
            )
        except HTTPException as exc:
            return True, exc
        return False, None

    def _body_too_large(self, headers: list) -> tuple[bool, int]:
        max_bytes = settings.max_request_body_bytes
        if max_bytes <= 0:
            return False, 0
        for name, value in headers:
            if name.lower() == b"content-length":
                try:
                    length = int(value)
                except ValueError:
                    return False, 0
                return length > max_bytes, length
        return False, 0

    async def __call__(self, scope: dict, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex
        client_ip = self._client_host(scope)
        path = scope.get("path", "")
        method = scope.get("method", "")
        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                nonlocal status_code
                status_code = message.get("status", status_code)
                message.setdefault("headers", []).extend(
                    [
                        (b"x-request-id", request_id.encode()),
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                        (b"x-xss-protection", b"0"),
                    ]
                )
            await send(message)

        async def reject(json_response: JSONResponse, code: int) -> None:
            nonlocal status_code
            status_code = code
            await json_response(scope, receive, send_wrapper)

        if self._rate_limited(client_ip)[0]:
            await reject(
                JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests, please retry later"},
                    headers={"Retry-After": str(settings.rate_limit_window_seconds)},
                ),
                429,
            )
            self._log(request_id, method, path, client_ip, started, status_code)
            return

        too_large, _ = self._body_too_large(scope.get("headers") or [])
        if too_large:
            await reject(
                JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                ),
                413,
            )
            self._log(request_id, method, path, client_ip, started, status_code)
            return

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            self._log(request_id, method, path, client_ip, started, status_code, error=True)
            raise
        self._log(request_id, method, path, client_ip, started, status_code)

    def _log(
        self,
        request_id: str,
        method: str,
        path: str,
        client_ip: str,
        started: float,
        status_code: int,
        error: bool = False,
    ) -> None:
        duration_ms = (time.perf_counter() - started) * 1000
        extra = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "duration_ms": round(duration_ms, 2),
        }
        if error:
            logger.exception("request failed", extra=extra)
        else:
            logger.info("request %s", status_code, extra=extra)