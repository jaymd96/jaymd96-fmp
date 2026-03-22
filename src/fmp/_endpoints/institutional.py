from __future__ import annotations


def _build_params(**kwargs: object) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


class InstitutionalMixin:
    """Institutional ownership endpoints."""

    def institutional_ownership_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(page=page, limit=limit)
        return self._request(
            "institutional-ownership/latest",
            params=params or None,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def institutional_ownership_extract(
        self,
        cik: str,
        *,
        year: int | None = None,
        quarter: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(cik=cik, year=year, quarter=quarter)
        return self._request(
            "institutional-ownership/extract",
            params=params,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def institutional_ownership_dates(
        self,
        cik: str,
        *,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._request(
            "institutional-ownership/dates",
            params={"cik": cik},
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def institutional_ownership_by_holder(
        self,
        symbol: str,
        *,
        year: int | None = None,
        quarter: int | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(
            symbol=symbol, year=year, quarter=quarter, page=page, limit=limit,
        )
        return self._request(
            "institutional-ownership/extract-analytics/holder",
            params=params,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def institutional_holder_performance(
        self,
        cik: str,
        *,
        page: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(cik=cik, page=page)
        return self._request(
            "institutional-ownership/holder-performance-summary",
            params=params,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def institutional_holder_industry_breakdown(
        self,
        cik: str,
        *,
        year: int | None = None,
        quarter: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(cik=cik, year=year, quarter=quarter)
        return self._request(
            "institutional-ownership/holder-industry-breakdown",
            params=params,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def institutional_positions_summary(
        self,
        symbol: str,
        *,
        year: int | None = None,
        quarter: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol, year=year, quarter=quarter)
        return self._request(
            "institutional-ownership/symbol-positions-summary",
            params=params,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def institutional_industry_summary(
        self,
        *,
        year: int | None = None,
        quarter: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(year=year, quarter=quarter)
        return self._request(
            "institutional-ownership/industry-summary",
            params=params or None,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )
