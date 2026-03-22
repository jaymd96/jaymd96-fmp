"""§2 — Profitability derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Margin ratios ──────────────────────────────────────────────
    _d(
        "gross_profit_margin",
        "gross_profit / NULLIF(revenue, 0)",
        ("gross_profit", "revenue"),
        category="profitability",
    ),
    _d(
        "operating_profit_margin",
        "operating_income / NULLIF(revenue, 0)",
        ("operating_income", "revenue"),
        category="profitability",
    ),
    _d(
        "net_profit_margin",
        "net_income / NULLIF(revenue, 0)",
        ("net_income", "revenue"),
        category="profitability",
    ),
    _d(
        "ebitda_margin",
        "ebitda / NULLIF(revenue, 0)",
        ("ebitda", "revenue"),
        category="profitability",
    ),
    _d(
        "ebit_margin",
        "(ebitda - depreciation_and_amortization) / NULLIF(revenue, 0)",
        ("ebitda", "depreciation_and_amortization", "revenue"),
        category="profitability",
    ),
    # ── Return ratios ──────────────────────────────────────────────
    _d(
        "return_on_assets",
        "net_income / NULLIF(total_assets, 0)",
        ("net_income", "total_assets"),
        category="profitability",
    ),
    _d(
        "return_on_equity",
        "net_income / NULLIF(total_stockholders_equity, 0)",
        ("net_income", "total_stockholders_equity"),
        category="profitability",
    ),
    _d(
        "roic_derived",
        "(operating_income * (1 - income_tax_expense / NULLIF(income_before_tax, 0)))"
        " / NULLIF(total_debt + total_stockholders_equity - cash_and_equivalents, 0)",
        (
            "operating_income",
            "income_tax_expense",
            "income_before_tax",
            "total_debt",
            "total_stockholders_equity",
            "cash_and_equivalents",
        ),
        category="profitability",
    ),
    _d(
        "roce",
        "(ebitda - depreciation_and_amortization)"
        " / NULLIF(total_assets - total_current_liabilities, 0)",
        (
            "ebitda",
            "depreciation_and_amortization",
            "total_assets",
            "total_current_liabilities",
        ),
        category="profitability",
    ),
    _d(
        "return_on_tangible_assets",
        "net_income / NULLIF(total_assets - goodwill_and_intangibles, 0)",
        ("net_income", "total_assets", "goodwill_and_intangibles"),
        category="profitability",
    ),
    _d(
        "return_on_net_assets",
        "net_income / NULLIF(total_assets - total_current_liabilities, 0)",
        ("net_income", "total_assets", "total_current_liabilities"),
        category="profitability",
    ),
    _d(
        "operating_return_on_assets",
        "operating_income / NULLIF(total_assets, 0)",
        ("operating_income", "total_assets"),
        category="profitability",
    ),
    _d(
        "cash_return_on_assets",
        "operating_cash_flow / NULLIF(total_assets, 0)",
        ("operating_cash_flow", "total_assets"),
        category="profitability",
    ),
    _d(
        "cash_return_on_ic",
        "operating_cash_flow"
        " / NULLIF(total_debt + total_stockholders_equity - cash_and_equivalents, 0)",
        (
            "operating_cash_flow",
            "total_debt",
            "total_stockholders_equity",
            "cash_and_equivalents",
        ),
        category="profitability",
    ),
    # ── Tax / interest decomposition ───────────────────────────────
    _d(
        "effective_tax_rate",
        "income_tax_expense / NULLIF(income_before_tax, 0)",
        ("income_tax_expense", "income_before_tax"),
        category="profitability",
    ),
    _d(
        "tax_burden_ratio",
        "net_income / NULLIF(income_before_tax, 0)",
        ("net_income", "income_before_tax"),
        category="profitability",
    ),
    _d(
        "interest_burden_ratio",
        "income_before_tax / NULLIF(operating_income, 0)",
        ("income_before_tax", "operating_income"),
        category="profitability",
    ),
    # ── Economic profit ────────────────────────────────────────────
    _d(
        "nopat",
        "operating_income * (1 - income_tax_expense / NULLIF(income_before_tax, 0))",
        ("operating_income", "income_tax_expense", "income_before_tax"),
        category="profitability",
    ),
    _d(
        "economic_profit_proxy",
        "(operating_income * (1 - income_tax_expense / NULLIF(income_before_tax, 0)))"
        " - 0.10 * (total_debt + total_stockholders_equity - cash_and_equivalents)",
        (
            "operating_income",
            "income_tax_expense",
            "income_before_tax",
            "total_debt",
            "total_stockholders_equity",
            "cash_and_equivalents",
        ),
        category="profitability",
    ),
    _d(
        "roic_wacc_spread",
        "(operating_income * (1 - income_tax_expense / NULLIF(income_before_tax, 0)))"
        " / NULLIF(total_debt + total_stockholders_equity - cash_and_equivalents, 0)"
        " - 0.10",
        (
            "operating_income",
            "income_tax_expense",
            "income_before_tax",
            "total_debt",
            "total_stockholders_equity",
            "cash_and_equivalents",
        ),
        category="profitability",
    ),
]
