from __future__ import annotations


class DirectoryMixin:
    """Directory / listing endpoints."""

    def stock_list(self, *, force_refresh: bool = False) -> list[dict]:
        return self._request(
            "stock-list", ttl_category="static_lists", force_refresh=force_refresh
        )

    def financial_statement_symbol_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "financial-statement-symbol-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def cik_list(
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
            "cik-list",
            params=params or None,
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def symbol_change(
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
            "symbol-change",
            params=params or None,
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def etf_list(self, *, force_refresh: bool = False) -> list[dict]:
        return self._request(
            "etf-list", ttl_category="static_lists", force_refresh=force_refresh
        )

    def actively_trading_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "actively-trading-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def earnings_transcript_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "earnings-transcript-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def available_exchanges(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "available-exchanges",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def available_sectors(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "available-sectors",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def available_industries(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "available-industries",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def available_countries(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "available-countries",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )
