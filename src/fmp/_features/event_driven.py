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
]
