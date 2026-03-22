"""§20 — Event-driven derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    _d(
        "ipo_age_days",
        "CURRENT_DATE - ipo_date",
        ("ipo_date",),
        category="event_driven",
        dtype="INTEGER",
    ),
    _d(
        "near_52w_high",
        "CASE WHEN (year_high - price) / NULLIF(year_high, 0) < 0.05 "
        "THEN 1 ELSE 0 END",
        ("year_high", "price"),
        category="event_driven",
        dtype="INTEGER",
    ),
    _d(
        "near_52w_low",
        "CASE WHEN (price - year_low) / NULLIF(year_low, 0) < 0.05 "
        "THEN 1 ELSE 0 END",
        ("price", "year_low"),
        category="event_driven",
        dtype="INTEGER",
    ),
    # ── Float & headcount ────────────────────────────────────────────
    _d(
        "float_pct",
        "float_shares / NULLIF(outstanding_shares, 0)",
        ("float_shares", "outstanding_shares"),
        category="event_driven",
    ),
    _d(
        "employee_growth",
        "(employee_count_val - LAG(employee_count_val) OVER w)"
        " / NULLIF(ABS(LAG(employee_count_val) OVER w), 0)",
        ("employee_count_val",),
        category="event_driven",
        lag=True,
    ),
    # ── Pre-computed multi-period returns from FMP ─────────────────
    _d("fmp_ret_1d", "fmp_return_1d", ("fmp_return_1d",), category="event_driven"),
    _d("fmp_ret_5d", "fmp_return_5d", ("fmp_return_5d",), category="event_driven"),
    _d("fmp_ret_1m", "fmp_return_1m", ("fmp_return_1m",), category="event_driven"),
    _d("fmp_ret_3m", "fmp_return_3m", ("fmp_return_3m",), category="event_driven"),
    _d("fmp_ret_6m", "fmp_return_6m", ("fmp_return_6m",), category="event_driven"),
    _d("fmp_ret_ytd", "fmp_return_ytd", ("fmp_return_ytd",), category="event_driven"),
    _d("fmp_ret_1y", "fmp_return_1y", ("fmp_return_1y",), category="event_driven"),
    _d("fmp_ret_3y", "fmp_return_3y", ("fmp_return_3y",), category="event_driven"),
    _d("fmp_ret_5y", "fmp_return_5y", ("fmp_return_5y",), category="event_driven"),
    # ── Split features ─────────────────────────────────────────────
    _d("split_ratio", "split_numerator / NULLIF(split_denominator, 0)", ("split_numerator", "split_denominator"), category="event_driven"),
]
