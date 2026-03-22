from __future__ import annotations


def _build_params(**kwargs: object) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


def _join_symbols(symbols: str | list[str]) -> str:
    if isinstance(symbols, list):
        return ",".join(symbols)
    return symbols


class NewsMixin:
    """News and press release endpoints."""

    def fmp_articles(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(page=page, limit=limit)
        return self._request(
            "fmp-articles",
            params=params or None,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def general_news_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(page=page, limit=limit)
        return self._request(
            "news/general-latest",
            params=params or None,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def press_releases_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(page=page, limit=limit)
        return self._request(
            "news/press-releases-latest",
            params=params or None,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def stock_news_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(page=page, limit=limit)
        return self._request(
            "news/stock-latest",
            params=params or None,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def crypto_news_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(page=page, limit=limit)
        return self._request(
            "news/crypto-latest",
            params=params or None,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def forex_news_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(page=page, limit=limit)
        return self._request(
            "news/forex-latest",
            params=params or None,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def press_releases(
        self,
        symbols: str | list[str],
        *,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbols=_join_symbols(symbols))
        return self._request(
            "news/press-releases",
            params=params,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def stock_news(
        self,
        symbols: str | list[str],
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(
            symbols=_join_symbols(symbols), page=page, limit=limit,
        )
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "news/stock",
            params=params,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def crypto_news(
        self,
        symbols: str | list[str],
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(
            symbols=_join_symbols(symbols), page=page, limit=limit,
        )
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "news/crypto",
            params=params,
            ttl_category="news",
            force_refresh=force_refresh,
        )

    def forex_news(
        self,
        symbols: str | list[str],
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(
            symbols=_join_symbols(symbols), page=page, limit=limit,
        )
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request(
            "news/forex",
            params=params,
            ttl_category="news",
            force_refresh=force_refresh,
        )
