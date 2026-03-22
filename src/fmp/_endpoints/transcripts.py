from __future__ import annotations


def _build_params(**kwargs: object) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


class TranscriptsMixin:
    """Earning call transcript endpoints."""

    def earning_call_transcript_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(page=page, limit=limit)
        return self._request(
            "earning-call-transcript-latest",
            params=params or None,
            ttl_category="transcripts",
            force_refresh=force_refresh,
        )

    def earning_call_transcript(
        self,
        symbol: str,
        *,
        year: int | None = None,
        quarter: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        params = _build_params(symbol=symbol, year=year, quarter=quarter)
        return self._request(
            "earning-call-transcript",
            params=params,
            ttl_category="transcripts",
            force_refresh=force_refresh,
        )

    def earning_call_transcript_dates(
        self,
        symbol: str,
        *,
        force_refresh: bool = False,
    ) -> list[dict]:
        return self._request(
            "earning-call-transcript-dates",
            params={"symbol": symbol},
            ttl_category="transcripts",
            force_refresh=force_refresh,
        )
