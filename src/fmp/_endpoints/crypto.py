from __future__ import annotations


class CryptoMixin:
    """Cryptocurrency endpoints."""

    def crypto_list(
        self, *, force_refresh: bool = False
    ) -> list[dict]:
        return self._request(
            "crypto-list",
            ttl_category="static_lists",
            force_refresh=force_refresh,
        )
