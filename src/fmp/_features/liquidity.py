"""§3 — Liquidity derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    _d(
        "current_ratio_derived",
        "total_current_assets / NULLIF(total_current_liabilities, 0)",
        ("total_current_assets", "total_current_liabilities"),
        category="liquidity",
    ),
    _d(
        "quick_ratio",
        "(total_current_assets - inventory) / NULLIF(total_current_liabilities, 0)",
        ("total_current_assets", "inventory", "total_current_liabilities"),
        category="liquidity",
    ),
    _d(
        "cash_ratio",
        "(cash_and_equivalents + short_term_investments)"
        " / NULLIF(total_current_liabilities, 0)",
        (
            "cash_and_equivalents",
            "short_term_investments",
            "total_current_liabilities",
        ),
        category="liquidity",
    ),
    _d(
        "working_capital",
        "total_current_assets - total_current_liabilities",
        ("total_current_assets", "total_current_liabilities"),
        category="liquidity",
    ),
    _d(
        "working_capital_to_revenue",
        "(total_current_assets - total_current_liabilities)"
        " / NULLIF(revenue, 0)",
        ("total_current_assets", "total_current_liabilities", "revenue"),
        category="liquidity",
    ),
    _d(
        "nwc_to_total_assets",
        "(total_current_assets - total_current_liabilities)"
        " / NULLIF(total_assets, 0)",
        ("total_current_assets", "total_current_liabilities", "total_assets"),
        category="liquidity",
    ),
    _d(
        "defensive_interval",
        "(cash_and_equivalents + short_term_investments + net_receivables)"
        " / NULLIF(operating_expenses / 365.0, 0)",
        (
            "cash_and_equivalents",
            "short_term_investments",
            "net_receivables",
            "operating_expenses",
        ),
        category="liquidity",
    ),
    _d(
        "cash_conversion_cycle",
        # DIO + DSO - DPO inlined from efficiency definitions
        "(inventory / NULLIF(cost_of_revenue / 365.0, 0))"
        " + (net_receivables / NULLIF(revenue / 365.0, 0))"
        " - (accounts_payable / NULLIF(cost_of_revenue / 365.0, 0))",
        (
            "inventory",
            "cost_of_revenue",
            "net_receivables",
            "revenue",
            "accounts_payable",
        ),
        category="liquidity",
    ),
    _d(
        "ocf_ratio",
        "operating_cash_flow / NULLIF(total_current_liabilities, 0)",
        ("operating_cash_flow", "total_current_liabilities"),
        category="liquidity",
    ),
    _d(
        "net_debt_derived",
        "total_debt - cash_and_equivalents",
        ("total_debt", "cash_and_equivalents"),
        category="liquidity",
    ),
    _d(
        "net_debt_to_ebitda",
        "(total_debt - cash_and_equivalents) / NULLIF(ebitda, 0)",
        ("total_debt", "cash_and_equivalents", "ebitda"),
        category="liquidity",
    ),
    _d(
        "cash_burn_rate",
        "operating_cash_flow / 12.0",
        ("operating_cash_flow",),
        category="liquidity",
    ),
    _d(
        "cash_runway_months",
        "cash_and_equivalents / NULLIF(-operating_cash_flow / 12.0, 0)",
        ("cash_and_equivalents", "operating_cash_flow"),
        category="liquidity",
    ),
]
