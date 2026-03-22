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
from fmp._ontology import Grain, list_fields
from fmp._query import QueryBuilder

__version__ = "0.2.0"
__all__ = [
    "FMPClient",
    "FMPError",
    "AuthenticationError",
    "ForbiddenError",
    "Grain",
    "NotFoundError",
    "QueryBuilder",
    "RateLimitError",
    "ServerError",
    "list_fields",
    "__version__",
]
