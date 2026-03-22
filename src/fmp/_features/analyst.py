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
    # ── Price-target features ────────────────────────────────────────
    _d(
        "target_upside",
        "(target_consensus - price) / NULLIF(price, 0)",
        ("target_consensus", "price"),
        category="analyst",
    ),
    _d(
        "target_dispersion",
        "(target_high - target_low) / NULLIF(target_median, 0)",
        ("target_high", "target_low", "target_median"),
        category="analyst",
    ),
    # ── Consensus scoring ────────────────────────────────────────────
    _d(
        "consensus_score",
        "(strong_buy * 5 + buy * 4 + hold * 3 + sell * 2 + strong_sell * 1)"
        " / NULLIF(strong_buy + buy + hold + sell + strong_sell, 0)",
        ("strong_buy", "buy", "hold", "sell", "strong_sell"),
        category="analyst",
    ),
    _d(
        "analyst_coverage",
        "num_analysts_eps",
        ("num_analysts_eps",),
        category="analyst",
        dtype="INTEGER",
    ),
    # ── Forward estimates ────────────────────────────────────────────
    _d(
        "est_eps_growth",
        "(est_eps_avg - eps_diluted) / NULLIF(ABS(eps_diluted), 0)",
        ("est_eps_avg", "eps_diluted"),
        category="analyst",
    ),
    _d(
        "est_revenue_growth",
        "(est_revenue_avg - revenue) / NULLIF(ABS(revenue), 0)",
        ("est_revenue_avg", "revenue"),
        category="analyst",
    ),
    _d(
        "forward_pe",
        "price / NULLIF(est_eps_avg, 0)",
        ("price", "est_eps_avg"),
        category="analyst",
    ),
    # ── FMP rating pass-through ──────────────────────────────────────
    _d(
        "fmp_rating_val",
        "fmp_rating_score",
        ("fmp_rating_score",),
        category="analyst",
        dtype="INTEGER",
    ),
]
