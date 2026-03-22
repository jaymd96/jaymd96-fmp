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
        "quote_volume / NULLIF(quote_volume, 0)",
        ("quote_volume", "quote_volume"),
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
    # ── Average True Range (14-day) ──────────────────────────────────
    _d(
        "atr_14",
        "AVG(GREATEST(high - low,"
        " ABS(high - LAG(close) OVER w),"
        " ABS(low - LAG(close) OVER w)))"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)",
        ("high", "low", "close"),
        category="risk",
        lag=True,
    ),
    # ── Downside volatility (annualised) ─────────────────────────────
    _d(
        "down_volatility_20d",
        "STDDEV(CASE WHEN close < LAG(close) OVER w"
        " THEN (close - LAG(close) OVER w)"
        " / NULLIF(LAG(close) OVER w, 0)"
        " ELSE NULL END)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) * SQRT(252)",
        ("close",),
        category="risk",
        lag=True,
    ),
    # ── Calmar ratio (1-year return / max drawdown) ─────────────────────
    _d(
        "calmar_ratio",
        "((close / NULLIF(LAG(close, 252) OVER w, 0)) - 1)"
        " / NULLIF(ABS((close - MAX(close) OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW))"
        " / NULLIF(MAX(close) OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW), 0)), 0)",
        ("close",),
        category="risk",
        lag=True,
    ),
    # ── Value at Risk (5th percentile, 252-day) ─────────────────────────
    _d(
        "var_95_252d",
        "QUANTILE_CONT((close / NULLIF(LAG(close) OVER w, 0) - 1), 0.05)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW)",
        ("close",),
        category="risk",
        lag=True,
    ),
    # ── Return distribution: skewness (252-day) ─────────────────────────
    _d(
        "skewness_252d",
        "SKEWNESS(close / NULLIF(LAG(close) OVER w, 0) - 1)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW)",
        ("close",),
        category="risk",
        lag=True,
    ),
    # ── Return distribution: kurtosis (252-day) ─────────────────────────
    _d(
        "kurtosis_252d",
        "KURTOSIS(close / NULLIF(LAG(close) OVER w, 0) - 1)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW)",
        ("close",),
        category="risk",
        lag=True,
    ),
    # ── Risk-adjusted return ratios ────────────────────────────────────
    _d(
        "sharpe_ratio_252d",
        "((close / NULLIF(LAG(close, 252) OVER w, 0) - 1) - rate_10y / 100.0)"
        " / NULLIF(STDDEV(close / NULLIF(LAG(close) OVER w, 0) - 1)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) * SQRT(252), 0)",
        ("close", "rate_10y"),
        category="risk",
        lag=True,
    ),
    _d(
        "sortino_ratio_252d",
        "((close / NULLIF(LAG(close, 252) OVER w, 0) - 1) - rate_10y / 100.0)"
        " / NULLIF(STDDEV(CASE WHEN close < LAG(close) OVER w"
        " THEN close / NULLIF(LAG(close) OVER w, 0) - 1"
        " ELSE NULL END)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) * SQRT(252), 0)",
        ("close", "rate_10y"),
        category="risk",
        lag=True,
    ),
]
