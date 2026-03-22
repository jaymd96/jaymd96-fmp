from __future__ import annotations


class SECFilingsMixin:
    """SEC filings and SIC classification endpoints."""

    def sec_filings_8k(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "sec-filings-8k",
            params=params or None,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sec_filings_financials(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "sec-filings-financials",
            params=params or None,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sec_filings_by_form_type(
        self,
        form_type: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"formType": form_type}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "sec-filings-search/form-type",
            params=params,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sec_filings_by_symbol(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "sec-filings-search/symbol",
            params=params,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sec_filings_by_cik(
        self,
        cik: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"cik": cik}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self._request(
            "sec-filings-search/cik",
            params=params,
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sec_company_by_name(
        self, company: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "sec-filings-company-search/name",
            params={"company": company},
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sec_company_by_symbol(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "sec-filings-company-search/symbol",
            params={"symbol": symbol},
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sec_company_by_cik(
        self, cik: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "sec-filings-company-search/cik",
            params={"cik": cik},
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sec_profile(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "sec-profile",
            params={"symbol": symbol},
            ttl_category="sec_filings",
            force_refresh=force_refresh,
        )

    def sic_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "standard-industrial-classification-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def sic_search(
        self,
        *,
        symbol: str | None = None,
        sic_code: str | None = None,
        industry_title: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {}
        if symbol is not None:
            params["symbol"] = symbol
        if sic_code is not None:
            params["sicCode"] = sic_code
        if industry_title is not None:
            params["industryTitle"] = industry_title
        return self._request(
            "industry-classification-search",
            params=params or None,
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def sic_all(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "all-industry-classification",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )
