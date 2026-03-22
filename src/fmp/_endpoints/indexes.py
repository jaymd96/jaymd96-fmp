from __future__ import annotations


class IndexesMixin:
    """Market index and constituent endpoints."""

    def index_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "index-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def sp500_constituent(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "sp500-constituent",
            ttl_category="index_constituents",
            force_refresh=force_refresh,
        )

    def nasdaq_constituent(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "nasdaq-constituent",
            ttl_category="index_constituents",
            force_refresh=force_refresh,
        )

    def dowjones_constituent(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "dowjones-constituent",
            ttl_category="index_constituents",
            force_refresh=force_refresh,
        )

    def historical_sp500_constituent(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "historical-sp500-constituent",
            ttl_category="index_constituents",
            force_refresh=force_refresh,
        )

    def historical_nasdaq_constituent(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "historical-nasdaq-constituent",
            ttl_category="index_constituents",
            force_refresh=force_refresh,
        )

    def historical_dowjones_constituent(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "historical-dowjones-constituent",
            ttl_category="index_constituents",
            force_refresh=force_refresh,
        )
