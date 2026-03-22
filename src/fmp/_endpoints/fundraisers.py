from __future__ import annotations


class FundraisersMixin:
    """Crowdfunding and equity offering endpoints."""

    def crowdfunding_rss(
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
            "crowdfunding-rss",
            params=params or None,
            ttl_category="fundraisers",
            force_refresh=force_refresh,
        )

    def crowdfunding_search(
        self, name: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "crowdfunding-search",
            params={"name": name},
            ttl_category="fundraisers",
            force_refresh=force_refresh,
        )

    def crowdfunding_by_cik(
        self, cik: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "crowdfunding-by-cik",
            params={"cik": cik},
            ttl_category="fundraisers",
            force_refresh=force_refresh,
        )

    def equity_offering_rss(
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
            "equity-offering-rss",
            params=params or None,
            ttl_category="fundraisers",
            force_refresh=force_refresh,
        )

    def equity_offering_search(
        self, name: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "equity-offering-search",
            params={"name": name},
            ttl_category="fundraisers",
            force_refresh=force_refresh,
        )

    def equity_offering_by_cik(
        self, cik: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "equity-offering-by-cik",
            params={"cik": cik},
            ttl_category="fundraisers",
            force_refresh=force_refresh,
        )
