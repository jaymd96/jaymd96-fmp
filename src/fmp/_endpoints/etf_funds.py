from __future__ import annotations


class ETFFundsMixin:
    """ETF and fund endpoints."""

    def etf_holdings(
        self, symbol: str, *, date: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if date is not None:
            params["date"] = date
        return self._request(
            "etf/holdings",
            params=params,
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )

    def etf_info(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "etf/info",
            params={"symbol": symbol},
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )

    def etf_country_weightings(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "etf/country-weightings",
            params={"symbol": symbol},
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )

    def etf_asset_exposure(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "etf/asset-exposure",
            params={"symbol": symbol},
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )

    def etf_sector_weightings(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "etf/sector-weightings",
            params={"symbol": symbol},
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )

    def fund_disclosure_latest(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "funds/disclosure-holders-latest",
            params={"symbol": symbol},
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )

    def fund_disclosure(
        self,
        symbol: str,
        *,
        year: int | None = None,
        quarter: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if year is not None:
            params["year"] = year
        if quarter is not None:
            params["quarter"] = quarter
        return self._request(
            "funds/disclosure",
            params=params,
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )

    def fund_disclosure_search(
        self, name: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "funds/disclosure-holders-search",
            params={"name": name},
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )

    def fund_disclosure_dates(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "funds/disclosure-dates",
            params={"symbol": symbol},
            ttl_category="etf_fund_holdings",
            force_refresh=force_refresh,
        )
