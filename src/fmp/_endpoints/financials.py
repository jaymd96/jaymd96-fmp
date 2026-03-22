from __future__ import annotations


class FinancialsMixin:
    """Financial statement and metrics endpoints."""

    # -- Core statements ---------------------------------------------------

    def income_statement(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "income-statement",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def balance_sheet(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "balance-sheet-statement",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def cash_flow_statement(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "cash-flow-statement",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def latest_financial_statements(
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
            "latest-financial-statements",
            params=params or None,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    # -- TTM statements ----------------------------------------------------

    def income_statement_ttm(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "income-statement-ttm",
            params={"symbol": symbol},
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def balance_sheet_ttm(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "balance-sheet-statement-ttm",
            params={"symbol": symbol},
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def cash_flow_ttm(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "cash-flow-statement-ttm",
            params={"symbol": symbol},
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    # -- Metrics and ratios ------------------------------------------------

    def key_metrics(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "key-metrics",
            params=params,
            ttl_category="key_metrics",
            force_refresh=force_refresh,
        )

    def ratios(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "ratios",
            params=params,
            ttl_category="key_metrics",
            force_refresh=force_refresh,
        )

    def key_metrics_ttm(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "key-metrics-ttm",
            params={"symbol": symbol},
            ttl_category="key_metrics",
            force_refresh=force_refresh,
        )

    def ratios_ttm(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "ratios-ttm",
            params={"symbol": symbol},
            ttl_category="key_metrics",
            force_refresh=force_refresh,
        )

    def financial_scores(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "financial-scores",
            params={"symbol": symbol},
            ttl_category="key_metrics",
            force_refresh=force_refresh,
        )

    def owner_earnings(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "owner-earnings",
            params={"symbol": symbol},
            ttl_category="key_metrics",
            force_refresh=force_refresh,
        )

    # -- Enterprise values -------------------------------------------------

    def enterprise_values(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "enterprise-values",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    # -- Growth ------------------------------------------------------------

    def income_statement_growth(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "income-statement-growth",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def balance_sheet_growth(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "balance-sheet-statement-growth",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def cash_flow_growth(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "cash-flow-statement-growth",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def financial_growth(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "financial-growth",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    # -- Reports -----------------------------------------------------------

    def financial_reports_dates(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "financial-reports-dates",
            params={"symbol": symbol},
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def financial_reports_json(
        self,
        symbol: str,
        *,
        year: int | None = None,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if year is not None:
            params["year"] = year
        if period is not None:
            params["period"] = period
        return self._request(
            "financial-reports-json",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def financial_reports_xlsx(
        self,
        symbol: str,
        *,
        year: int | None = None,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if year is not None:
            params["year"] = year
        if period is not None:
            params["period"] = period
        return self._request(
            "financial-reports-xlsx",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    # -- Segmentation ------------------------------------------------------

    def revenue_product_segmentation(
        self,
        symbol: str,
        *,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        return self._request(
            "revenue-product-segmentation",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def revenue_geographic_segmentation(
        self,
        symbol: str,
        *,
        period: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        return self._request(
            "revenue-geographic-segmentation",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    # -- As-reported statements --------------------------------------------

    def income_statement_as_reported(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "income-statement-as-reported",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def balance_sheet_as_reported(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "balance-sheet-statement-as-reported",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def cash_flow_as_reported(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "cash-flow-statement-as-reported",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )

    def financial_statement_full_as_reported(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if period is not None:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "financial-statement-full-as-reported",
            params=params,
            ttl_category="financial_statements",
            force_refresh=force_refresh,
        )
