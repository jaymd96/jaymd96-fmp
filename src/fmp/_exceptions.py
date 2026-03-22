"""FMP client exceptions."""

from __future__ import annotations


class FMPError(Exception):
    """Base exception for FMP client errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict | None = None,
    ):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class AuthenticationError(FMPError):
    """Raised on HTTP 401 — invalid API key."""


class ForbiddenError(FMPError):
    """Raised on HTTP 403 — plan limit exceeded."""


class RateLimitError(FMPError):
    """Raised on HTTP 429 after retries exhausted."""


class NotFoundError(FMPError):
    """Raised on HTTP 404 — endpoint not found."""


class ServerError(FMPError):
    """Raised on HTTP 5xx — server-side error."""
