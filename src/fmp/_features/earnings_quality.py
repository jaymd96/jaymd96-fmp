"""§10 — Earnings quality derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Accrual quality ───────────────────────────────────────────────
    _d(
        "sloan_accrual_cf",
        "(net_income - operating_cash_flow) / NULLIF(total_assets, 0)",
        ("net_income", "operating_cash_flow", "total_assets"),
        category="earnings_quality",
    ),
    _d(
        "cash_to_accruals",
        "operating_cash_flow / NULLIF(net_income, 0)",
        ("operating_cash_flow", "net_income"),
        category="earnings_quality",
    ),
    # ── Receivables / inventory signals ───────────────────────────────
    _d(
        "receivables_pct_revenue",
        "net_receivables / NULLIF(revenue, 0)",
        ("net_receivables", "revenue"),
        category="earnings_quality",
    ),
    _d(
        "delta_receivables_revenue",
        "(net_receivables - LAG(net_receivables) OVER w)"
        " / NULLIF(revenue - LAG(revenue) OVER w, 0)",
        ("net_receivables", "revenue"),
        category="earnings_quality",
        lag=True,
    ),
    _d(
        "inventory_pct_revenue",
        "inventory / NULLIF(revenue, 0)",
        ("inventory", "revenue"),
        category="earnings_quality",
    ),
    _d(
        "delta_inventory_revenue",
        "(inventory - LAG(inventory) OVER w)"
        " / NULLIF(revenue - LAG(revenue) OVER w, 0)",
        ("inventory", "revenue"),
        category="earnings_quality",
        lag=True,
    ),
    # ── Deferred revenue & goodwill ───────────────────────────────────
    _d(
        "deferred_revenue_growth",
        "(deferred_revenue - LAG(deferred_revenue) OVER w)"
        " / NULLIF(ABS(LAG(deferred_revenue) OVER w), 0)",
        ("deferred_revenue",),
        category="earnings_quality",
        lag=True,
    ),
    _d(
        "goodwill_to_assets",
        "goodwill_and_intangibles / NULLIF(total_assets, 0)",
        ("goodwill_and_intangibles", "total_assets"),
        category="earnings_quality",
    ),
    _d(
        "goodwill_impairment_flag",
        "CASE WHEN goodwill < LAG(goodwill) OVER w THEN 1 ELSE 0 END",
        ("goodwill",),
        category="earnings_quality",
        dtype="INTEGER",
        lag=True,
    ),
    # ── Asset quality ─────────────────────────────────────────────────
    _d(
        "asset_quality",
        "(total_assets - total_current_assets - property_plant_equipment)"
        " / NULLIF(total_assets, 0)",
        ("total_assets", "total_current_assets", "property_plant_equipment"),
        category="earnings_quality",
    ),
    # ── Earnings / revenue surprise ───────────────────────────────────
    _d(
        "earnings_surprise",
        "(earnings_eps - eps_estimated) / NULLIF(ABS(eps_estimated), 0)",
        ("earnings_eps", "eps_estimated"),
        category="earnings_quality",
    ),
    _d(
        "revenue_surprise",
        "(earnings_revenue - revenue_estimated)"
        " / NULLIF(ABS(revenue_estimated), 0)",
        ("earnings_revenue", "revenue_estimated"),
        category="earnings_quality",
    ),
    # ── Cash-flow quality flags ───────────────────────────────────────
    _d(
        "ocf_exceeds_ni",
        "CASE WHEN operating_cash_flow > net_income THEN 1 ELSE 0 END",
        ("operating_cash_flow", "net_income"),
        category="earnings_quality",
        dtype="INTEGER",
    ),
    _d(
        "total_accruals_to_assets",
        "(net_income - operating_cash_flow) / NULLIF(total_assets, 0)",
        ("net_income", "operating_cash_flow", "total_assets"),
        category="earnings_quality",
    ),
    # ── Beneish M-score components ────────────────────────────────────
    _d(
        "dsri",
        "(net_receivables / NULLIF(revenue, 0))"
        " / NULLIF(LAG(net_receivables) OVER w"
        " / NULLIF(LAG(revenue) OVER w, 0), 0)",
        ("net_receivables", "revenue"),
        category="earnings_quality",
        lag=True,
    ),
    _d(
        "gmi",
        "(LAG(gross_profit) OVER w / NULLIF(LAG(revenue) OVER w, 0))"
        " / NULLIF(gross_profit / NULLIF(revenue, 0), 0)",
        ("gross_profit", "revenue"),
        category="earnings_quality",
        lag=True,
    ),
]
