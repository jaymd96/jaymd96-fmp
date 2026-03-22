from __future__ import annotations


class QuotesMixin:
    """Real-time and batch quote endpoints."""

    def quote(
        self, symbol: str | list[str], *, force_refresh: bool = False
    ) -> list[dict]:
        resolved = ",".join(symbol) if isinstance(symbol, list) else symbol
        return self._request(
            "quote",
            params={"symbol": resolved},
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def quote_short(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "quote-short",
            params={"symbol": symbol},
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def aftermarket_trade(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "aftermarket-trade",
            params={"symbol": symbol},
            ttl_category="aftermarket",
            force_refresh=force_refresh,
        )

    def aftermarket_quote(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "aftermarket-quote",
            params={"symbol": symbol},
            ttl_category="aftermarket",
            force_refresh=force_refresh,
        )

    def stock_price_change(
        self, symbol: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "stock-price-change",
            params={"symbol": symbol},
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_quote(
        self, symbols: list[str], *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "batch-quote",
            params={"symbols": ",".join(symbols)},
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_quote_short(
        self, symbols: list[str], *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "batch-quote-short",
            params={"symbols": ",".join(symbols)},
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_aftermarket_trade(
        self, symbols: list[str], *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "batch-aftermarket-trade",
            params={"symbols": ",".join(symbols)},
            ttl_category="aftermarket",
            force_refresh=force_refresh,
        )

    def batch_aftermarket_quote(
        self, symbols: list[str], *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "batch-aftermarket-quote",
            params={"symbols": ",".join(symbols)},
            ttl_category="aftermarket",
            force_refresh=force_refresh,
        )

    def batch_exchange_quote(
        self, exchange: str, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "batch-exchange-quote",
            params={"exchange": exchange},
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_mutualfund_quotes(
        self, *, exchange: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if exchange is not None:
            params["exchange"] = exchange
        return self._request(
            "batch-mutualfund-quotes",
            params=params or None,
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_etf_quotes(
        self, *, exchange: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if exchange is not None:
            params["exchange"] = exchange
        return self._request(
            "batch-etf-quotes",
            params=params or None,
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_commodity_quotes(
        self, *, exchange: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if exchange is not None:
            params["exchange"] = exchange
        return self._request(
            "batch-commodity-quotes",
            params=params or None,
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_crypto_quotes(
        self, *, exchange: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if exchange is not None:
            params["exchange"] = exchange
        return self._request(
            "batch-crypto-quotes",
            params=params or None,
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_forex_quotes(
        self, *, exchange: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if exchange is not None:
            params["exchange"] = exchange
        return self._request(
            "batch-forex-quotes",
            params=params or None,
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )

    def batch_index_quotes(
        self, *, exchange: str | None = None, force_refresh: bool = False
    ) -> list[dict]:
        params: dict = {}
        if exchange is not None:
            params["exchange"] = exchange
        return self._request(
            "batch-index-quotes",
            params=params or None,
            ttl_category="realtime_quotes",
            force_refresh=force_refresh,
        )
