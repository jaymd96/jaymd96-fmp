from __future__ import annotations


def _build_params(**kwargs: object) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


class EarningsMixin:
    """Earnings, dividends, splits, and IPO endpoints."""

    def dividends(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol, limit=limit)
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "dividends",
            params=params,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )

    def dividends_calendar(
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
            "dividends-calendar",
            params=params or None,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )

    def earnings(
        self,
        symbol: str,
        *,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol, limit=limit)
        return self._request(
            "earnings",
            params=params,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )

    def earnings_calendar(
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
            "earnings-calendar",
            params=params or None,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )

    def ipos_calendar(
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
            "ipos-calendar",
            params=params or None,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )

    def ipos_disclosure(
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
            "ipos-disclosure",
            params=params or None,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )

    def ipos_prospectus(
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
            "ipos-prospectus",
            params=params or None,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )

    def splits(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol)
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "splits",
            params=params,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )

    def splits_calendar(
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
            "splits-calendar",
            params=params or None,
            ttl_category="earnings_calendar",
            force_refresh=force_refresh,
        )
