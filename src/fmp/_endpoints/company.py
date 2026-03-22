from __future__ import annotations


class CompanyMixin:
    """Company information endpoints."""

    def profile(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "profile",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def profile_cik(
        self, cik: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "profile-cik",
            params={"cik": cik},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def company_notes(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "company-notes",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def stock_peers(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "stock-peers",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def delisted_companies(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "delisted-companies",
            params=params or None,
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def employee_count(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "employee-count",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def historical_employee_count(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "historical-employee-count",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def market_capitalization(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "market-capitalization",
            params={"symbol": symbol},
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def market_capitalization_batch(
        self, symbols: list[str], *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "market-capitalization-batch",
            params={"symbols": ",".join(symbols)},
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def historical_market_capitalization(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "historical-market-capitalization",
            params=params,
            ttl_category="daily_historical",
            force_refresh=force_refresh,
        )

    def shares_float(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "shares-float",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def shares_float_all(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "shares-float-all",
            params=params or None,
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def mergers_acquisitions_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "mergers-acquisitions-latest",
            params=params or None,
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def mergers_acquisitions_search(
        self, name: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "mergers-acquisitions-search",
            params={"name": name},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def key_executives(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "key-executives",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def executive_compensation(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "governance-executive-compensation",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def compensation_benchmark(
        self, *, year: int | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        return self._request(
            "executive-compensation-benchmark",
            params=params or None,
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )
