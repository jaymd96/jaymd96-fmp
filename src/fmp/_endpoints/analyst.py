from __future__ import annotations


def _build_params(**kwargs: object) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


class AnalystMixin:
    """Analyst estimates, ratings, grades, and price target endpoints."""

    def analyst_estimates(
        self,
        symbol: str,
        *,
        period: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol, period=period, page=page, limit=limit)
        return self._request(
            "analyst-estimates",
            params=params,
            ttl_category="analyst",
            force_refresh=force_refresh,
        )

    def ratings_snapshot(
        self,
        symbol: str,
        *,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._request(
            "ratings-snapshot",
            params={"symbol": symbol},
            ttl_category="analyst",
            force_refresh=force_refresh,
        )

    def ratings_historical(
        self,
        symbol: str,
        *,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol, limit=limit)
        return self._request(
            "ratings-historical",
            params=params,
            ttl_category="analyst",
            force_refresh=force_refresh,
        )

    def price_target_summary(
        self,
        symbol: str,
        *,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._request(
            "price-target-summary",
            params={"symbol": symbol},
            ttl_category="analyst",
            force_refresh=force_refresh,
        )

    def price_target_consensus(
        self,
        symbol: str,
        *,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._request(
            "price-target-consensus",
            params={"symbol": symbol},
            ttl_category="analyst",
            force_refresh=force_refresh,
        )

    def grades(
        self,
        symbol: str,
        *,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol, limit=limit)
        return self._request(
            "grades",
            params=params,
            ttl_category="analyst",
            force_refresh=force_refresh,
        )

    def grades_historical(
        self,
        symbol: str,
        *,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol, limit=limit)
        return self._request(
            "grades-historical",
            params=params,
            ttl_category="analyst",
            force_refresh=force_refresh,
        )

    def grades_consensus(
        self,
        symbol: str,
        *,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._request(
            "grades-consensus",
            params={"symbol": symbol},
            ttl_category="analyst",
            force_refresh=force_refresh,
        )
