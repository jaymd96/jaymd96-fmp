from __future__ import annotations


class ESGMixin:
    """ESG (Environmental, Social, Governance) endpoints."""

    def esg_score(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "esg-environmental-social-governance-data",
            params={"symbol": symbol},
            ttl_category="esg",
            force_refresh=force_refresh,
        )

    def esg_ratings(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "esg-environmental-social-governance-data-ratings",
            params={"symbol": symbol},
            ttl_category="esg",
            force_refresh=force_refresh,
        )

    def esg_benchmark(
        self, *, year: int | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        return self._request(
            "esg-environmental-social-governance-sector-benchmark",
            params=params or None,
            ttl_category="esg",
            force_refresh=force_refresh,
        )
