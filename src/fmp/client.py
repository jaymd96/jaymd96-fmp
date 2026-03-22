"""FMP API client with DuckDB caching."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from fmp._query import QueryBuilder

from fmp._cache import DuckDBCache
from fmp._config import DEFAULT_TTLS
from fmp._exceptions import FMPError
from fmp._http import HTTPClient
from fmp._store import BitemporalStore

from fmp._endpoints.search import SearchMixin
from fmp._endpoints.directory import DirectoryMixin
from fmp._endpoints.company import CompanyMixin
from fmp._endpoints.quotes import QuotesMixin
from fmp._endpoints.financials import FinancialsMixin
from fmp._endpoints.charts import ChartsMixin
from fmp._endpoints.economics import EconomicsMixin
from fmp._endpoints.earnings import EarningsMixin
from fmp._endpoints.transcripts import TranscriptsMixin
from fmp._endpoints.news import NewsMixin
from fmp._endpoints.institutional import InstitutionalMixin
from fmp._endpoints.analyst import AnalystMixin
from fmp._endpoints.market_performance import MarketPerformanceMixin
from fmp._endpoints.technical import TechnicalMixin
from fmp._endpoints.etf_funds import ETFFundsMixin
from fmp._endpoints.sec_filings import SECFilingsMixin
from fmp._endpoints.insider import InsiderMixin
from fmp._endpoints.indexes import IndexesMixin
from fmp._endpoints.market_hours import MarketHoursMixin
from fmp._endpoints.commodities import CommoditiesMixin
from fmp._endpoints.dcf import DCFMixin
from fmp._endpoints.forex import ForexMixin
from fmp._endpoints.crypto import CryptoMixin
from fmp._endpoints.senate import SenateMixin
from fmp._endpoints.esg import ESGMixin
from fmp._endpoints.cot import COTMixin
from fmp._endpoints.fundraisers import FundraisersMixin
from fmp._endpoints.bulk import BulkMixin


class FMPClient(
    SearchMixin,
    DirectoryMixin,
    CompanyMixin,
    QuotesMixin,
    FinancialsMixin,
    ChartsMixin,
    EconomicsMixin,
    EarningsMixin,
    TranscriptsMixin,
    NewsMixin,
    InstitutionalMixin,
    AnalystMixin,
    MarketPerformanceMixin,
    TechnicalMixin,
    ETFFundsMixin,
    SECFilingsMixin,
    InsiderMixin,
    IndexesMixin,
    MarketHoursMixin,
    CommoditiesMixin,
    DCFMixin,
    ForexMixin,
    CryptoMixin,
    SenateMixin,
    ESGMixin,
    COTMixin,
    FundraisersMixin,
    BulkMixin,
):
    """Python client for the Financial Modeling Prep API.

    Args:
        api_key: FMP API key. Falls back to the ``FMP_API_KEY`` env var.
        cache_path: Path to the DuckDB cache file.  Use ``None`` for in-memory.
        ttl_overrides: Override default TTL (seconds) per category.
        timeout: HTTP request timeout in seconds.
        max_retries: Max retry attempts on 429 responses.
        rate_limit: Max requests per second (``None`` = unlimited).
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        cache_path: str | None = "~/.fmp/cache.db",
        ttl_overrides: dict[str, int] | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit: float | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("FMP_API_KEY")
        if not resolved_key:
            raise FMPError(
                "API key required. Pass api_key= or set the FMP_API_KEY env var."
            )

        self._http = HTTPClient(
            resolved_key,
            timeout=timeout,
            max_retries=max_retries,
            rate_limit=rate_limit,
        )
        self._cache = DuckDBCache(cache_path)
        self._store = BitemporalStore(self._cache.connection)
        self._ttls: dict[str, int] = {**DEFAULT_TTLS, **(ttl_overrides or {})}

    # ------------------------------------------------------------------
    # Core plumbing (called by every endpoint mixin)
    # ------------------------------------------------------------------

    def _resolve_ttl(self, category: str) -> int:
        return self._ttls.get(category, self._ttls["default"])

    def _cache_key(self, path: str, params: dict) -> str:
        filtered = {k: v for k, v in sorted(params.items()) if k != "apikey"}
        parts = ":".join(f"{k}={v}" for k, v in filtered.items())
        return f"{path}:{parts}" if parts else path

    def _request(
        self,
        path: str,
        *,
        params: dict | None = None,
        ttl_category: str = "default",
        force_refresh: bool = False,
    ) -> list[dict]:
        """Fetch from cache or API. All endpoint methods delegate here."""
        params = params or {}
        cache_key = self._cache_key(path, params)
        ttl = self._resolve_ttl(ttl_category)

        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        data = self._http.get(path, params=params)
        self._cache.set(cache_key, path, params, data, ttl)
        return data

    # ------------------------------------------------------------------
    # Bulk / concurrency helpers
    # ------------------------------------------------------------------

    def fetch_many(
        self,
        method: Callable[..., list[dict]],
        symbols: list[str],
        *,
        max_workers: int = 10,
        **kwargs: Any,
    ) -> dict[str, list[dict]]:
        """Call *method* for each symbol concurrently.

        Returns a dict keyed by symbol. Failed symbols are omitted (errors
        are collected and re-raised as a single ``FMPError`` if *all* fail).

        Example::

            results = client.fetch_many(client.quote, ["AAPL", "MSFT", "GOOG"])
        """
        results: dict[str, list[dict]] = {}
        errors: dict[str, Exception] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(method, sym, **kwargs): sym for sym in symbols
            }
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    results[sym] = future.result()
                except Exception as exc:
                    errors[sym] = exc

        if errors and not results:
            first = next(iter(errors.values()))
            raise FMPError(
                f"All {len(errors)} requests failed. First error: {first}"
            ) from first

        return results

    def paginate_all(
        self,
        method: Callable[..., list[dict]],
        *,
        limit: int = 100,
        max_pages: int = 100,
        **kwargs: Any,
    ) -> list[dict]:
        """Auto-paginate a paginated endpoint until exhausted.

        Example::

            all_news = client.paginate_all(client.stock_news_latest, limit=100)
        """
        all_results: list[dict] = []
        for page in range(max_pages):
            batch = method(page=page, limit=limit, **kwargs)
            if not batch:
                break
            all_results.extend(batch)
            if len(batch) < limit:
                break
        return all_results

    # ------------------------------------------------------------------
    # Query builder (ontology-driven DataFrame API)
    # ------------------------------------------------------------------

    def query(self) -> QueryBuilder:
        """Start building a cross-dataset query.

        Example::

            df = (client.query()
                .symbols("AAPL", "MSFT")
                .select("close", "volume", "revenue", "net_income")
                .date_range("2023-01-01", "2024-12-31")
                .execute()
            )
        """
        from fmp._query import QueryBuilder
        return QueryBuilder(self._http, self._store, self._ttls)

    def revisions(self, symbol: str, dataset: str, **filters: Any) -> list[dict]:
        """See how data for a symbol changed across fetches.

        Example::

            client.revisions("AAPL", "income_statement", date="2023-09-30", period="FY")
        """
        return self._store.revisions(dataset, symbol, **filters)

    @property
    def store(self) -> BitemporalStore:
        """The underlying :class:`BitemporalStore` instance."""
        return self._store

    # ------------------------------------------------------------------
    # Cache access
    # ------------------------------------------------------------------

    def sql(self, query: str, params: list | None = None) -> list[dict]:
        """Execute arbitrary SQL against the cache database."""
        return self._cache.sql(query, params)

    @property
    def cache(self) -> DuckDBCache:
        """The underlying :class:`DuckDBCache` instance."""
        return self._cache

    def clear_cache(self, endpoint: str | None = None) -> int:
        """Clear cached entries. Returns the number of rows deleted."""
        return self._cache.clear(endpoint)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close HTTP and DuckDB connections."""
        self._http.close()
        self._cache.close()

    def __enter__(self) -> FMPClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
