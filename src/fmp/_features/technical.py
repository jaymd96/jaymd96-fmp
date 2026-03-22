"""§14 — Technical derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── 52-week position (from quote) ─────────────────────────────────
    _d(
        "distance_52w_high",
        "(year_high - price) / NULLIF(year_high, 0)",
        ("year_high", "price"),
        category="technical",
    ),
    _d(
        "distance_52w_low",
        "(price - year_low) / NULLIF(year_low, 0)",
        ("price", "year_low"),
        category="technical",
    ),
    # ── Candlestick / intraday ────────────────────────────────────────
    _d(
        "candlestick_range",
        "(high - low) / NULLIF(open, 0)",
        ("high", "low", "open"),
        category="technical",
    ),
    _d(
        "intraday_return",
        "(close - open) / NULLIF(open, 0)",
        ("close", "open"),
        category="technical",
    ),
    # ── Volume dynamics ───────────────────────────────────────────────
    _d(
        "volume_rate_of_change",
        "(volume - LAG(volume) OVER w) / NULLIF(LAG(volume) OVER w, 0)",
        ("volume",),
        category="technical",
        lag=True,
    ),
    _d(
        "force_index",
        "(close - LAG(close) OVER w) * volume",
        ("close", "volume"),
        category="technical",
        lag=True,
    ),
    _d(
        "obv_direction",
        "CASE WHEN close > LAG(close) OVER w THEN volume"
        " WHEN close < LAG(close) OVER w THEN -volume"
        " ELSE 0 END",
        ("close", "volume"),
        category="technical",
        lag=True,
    ),
    # ── Price momentum (multi-period returns) ─────────────────────────
    _d(
        "price_momentum_5d",
        "(close - LAG(close, 5) OVER w) / NULLIF(LAG(close, 5) OVER w, 0)",
        ("close",),
        category="technical",
        lag=True,
    ),
    _d(
        "price_momentum_21d",
        "(close - LAG(close, 21) OVER w) / NULLIF(LAG(close, 21) OVER w, 0)",
        ("close",),
        category="technical",
        lag=True,
    ),
    _d(
        "price_momentum_63d",
        "(close - LAG(close, 63) OVER w) / NULLIF(LAG(close, 63) OVER w, 0)",
        ("close",),
        category="technical",
        lag=True,
    ),
    _d(
        "price_momentum_126d",
        "(close - LAG(close, 126) OVER w) / NULLIF(LAG(close, 126) OVER w, 0)",
        ("close",),
        category="technical",
        lag=True,
    ),
    _d(
        "price_momentum_252d",
        "(close - LAG(close, 252) OVER w) / NULLIF(LAG(close, 252) OVER w, 0)",
        ("close",),
        category="technical",
        lag=True,
    ),
    # ── Rolling extremes ──────────────────────────────────────────────
    _d(
        "rolling_high_20d",
        "MAX(high) OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)",
        ("high",),
        category="technical",
        lag=True,
    ),
    _d(
        "rolling_low_20d",
        "MIN(low) OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)",
        ("low",),
        category="technical",
        lag=True,
    ),
    # ── price_to_sma_50: skipped — requires AVG window which should
    #    come from FMP's technical-indicators endpoint.
    # ── bollinger_position: skipped — requires SMA + STDDEV rolling
    #    calculation better sourced from FMP endpoint.
]
