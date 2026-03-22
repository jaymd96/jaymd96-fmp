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
]
