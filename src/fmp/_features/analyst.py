"""§17 — Analyst estimate derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    _d(
        "earnings_surprise_pct",
        "(earnings_eps - eps_estimated) / NULLIF(ABS(eps_estimated), 0)",
        ("earnings_eps", "eps_estimated"),
        category="analyst",
    ),
    _d(
        "revenue_surprise_pct",
        "(earnings_revenue - revenue_estimated)"
        " / NULLIF(ABS(revenue_estimated), 0)",
        ("earnings_revenue", "revenue_estimated"),
        category="analyst",
    ),
    _d(
        "eps_surprise_direction",
        "CASE WHEN earnings_eps > eps_estimated THEN 1 "
        "WHEN earnings_eps < eps_estimated THEN -1 "
        "ELSE 0 END",
        ("earnings_eps", "eps_estimated"),
        category="analyst",
        dtype="INTEGER",
    ),
    _d(
        "revenue_beat",
        "CASE WHEN earnings_revenue > revenue_estimated THEN 1 ELSE 0 END",
        ("earnings_revenue", "revenue_estimated"),
        category="analyst",
        dtype="INTEGER",
    ),
]
