"""§9 — DuPont decomposition derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    _d(
        "tax_burden",
        "net_income / NULLIF(income_before_tax, 0)",
        ("net_income", "income_before_tax"),
        category="dupont",
    ),
    _d(
        "interest_burden",
        "income_before_tax / NULLIF(operating_income, 0)",
        ("income_before_tax", "operating_income"),
        category="dupont",
    ),
    _d(
        "dupont_operating_margin",
        "operating_income / NULLIF(revenue, 0)",
        ("operating_income", "revenue"),
        category="dupont",
    ),
    _d(
        "dupont_asset_turnover",
        "revenue / NULLIF(total_assets, 0)",
        ("revenue", "total_assets"),
        category="dupont",
    ),
    _d(
        "dupont_equity_multiplier",
        "total_assets / NULLIF(total_stockholders_equity, 0)",
        ("total_assets", "total_stockholders_equity"),
        category="dupont",
    ),
    _d(
        "roe_3factor",
        "(net_income / NULLIF(revenue, 0))"
        " * (revenue / NULLIF(total_assets, 0))"
        " * (total_assets / NULLIF(total_stockholders_equity, 0))",
        ("net_income", "revenue", "total_assets", "total_stockholders_equity"),
        category="dupont",
    ),
    _d(
        "roe_5factor",
        "(net_income / NULLIF(income_before_tax, 0))"
        " * (income_before_tax / NULLIF(operating_income, 0))"
        " * (operating_income / NULLIF(revenue, 0))"
        " * (revenue / NULLIF(total_assets, 0))"
        " * (total_assets / NULLIF(total_stockholders_equity, 0))",
        (
            "net_income",
            "income_before_tax",
            "operating_income",
            "revenue",
            "total_assets",
            "total_stockholders_equity",
        ),
        category="dupont",
    ),
]
