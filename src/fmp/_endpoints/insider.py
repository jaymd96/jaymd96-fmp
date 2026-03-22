from __future__ import annotations


class InsiderMixin:
    """Insider trading endpoints."""

    def insider_trading_latest(
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
            "insider-trading/latest",
            params=params or None,
            ttl_category="insider_trades",
            force_refresh=force_refresh,
        )

    def insider_trading_search(
        self,
        symbol: str,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "insider-trading/search",
            params=params,
            ttl_category="insider_trades",
            force_refresh=force_refresh,
        )

    def insider_trading_by_name(
        self, name: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "insider-trading/reporting-name",
            params={"name": name},
            ttl_category="insider_trades",
            force_refresh=force_refresh,
        )

    def insider_trading_transaction_types(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "insider-trading-transaction-type",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def insider_trading_statistics(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "insider-trading/statistics",
            params={"symbol": symbol},
            ttl_category="insider_trades",
            force_refresh=force_refresh,
        )

    def acquisition_of_beneficial_ownership(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "acquisition-of-beneficial-ownership",
            params={"symbol": symbol},
            ttl_category="insider_trades",
            force_refresh=force_refresh,
        )
