"""§13 — Risk derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Daily return ──────────────────────────────────────────────────
    _d(
        "daily_return",
        "(close - LAG(close) OVER w) / NULLIF(LAG(close) OVER w, 0)",
        ("close",),
        category="risk",
        lag=True,
    ),
    # ── Historical volatility (annualised) ────────────────────────────
    _d(
        "historical_volatility_20d",
        "STDDEV(close / NULLIF(LAG(close) OVER w, 0) - 1)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) * SQRT(252)",
        ("close",),
        category="risk",
        lag=True,
    ),
    _d(
        "historical_volatility_60d",
        "STDDEV(close / NULLIF(LAG(close) OVER w, 0) - 1)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) * SQRT(252)",
        ("close",),
        category="risk",
        lag=True,
    ),
    _d(
        "historical_volatility_252d",
        "STDDEV(close / NULLIF(LAG(close) OVER w, 0) - 1)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) * SQRT(252)",
        ("close",),
        category="risk",
        lag=True,
    ),
    # ── Drawdown ──────────────────────────────────────────────────────
    _d(
        "max_drawdown_252d",
        "(close - MAX(close) OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW))"
        " / NULLIF(MAX(close) OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW), 0)",
        ("close",),
        category="risk",
        lag=True,
    ),
    # ── VaR: skipped — PERCENTILE_CONT OVER window not supported in
    #    DuckDB with ROWS frame.
    # ── 52-week range (from quote) ────────────────────────────────────
    _d(
        "distance_from_52w_high",
        "(year_high - price) / NULLIF(year_high, 0)",
        ("year_high", "price"),
        category="risk",
    ),
    _d(
        "distance_from_52w_low",
        "(price - year_low) / NULLIF(year_low, 0)",
        ("price", "year_low"),
        category="risk",
    ),
    # ── Volume ────────────────────────────────────────────────────────
    _d(
        "volume_to_avg",
        "quote_volume / NULLIF(avg_volume, 0)",
        ("quote_volume", "avg_volume"),
        category="risk",
    ),
    # ── Intraday range ────────────────────────────────────────────────
    _d(
        "price_range_pct",
        "(high - low) / NULLIF(open, 0)",
        ("high", "low", "open"),
        category="risk",
    ),
    # ── Overnight gap ─────────────────────────────────────────────────
    _d(
        "overnight_gap",
        "(open - LAG(close) OVER w) / NULLIF(LAG(close) OVER w, 0)",
        ("open", "close"),
        category="risk",
        lag=True,
    ),
    # ── Directional flag ──────────────────────────────────────────────
    _d(
        "up_day",
        "CASE WHEN close > LAG(close) OVER w THEN 1 ELSE 0 END",
        ("close",),
        category="risk",
        dtype="INTEGER",
        lag=True,
    ),
    # ── True range ────────────────────────────────────────────────────
    _d(
        "true_range",
        "GREATEST(high - low,"
        " ABS(high - LAG(close) OVER w),"
        " ABS(low - LAG(close) OVER w))",
        ("high", "low", "close"),
        category="risk",
        lag=True,
    ),
    # ── earnings_volatility: skipped — requires 8-quarter rolling
    #    aggregation that cannot be expressed in a single SQL expression.
]
