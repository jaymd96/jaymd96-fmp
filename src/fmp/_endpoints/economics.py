from __future__ import annotations


def _build_params(**kwargs: object) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


class EconomicsMixin:
    """Economic data endpoints."""

    def treasury_rates(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params()
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "treasury-rates",
            params=params or None,
            ttl_category="economic_indicators",
            force_refresh=force_refresh,
        )

    def economic_indicators(
        self,
        name: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(name=name)
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "economic-indicators",
            params=params,
            ttl_category="economic_indicators",
            force_refresh=force_refresh,
        )

    def economic_calendar(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params()
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "economic-calendar",
            params=params or None,
            ttl_category="economic_indicators",
            force_refresh=force_refresh,
        )

    def market_risk_premium(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "market-risk-premium",
            ttl_category="economic_indicators",
            force_refresh=force_refresh,
        )
