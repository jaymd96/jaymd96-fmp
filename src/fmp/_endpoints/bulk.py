from __future__ import annotations


class BulkMixin:
    """Bulk data endpoints."""

    def profile_bulk(
        self, *, part: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if part is not None:
            params["part"] = part
        return self._request(
            "profile-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def quote_bulk(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "batch-request-end-of-day-prices",
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def income_statement_bulk(
        self,
        *,
        year: int | None = None,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        if period is not None:
            params["period"] = period
        return self._request(
            "income-statement-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def balance_sheet_bulk(
        self,
        *,
        year: int | None = None,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        if period is not None:
            params["period"] = period
        return self._request(
            "balance-sheet-statement-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def cash_flow_bulk(
        self,
        *,
        year: int | None = None,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        if period is not None:
            params["period"] = period
        return self._request(
            "cash-flow-statement-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def ratios_bulk(
        self,
        *,
        year: int | None = None,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        if period is not None:
            params["period"] = period
        return self._request(
            "ratios-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def key_metrics_bulk(
        self,
        *,
        year: int | None = None,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        if period is not None:
            params["period"] = period
        return self._request(
            "key-metrics-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def earnings_surprise_bulk(
        self, *, year: int | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        return self._request(
            "earnings-surprises-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def financial_scores_bulk(
        self, *, year: int | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if year is not None:
            params["year"] = year
        return self._request(
            "financial-scores-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )

    def etf_holdings_bulk(
        self, *, date: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if date is not None:
            params["date"] = date
        return self._request(
            "etf-holdings-bulk",
            params=params or None,
            ttl_category="bulk_data",
            force_refresh=force_refresh,
        )
