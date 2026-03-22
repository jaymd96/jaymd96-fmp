"""§18 — Macro / rates derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Pass-through yields ──────────────────────────────────────────
    _d(
        "yield_10y",
        "rate_10y",
        ("rate_10y",),
        category="macro",
    ),
    _d(
        "yield_2y",
        "rate_2y",
        ("rate_2y",),
        category="macro",
    ),
    # ── Yield spreads ────────────────────────────────────────────────
    _d(
        "yield_spread_2s10s",
        "rate_10y - rate_2y",
        ("rate_10y", "rate_2y"),
        category="macro",
    ),
    _d(
        "yield_curve_slope",
        "rate_30y - rate_3m",
        ("rate_30y", "rate_3m"),
        category="macro",
    ),
    _d(
        "yield_spread_10y_3m",
        "rate_10y - rate_3m",
        ("rate_10y", "rate_3m"),
        category="macro",
    ),
    # ── Decimal-scaled rates ─────────────────────────────────────────
    _d(
        "risk_free_rate",
        "rate_10y / 100.0",
        ("rate_10y",),
        category="macro",
    ),
    _d(
        "short_rate",
        "rate_3m / 100.0",
        ("rate_3m",),
        category="macro",
    ),
    _d(
        "long_rate",
        "rate_30y / 100.0",
        ("rate_30y",),
        category="macro",
    ),
    # ── Inversion flag ───────────────────────────────────────────────
    _d(
        "yield_curve_inverted",
        "CASE WHEN rate_2y > rate_10y THEN 1 ELSE 0 END",
        ("rate_2y", "rate_10y"),
        category="macro",
        dtype="INTEGER",
    ),
]
