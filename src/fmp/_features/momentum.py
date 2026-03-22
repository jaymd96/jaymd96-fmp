"""§15 — Momentum derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Single-period returns ─────────────────────────────────────────
    _d(
        "return_1d",
        "(close - LAG(close) OVER w) / NULLIF(LAG(close) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    _d(
        "return_5d",
        "(close - LAG(close, 5) OVER w) / NULLIF(LAG(close, 5) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    _d(
        "return_21d",
        "(close - LAG(close, 21) OVER w) / NULLIF(LAG(close, 21) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    _d(
        "return_63d",
        "(close - LAG(close, 63) OVER w) / NULLIF(LAG(close, 63) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    _d(
        "return_126d",
        "(close - LAG(close, 126) OVER w) / NULLIF(LAG(close, 126) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    _d(
        "return_252d",
        "(close - LAG(close, 252) OVER w) / NULLIF(LAG(close, 252) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    # ── Classic momentum (12-month minus 1-month) ─────────────────────
    _d(
        "momentum_12_1",
        "(LAG(close, 21) OVER w - LAG(close, 252) OVER w)"
        " / NULLIF(LAG(close, 252) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    # ── 52-week percentile (from quote) ───────────────────────────────
    _d(
        "percentile_52w",
        "(price - year_low) / NULLIF(year_high - year_low, 0)",
        ("price", "year_low", "year_high"),
        category="momentum",
    ),
    # ── Short-term reversal ───────────────────────────────────────────
    _d(
        "short_term_reversal",
        "-(close - LAG(close, 5) OVER w) / NULLIF(LAG(close, 5) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    # ── Volume-price confirmation ─────────────────────────────────────
    _d(
        "volume_price_confirmation",
        "((close - LAG(close) OVER w) / NULLIF(LAG(close) OVER w, 0))"
        " * (volume / NULLIF(quote_volume, 0))",
        ("close", "volume", "quote_volume"),
        category="momentum",
        lag=True,
    ),
    # ── Mean reversion (same as short-term reversal) ──────────────────
    _d(
        "mean_reversion_5d",
        "-(close - LAG(close, 5) OVER w) / NULLIF(LAG(close, 5) OVER w, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
    # ── Acceleration (change in momentum) ─────────────────────────────
    _d(
        "acceleration",
        "((close - LAG(close, 21) OVER w)"
        " / NULLIF(LAG(close, 21) OVER w, 0))"
        " - ((LAG(close, 21) OVER w - LAG(close, 42) OVER w)"
        " / NULLIF(LAG(close, 42) OVER w, 0))",
        ("close",),
        category="momentum",
        lag=True,
    ),
    # ── Up/down volume ratio (20-day) ────────────────────────────────
    _d(
        "up_down_volume_ratio_20d",
        "SUM(CASE WHEN close > LAG(close) OVER w THEN volume ELSE 0 END)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)"
        " / NULLIF(SUM(CASE WHEN close <= LAG(close) OVER w"
        " THEN volume ELSE 0 END)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 19 PRECEDING AND CURRENT ROW), 0)",
        ("close", "volume"),
        category="momentum",
        lag=True,
    ),
    # ── Frog-in-the-pan (fraction of positive-return days, 252-day) ─────
    _d(
        "frog_in_pan",
        "SUM(CASE WHEN (close - LAG(close) OVER w) > 0 THEN 1.0 ELSE 0.0 END)"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 251 PRECEDING AND CURRENT ROW)"
        " / NULLIF(252.0, 0)",
        ("close",),
        category="momentum",
        lag=True,
    ),
]
