from __future__ import annotations


class CommoditiesMixin:
    """Commodities endpoints."""

    def commodities_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "commodities-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )
