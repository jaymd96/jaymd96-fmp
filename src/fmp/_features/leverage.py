"""§4 — Leverage derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Capital-structure ratios ───────────────────────────────────
    _d(
        "debt_to_equity_derived",
        "total_debt / NULLIF(total_stockholders_equity, 0)",
        ("total_debt", "total_stockholders_equity"),
        category="leverage",
    ),
    _d(
        "debt_to_assets_derived",
        "total_debt / NULLIF(total_assets, 0)",
        ("total_debt", "total_assets"),
        category="leverage",
    ),
    _d(
        "equity_multiplier",
        "total_assets / NULLIF(total_stockholders_equity, 0)",
        ("total_assets", "total_stockholders_equity"),
        category="leverage",
    ),
    _d(
        "lt_debt_to_cap",
        "long_term_debt / NULLIF(long_term_debt + total_stockholders_equity, 0)",
        ("long_term_debt", "total_stockholders_equity"),
        category="leverage",
    ),
    # ── Coverage ratios ────────────────────────────────────────────
    _d(
        "interest_coverage",
        "(ebitda - depreciation_and_amortization) / NULLIF(interest_expense, 0)",
        ("ebitda", "depreciation_and_amortization", "interest_expense"),
        category="leverage",
    ),
    _d(
        "ebitda_interest_coverage",
        "ebitda / NULLIF(interest_expense, 0)",
        ("ebitda", "interest_expense"),
        category="leverage",
    ),
    _d(
        "cf_coverage",
        "operating_cash_flow / NULLIF(interest_expense, 0)",
        ("operating_cash_flow", "interest_expense"),
        category="leverage",
    ),
    _d(
        "fixed_charge_coverage",
        "(ebitda - depreciation_and_amortization + interest_expense)"
        " / NULLIF(interest_expense + debt_repayment, 0)",
        (
            "ebitda",
            "depreciation_and_amortization",
            "interest_expense",
            "debt_repayment",
        ),
        category="leverage",
    ),
    _d(
        "debt_service_coverage",
        "operating_cash_flow / NULLIF(interest_expense + debt_repayment, 0)",
        ("operating_cash_flow", "interest_expense", "debt_repayment"),
        category="leverage",
    ),
    # ── Leverage degree metrics ────────────────────────────────────
    _d(
        "financial_leverage_dfl",
        "(ebitda - depreciation_and_amortization)"
        " / NULLIF(ebitda - depreciation_and_amortization - interest_expense, 0)",
        ("ebitda", "depreciation_and_amortization", "interest_expense"),
        category="leverage",
    ),
    _d(
        "operating_leverage_dol",
        "CASE WHEN LAG(operating_income) OVER w = 0 OR LAG(revenue) OVER w = 0"
        " THEN NULL"
        " ELSE ((operating_income - LAG(operating_income) OVER w)"
        " / NULLIF(ABS(LAG(operating_income) OVER w), 0))"
        " / NULLIF((revenue - LAG(revenue) OVER w)"
        " / NULLIF(ABS(LAG(revenue) OVER w), 0), 0)"
        " END",
        ("operating_income", "revenue"),
        category="leverage",
        lag=True,
    ),
    _d(
        "combined_leverage_dtl",
        "CASE WHEN LAG(net_income) OVER w = 0 OR LAG(revenue) OVER w = 0"
        " THEN NULL"
        " ELSE ((net_income - LAG(net_income) OVER w)"
        " / NULLIF(ABS(LAG(net_income) OVER w), 0))"
        " / NULLIF((revenue - LAG(revenue) OVER w)"
        " / NULLIF(ABS(LAG(revenue) OVER w), 0), 0)"
        " END",
        ("net_income", "revenue"),
        category="leverage",
        lag=True,
    ),
    # ── Net-debt variants ──────────────────────────────────────────
    _d(
        "net_debt_to_equity",
        "(total_debt - cash_and_equivalents)"
        " / NULLIF(total_stockholders_equity, 0)",
        ("total_debt", "cash_and_equivalents", "total_stockholders_equity"),
        category="leverage",
    ),
    _d(
        "tangible_net_worth",
        "total_stockholders_equity - goodwill_and_intangibles",
        ("total_stockholders_equity", "goodwill_and_intangibles"),
        category="leverage",
    ),
    _d(
        "debt_to_tangible_nw",
        "total_debt"
        " / NULLIF(total_stockholders_equity - goodwill_and_intangibles, 0)",
        ("total_debt", "total_stockholders_equity", "goodwill_and_intangibles"),
        category="leverage",
    ),
    # ── Interest income / expense ──────────────────────────────────
    _d(
        "interest_income_to_expense",
        "interest_income / NULLIF(interest_expense, 0)",
        ("interest_income", "interest_expense"),
        category="leverage",
    ),
    _d(
        "net_interest_margin",
        "(interest_income - interest_expense) / NULLIF(total_assets, 0)",
        ("interest_income", "interest_expense", "total_assets"),
        category="leverage",
    ),
]
