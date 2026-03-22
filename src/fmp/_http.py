"""HTTP transport layer with retry, rate-limiting, and error mapping."""

from __future__ import annotations

import threading
import time

import httpx

from fmp._config import BASE_URL
from fmp._exceptions import (
    AuthenticationError,
    FMPError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)


class TokenBucket:
    """Thread-safe token-bucket rate limiter."""

    def __init__(self, rate: float) -> None:
        self._rate = rate  # tokens per second
        self._tokens = rate
        self._max = rate
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last
                self._last = now
                self._tokens = min(self._max, self._tokens + elapsed * self._rate)
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
            time.sleep(0.05)


class HTTPClient:
    """Thin wrapper around ``httpx.Client`` with auth, retry, and rate-limiting."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit: float | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={"apikey": api_key},
            timeout=timeout,
        )
        self._max_retries = max_retries
        self._limiter = TokenBucket(rate_limit) if rate_limit else None

    def get(self, path: str, params: dict | None = None) -> list[dict]:
        """Send a GET request with retry on 429 and exponential backoff."""
        if self._limiter:
            self._limiter.acquire()

        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            resp = self._client.get(path, params=params)

            if resp.status_code == 200:
                data = resp.json()
                # FMP returns error objects as dicts, not lists
                if isinstance(data, dict) and "Error Message" in data:
                    raise FMPError(data["Error Message"], status_code=resp.status_code)
                # Normalise to list[dict]
                if isinstance(data, dict):
                    return [data]
                return data

            if resp.status_code == 429:
                delay = (2**attempt) * 1.0
                last_exc = RateLimitError(
                    "Rate limited", status_code=429, response=_safe_json(resp)
                )
                time.sleep(delay)
                continue

            _raise_for_status(resp)

        # Exhausted retries on 429
        raise last_exc or RateLimitError("Rate limited after retries", status_code=429)

    def close(self) -> None:
        self._client.close()


def _safe_json(resp: httpx.Response) -> dict | None:
    try:
        return resp.json()
    except Exception:
        return None


def _raise_for_status(resp: httpx.Response) -> None:
    body = _safe_json(resp)
    msg = ""
    if isinstance(body, dict):
        msg = body.get("Error Message", resp.text)
    else:
        msg = resp.text

    if resp.status_code == 401:
        raise AuthenticationError(msg, status_code=401, response=body)
    if resp.status_code == 403:
        raise ForbiddenError(msg, status_code=403, response=body)
    if resp.status_code == 404:
        raise NotFoundError(msg, status_code=404, response=body)
    if resp.status_code >= 500:
        raise ServerError(msg, status_code=resp.status_code, response=body)
    raise FMPError(msg, status_code=resp.status_code, response=body)
