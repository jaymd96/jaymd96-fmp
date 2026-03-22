"""§6 — Valuation derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Price multiples ────────────────────────────────────────────
    _d(
        "pe_derived",
        "market_cap / NULLIF(net_income, 0)",
        ("market_cap", "net_income"),
        category="valuation",
    ),
    _d(
        "peg_ratio",
        "(price / NULLIF(eps_diluted, 0))"
        " / NULLIF(((est_eps_avg - eps_diluted)"
        " / NULLIF(ABS(eps_diluted), 0)) * 100, 0)",
        ("price", "eps_diluted", "est_eps_avg"),
        category="valuation",
    ),
    _d(
        "price_to_sales_derived",
        "market_cap / NULLIF(revenue, 0)",
        ("market_cap", "revenue"),
        category="valuation",
    ),
    _d(
        "price_to_book",
        "market_cap / NULLIF(total_stockholders_equity, 0)",
        ("market_cap", "total_stockholders_equity"),
        category="valuation",
    ),
    _d(
        "price_to_tangible_book",
        "market_cap"
        " / NULLIF(total_stockholders_equity - goodwill_and_intangibles, 0)",
        (
            "market_cap",
            "total_stockholders_equity",
            "goodwill_and_intangibles",
        ),
        category="valuation",
    ),
    _d(
        "price_to_cf",
        "market_cap / NULLIF(operating_cash_flow, 0)",
        ("market_cap", "operating_cash_flow"),
        category="valuation",
    ),
    _d(
        "price_to_fcf",
        "market_cap / NULLIF(free_cash_flow, 0)",
        ("market_cap", "free_cash_flow"),
        category="valuation",
    ),
    # ── EV multiples ───────────────────────────────────────────────
    _d(
        "ev_to_revenue",
        "enterprise_value / NULLIF(revenue, 0)",
        ("enterprise_value", "revenue"),
        category="valuation",
    ),
    _d(
        "ev_to_ebitda_derived",
        "enterprise_value / NULLIF(ebitda, 0)",
        ("enterprise_value", "ebitda"),
        category="valuation",
    ),
    _d(
        "ev_to_ebit",
        "enterprise_value"
        " / NULLIF(ebitda - depreciation_and_amortization, 0)",
        ("enterprise_value", "ebitda", "depreciation_and_amortization"),
        category="valuation",
    ),
    _d(
        "ev_to_fcf_derived",
        "enterprise_value / NULLIF(free_cash_flow, 0)",
        ("enterprise_value", "free_cash_flow"),
        category="valuation",
    ),
    _d(
        "ev_to_ic",
        "enterprise_value"
        " / NULLIF(total_debt + total_stockholders_equity - cash_and_equivalents, 0)",
        (
            "enterprise_value",
            "total_debt",
            "total_stockholders_equity",
            "cash_and_equivalents",
        ),
        category="valuation",
    ),
    _d(
        "ev_to_gross_profit",
        "enterprise_value / NULLIF(gross_profit, 0)",
        ("enterprise_value", "gross_profit"),
        category="valuation",
    ),
    # ── Yield metrics ──────────────────────────────────────────────
    _d(
        "earnings_yield_derived",
        "net_income / NULLIF(market_cap, 0)",
        ("net_income", "market_cap"),
        category="valuation",
    ),
    _d(
        "fcf_yield_derived",
        "free_cash_flow / NULLIF(market_cap, 0)",
        ("free_cash_flow", "market_cap"),
        category="valuation",
    ),
    _d(
        "shareholder_yield",
        "(-share_repurchase - dividends_paid)"
        " / NULLIF(market_cap, 0)",
        ("share_repurchase", "dividends_paid", "market_cap"),
        category="valuation",
    ),
    # ── Composite / other ──────────────────────────────────────────
    _d(
        "tobins_q",
        "(market_cap + total_liabilities)"
        " / NULLIF(total_assets, 0)",
        ("market_cap", "total_liabilities", "total_assets"),
        category="valuation",
    ),
    _d(
        "ev_per_share",
        "enterprise_value / NULLIF(weighted_avg_shares_diluted, 0)",
        ("enterprise_value", "weighted_avg_shares_diluted"),
        category="valuation",
    ),
    _d(
        "price_to_working_capital",
        "market_cap"
        " / NULLIF(total_current_assets - total_current_liabilities, 0)",
        (
            "market_cap",
            "total_current_assets",
            "total_current_liabilities",
        ),
        category="valuation",
    ),
    # ── DCF-based ─────────────────────────────────────────────────
    _d("dcf_value", "dcf_val", ("dcf_val",), category="valuation"),
    _d("dcf_upside", "(dcf_val - price) / NULLIF(price, 0)", ("dcf_val", "price"), category="valuation"),
    _d("dcf_margin_of_safety", "(dcf_val - price) / NULLIF(dcf_val, 0)", ("dcf_val", "price"), category="valuation"),
]
