"""In-memory sliding-window rate limiter.

Process-local only; sufficient for single-instance deployments. For
multi-instance setups swap this module for a shared store (e.g. Redis)
without changing the middleware interface.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

_lock = threading.Lock()
_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    """Clear all recorded hits (used by tests)."""
    with _lock:
        _hits.clear()


def check_rate_limit(key: str, limit: int, window_seconds: float) -> None:
    """Record one hit for ``key``; raise 429 when ``limit`` is exceeded."""
    if limit <= 0:
        return
    now = time.monotonic()
    with _lock:
        bucket = _hits[key]
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please retry later",
                headers={"Retry-After": str(int(window_seconds))},
            )
        bucket.append(now)