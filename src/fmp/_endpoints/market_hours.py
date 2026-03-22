from __future__ import annotations


class MarketHoursMixin:
    """Market hours and exchange holiday endpoints."""

    def exchange_market_hours(
        self, exchange: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "exchange-market-hours",
            params={"exchange": exchange},
            ttl_category="market_hours",
            force_refresh=force_refresh,
        )

    def holidays_by_exchange(
        self, exchange: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "holidays-by-exchange",
            params={"exchange": exchange},
            ttl_category="market_hours",
            force_refresh=force_refresh,
        )

    def all_exchange_market_hours(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "all-exchange-market-hours",
            ttl_category="market_hours",
            force_refresh=force_refresh,
        )
