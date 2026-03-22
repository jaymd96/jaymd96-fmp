from __future__ import annotations


def _build_params(**kwargs: object) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


class MarketPerformanceMixin:
    """Sector/industry performance and market movers endpoints."""

    def sector_performance_snapshot(
        self,
        *,
        date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(date=date)
        return self._request(
            "sector-performance-snapshot",
            params=params or None,
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def industry_performance_snapshot(
        self,
        *,
        date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(date=date)
        return self._request(
            "industry-performance-snapshot",
            params=params or None,
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def historical_sector_performance(
        self,
        sector: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(sector=sector)
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "historical-sector-performance",
            params=params,
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def historical_industry_performance(
        self,
        industry: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(industry=industry)
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "historical-industry-performance",
            params=params,
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def sector_pe_snapshot(
        self,
        *,
        date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(date=date)
        return self._request(
            "sector-pe-snapshot",
            params=params or None,
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def industry_pe_snapshot(
        self,
        *,
        date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(date=date)
        return self._request(
            "industry-pe-snapshot",
            params=params or None,
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def historical_sector_pe(
        self,
        sector: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(sector=sector)
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "historical-sector-pe",
            params=params,
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def historical_industry_pe(
        self,
        industry: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(industry=industry)
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "historical-industry-pe",
            params=params,
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def biggest_gainers(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "biggest-gainers",
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def biggest_losers(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "biggest-losers",
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )

    def most_active(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "most-actives",
            ttl_category="market_performance",
            force_refresh=force_refresh,
        )
