from __future__ import annotations


class ForexMixin:
    """Forex endpoints."""

    def forex_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "forex-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )
