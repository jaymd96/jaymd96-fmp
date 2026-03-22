from __future__ import annotations


def _build_params(**kwargs: object) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


class TechnicalMixin:
    """Technical indicator endpoints."""

    def _technical_indicator(
        self,
        indicator: str,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(
            symbol=symbol, periodLength=period_length, timeframe=timeframe,
        )
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            f"technical-indicators/{indicator}",
            params=params,
            ttl_category="technical_indicators",
            force_refresh=force_refresh,
        )

    def sma(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "sma", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )

    def ema(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "ema", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )

    def wma(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "wma", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )

    def dema(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "dema", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )

    def tema(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "tema", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )

    def rsi(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "rsi", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )

    def standard_deviation(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "standarddeviation", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )

    def williams(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "williams", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )

    def adx(
        self,
        symbol: str,
        period_length: int,
        timeframe: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._technical_indicator(
            "adx", symbol, period_length, timeframe,
            from_date=from_date, to_date=to_date, force_refresh=force_refresh,
        )
