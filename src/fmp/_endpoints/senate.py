from __future__ import annotations


class SenateMixin:
    """Senate trading and disclosure endpoints."""

    def senate_trading(
        self,
        *,
        symbol: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if symbol is not None:
            params["symbol"] = symbol
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "senate-trading",
            params=params or None,
            ttl_category="senate",
            force_refresh=force_refresh,
        )

    def senate_disclosure(
        self,
        *,
        symbol: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if symbol is not None:
            params["symbol"] = symbol
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "senate-disclosure",
            params=params or None,
            ttl_category="senate",
            force_refresh=force_refresh,
        )
