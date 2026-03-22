"""§5 — Efficiency derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Turnover ratios ────────────────────────────────────────────
    _d(
        "asset_turnover_derived",
        "revenue / NULLIF(total_assets, 0)",
        ("revenue", "total_assets"),
        category="efficiency",
    ),
    _d(
        "fixed_asset_turnover",
        "revenue / NULLIF(property_plant_equipment, 0)",
        ("revenue", "property_plant_equipment"),
        category="efficiency",
    ),
    _d(
        "inventory_turnover",
        "cost_of_revenue / NULLIF(inventory, 0)",
        ("cost_of_revenue", "inventory"),
        category="efficiency",
    ),
    _d(
        "dio",
        "inventory / NULLIF(cost_of_revenue / 365.0, 0)",
        ("inventory", "cost_of_revenue"),
        category="efficiency",
    ),
    _d(
        "receivables_turnover",
        "revenue / NULLIF(net_receivables, 0)",
        ("revenue", "net_receivables"),
        category="efficiency",
    ),
    _d(
        "dso",
        "net_receivables / NULLIF(revenue / 365.0, 0)",
        ("net_receivables", "revenue"),
        category="efficiency",
    ),
    _d(
        "payables_turnover",
        "cost_of_revenue / NULLIF(accounts_payable, 0)",
        ("cost_of_revenue", "accounts_payable"),
        category="efficiency",
    ),
    _d(
        "dpo",
        "accounts_payable / NULLIF(cost_of_revenue / 365.0, 0)",
        ("accounts_payable", "cost_of_revenue"),
        category="efficiency",
    ),
    _d(
        "ccc",
        # DIO + DSO - DPO
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
        category="efficiency",
    ),
    _d(
        "working_capital_turnover",
        "revenue / NULLIF(total_current_assets - total_current_liabilities, 0)",
        ("revenue", "total_current_assets", "total_current_liabilities"),
        category="efficiency",
    ),
    _d(
        "equity_turnover",
        "revenue / NULLIF(total_stockholders_equity, 0)",
        ("revenue", "total_stockholders_equity"),
        category="efficiency",
    ),
    _d(
        "capital_turnover",
        "revenue"
        " / NULLIF(total_debt + total_stockholders_equity - cash_and_equivalents, 0)",
        (
            "revenue",
            "total_debt",
            "total_stockholders_equity",
            "cash_and_equivalents",
        ),
        category="efficiency",
    ),
    # ── Employee productivity ────────────────────────────────────────
    _d(
        "revenue_per_employee",
        "revenue / NULLIF(employee_count_val, 0)",
        ("revenue", "employee_count_val"),
        category="efficiency",
    ),
    _d(
        "net_income_per_employee",
        "net_income / NULLIF(employee_count_val, 0)",
        ("net_income", "employee_count_val"),
        category="efficiency",
    ),
    # ── Expense ratios ─────────────────────────────────────────────
    _d(
        "opex_ratio",
        "operating_expenses / NULLIF(revenue, 0)",
        ("operating_expenses", "revenue"),
        category="efficiency",
    ),
    _d(
        "sga_to_revenue",
        "sga_expenses / NULLIF(revenue, 0)",
        ("sga_expenses", "revenue"),
        category="efficiency",
    ),
    _d(
        "rd_to_revenue",
        "rd_expenses / NULLIF(revenue, 0)",
        ("rd_expenses", "revenue"),
        category="efficiency",
    ),
    _d(
        "rd_to_gross_profit",
        "rd_expenses / NULLIF(gross_profit, 0)",
        ("rd_expenses", "gross_profit"),
        category="efficiency",
    ),
    _d(
        "capex_to_revenue",
        "ABS(capex) / NULLIF(revenue, 0)",
        ("capex", "revenue"),
        category="efficiency",
    ),
    _d(
        "capex_to_depreciation",
        "ABS(capex) / NULLIF(depreciation_and_amortization, 0)",
        ("capex", "depreciation_and_amortization"),
        category="efficiency",
    ),
]
