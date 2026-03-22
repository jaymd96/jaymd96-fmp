"""§7 — Cash-flow derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    _d(
        "fcf_derived",
        "operating_cash_flow + capex",
        ("operating_cash_flow", "capex"),
        category="cash_flow",
    ),
    _d(
        "fcf_margin",
        "free_cash_flow / NULLIF(revenue, 0)",
        ("free_cash_flow", "revenue"),
        category="cash_flow",
    ),
    _d(
        "cash_earnings_quality",
        "operating_cash_flow / NULLIF(net_income, 0)",
        ("operating_cash_flow", "net_income"),
        category="cash_flow",
    ),
    _d(
        "cash_debt_coverage",
        "operating_cash_flow / NULLIF(total_debt, 0)",
        ("operating_cash_flow", "total_debt"),
        category="cash_flow",
    ),
    _d(
        "ocf_to_capex",
        "operating_cash_flow / NULLIF(ABS(capex), 0)",
        ("operating_cash_flow", "capex"),
        category="cash_flow",
    ),
    _d(
        "capex_to_ocf",
        "ABS(capex) / NULLIF(operating_cash_flow, 0)",
        ("capex", "operating_cash_flow"),
        category="cash_flow",
    ),
    _d(
        "reinvestment_rate",
        "(ABS(capex) - depreciation_and_amortization)"
        " / NULLIF(operating_income * (1 - income_tax_expense"
        " / NULLIF(income_before_tax, 0)), 0)",
        (
            "capex",
            "depreciation_and_amortization",
            "operating_income",
            "income_tax_expense",
            "income_before_tax",
        ),
        category="cash_flow",
    ),
    _d(
        "cash_conversion_ratio",
        "free_cash_flow / NULLIF(net_income, 0)",
        ("free_cash_flow", "net_income"),
        category="cash_flow",
    ),
    _d(
        "ocf_growth",
        "(operating_cash_flow - LAG(operating_cash_flow) OVER w)"
        " / NULLIF(ABS(LAG(operating_cash_flow) OVER w), 0)",
        ("operating_cash_flow",),
        category="cash_flow",
        lag=True,
    ),
    _d(
        "capex_growth",
        "(capex - LAG(capex) OVER w)"
        " / NULLIF(ABS(LAG(capex) OVER w), 0)",
        ("capex",),
        category="cash_flow",
        lag=True,
    ),
    _d(
        "sloan_ratio",
        "(net_income - operating_cash_flow) / NULLIF(total_assets, 0)",
        ("net_income", "operating_cash_flow", "total_assets"),
        category="cash_flow",
    ),
    _d(
        "fcf_to_revenue",
        "free_cash_flow / NULLIF(revenue, 0)",
        ("free_cash_flow", "revenue"),
        category="cash_flow",
    ),
    _d(
        "fcf_per_share_derived",
        "free_cash_flow / NULLIF(weighted_avg_shares_diluted, 0)",
        ("free_cash_flow", "weighted_avg_shares_diluted"),
        category="cash_flow",
    ),
    _d(
        "dividends_to_fcf",
        "ABS(dividends_paid) / NULLIF(free_cash_flow, 0)",
        ("dividends_paid", "free_cash_flow"),
        category="cash_flow",
    ),
]
