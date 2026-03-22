from __future__ import annotations


class ChartsMixin:
    """Historical price and intraday chart endpoints."""

    def _chart_request(
        self,
        path: str,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        ttl_category: str = "daily_historical",
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        return self._request(
            path,
            params=params,
            ttl_category=ttl_category,
            force_refresh=force_refresh,
        )

    def historical_price_eod_light(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._chart_request(
            "historical-price-eod/light",
            symbol,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh,
        )

    def historical_price_eod_full(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._chart_request(
            "historical-price-eod/full",
            symbol,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh,
        )

    def historical_price_eod_non_split_adjusted(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._chart_request(
            "historical-price-eod/non-split-adjusted",
            symbol,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh,
        )

    def historical_price_eod_dividend_adjusted(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._chart_request(
            "historical-price-eod/dividend-adjusted",
            symbol,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh,
        )

    def intraday_chart(
        self,
        symbol: str,
        interval: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._chart_request(
            f"historical-chart/{interval}",
            symbol,
            from_date=from_date,
            to_date=to_date,
            ttl_category="intraday_charts",
            force_refresh=force_refresh,
        )
