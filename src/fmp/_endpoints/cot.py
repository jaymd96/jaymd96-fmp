from __future__ import annotations


class COTMixin:
    """Commitment of Traders report endpoints."""

    def cot_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "commitment-of-traders-report-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )

    def cot_report(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        return self._request(
            "commitment-of-traders-report",
            params=params,
            ttl_category="cot",
            force_refresh=force_refresh,
        )

    def cot_analysis(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params: dict = {"symbol": symbol}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        return self._request(
            "commitment-of-traders-report-analysis",
            params=params,
            ttl_category="cot",
            force_refresh=force_refresh,
        )
