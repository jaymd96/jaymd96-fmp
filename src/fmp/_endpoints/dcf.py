from __future__ import annotations


class DCFMixin:
    """Discounted cash flow endpoints."""

    def discounted_cash_flow(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "discounted-cash-flow",
            params={"symbol": symbol},
            ttl_category="dcf",
            force_refresh=force_refresh,
        )

    def levered_dcf(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "levered-discounted-cash-flow",
            params={"symbol": symbol},
            ttl_category="dcf",
            force_refresh=force_refresh,
        )

    def custom_dcf(
        self, symbol: str, *, force_refresh: bool = False, **kwargs
    ) -> list[dict]:
        params: dict = {"symbol": symbol, **kwargs}
        return self._request(
            "custom-discounted-cash-flow",
            params=params,
            ttl_category="dcf",
            force_refresh=force_refresh,
        )

    def custom_levered_dcf(
        self, symbol: str, *, force_refresh: bool = False, **kwargs
    ) -> list[dict]:
        params: dict = {"symbol": symbol, **kwargs}
        return self._request(
            "custom-levered-discounted-cash-flow",
            params=params,
            ttl_category="dcf",
            force_refresh=force_refresh,
        )
