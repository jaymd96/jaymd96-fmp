"""jaymd96-fmp — Python client for the Financial Modeling Prep API with DuckDB caching."""

from fmp.client import FMPClient
from fmp._exceptions import (
    AuthenticationError,
    FMPError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

__version__ = "0.1.0"
__all__ = [
    "FMPClient",
    "FMPError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "__version__",
]
