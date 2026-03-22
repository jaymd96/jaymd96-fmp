from __future__ import annotations


class SearchMixin:
    """Search and screener endpoints."""

    def search_symbol(
        self,
        query: str,
        *,
        limit: int | None = None,
        exchange: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"query": query}
        if limit is not None:
            params["limit"] = limit
        if exchange is not None:
            params["exchange"] = exchange
        return self._request(
            "search-symbol",
            params=params,
            ttl_category="screener",
            force_refresh=force_refresh,
        )

    def search_name(
        self,
        query: str,
        *,
        limit: int | None = None,
        exchange: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"query": query}
        if limit is not None:
            params["limit"] = limit
        if exchange is not None:
            params["exchange"] = exchange
        return self._request(
            "search-name",
            params=params,
            ttl_category="screener",
            force_refresh=force_refresh,
        )

    def search_cik(
        self, cik: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "search-cik",
            params={"cik": cik},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def search_cusip(
        self, cusip: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "search-cusip",
            params={"cusip": cusip},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def search_isin(
        self, isin: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "search-isin",
            params={"isin": isin},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )

    def screener(
        self,
        *,
        market_cap_more_than: int | None = None,
        market_cap_lower_than: int | None = None,
        price_more_than: float | None = None,
        price_lower_than: float | None = None,
        volume_more_than: int | None = None,
        volume_lower_than: int | None = None,
        beta_more_than: float | None = None,
        beta_lower_than: float | None = None,
        dividend_more_than: float | None = None,
        dividend_lower_than: float | None = None,
        sector: str | None = None,
        industry: str | None = None,
        country: str | None = None,
        exchange: str | None = None,
        is_etf: bool | None = None,
        is_actively_trading: bool | None = None,
        limit: int | None = None,
        page: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        # Map snake_case keyword arguments to camelCase API parameters.
        mapping = {
            "market_cap_more_than": "marketCapMoreThan",
            "market_cap_lower_than": "marketCapLowerThan",
            "price_more_than": "priceMoreThan",
            "price_lower_than": "priceLowerThan",
            "volume_more_than": "volumeMoreThan",
            "volume_lower_than": "volumeLowerThan",
            "beta_more_than": "betaMoreThan",
            "beta_lower_than": "betaLowerThan",
            "dividend_more_than": "dividendMoreThan",
            "dividend_lower_than": "dividendLowerThan",
            "sector": "sector",
            "industry": "industry",
            "country": "country",
            "exchange": "exchange",
            "is_etf": "isEtf",
            "is_actively_trading": "isActivelyTrading",
            "limit": "limit",
            "page": "page",
        }
        local = locals()
        params: dict = {}
        for py_name, api_name in mapping.items():
            value = local[py_name]
            if value is not None:
                params[api_name] = value
        return self._request(
            "company-screener",
            params=params or None,
            ttl_category="screener",
            force_refresh=force_refresh,
        )

    def search_exchange_variants(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "search-exchange-variants",
            params={"symbol": symbol},
            ttl_category="company_profiles",
            force_refresh=force_refresh,
        )
