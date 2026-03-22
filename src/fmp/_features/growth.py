"""§8 — Growth derived features.

All features in this module use ``LAG … OVER w`` and therefore require
``lag=True``.
"""

from __future__ import annotations

from fmp._features._base import _d

# Shorthand: standard YoY % change pattern
_YOY = "(({f}) - LAG({f}) OVER w) / NULLIF(ABS(LAG({f}) OVER w), 0)"

# Shorthand: period-over-period change (absolute, not %)
_CHG = "({f}) - LAG({f}) OVER w"


def _growth(name: str, field: str, deps: tuple[str, ...]) -> _d.__class__:
    """Build a standard YoY growth feature."""
    return _d(
        name,
        _YOY.format(f=field),
        deps,
        category="growth",
        lag=True,
    )


def _change(name: str, field: str, deps: tuple[str, ...]) -> _d.__class__:
    """Build an absolute-change feature (still requires LAG)."""
    return _d(
        name,
        _CHG.format(f=field),
        deps,
        category="growth",
        lag=True,
    )


FEATURES = [
    # ── Revenue & income ───────────────────────────────────────────
    _growth("revenue_growth_yoy", "revenue", ("revenue",)),
    _growth("gross_profit_growth", "gross_profit", ("gross_profit",)),
    _growth(
        "operating_income_growth", "operating_income", ("operating_income",)
    ),
    _growth("ebitda_growth", "ebitda", ("ebitda",)),
    _growth("net_income_growth", "net_income", ("net_income",)),
    _growth("eps_growth_yoy", "eps_diluted", ("eps_diluted",)),
    _growth("fcf_growth", "free_cash_flow", ("free_cash_flow",)),
    # ── Balance-sheet growth ───────────────────────────────────────
    _growth("asset_growth", "total_assets", ("total_assets",)),
    _growth(
        "book_value_growth",
        "total_stockholders_equity",
        ("total_stockholders_equity",),
    ),
    # ── Sustainable growth rate: ROE × retention ratio ─────────────
    _d(
        "sustainable_growth_rate",
        "(net_income / NULLIF(total_stockholders_equity, 0))"
        " * (1 - ABS(dividends_paid) / NULLIF(net_income, 0))",
        ("net_income", "total_stockholders_equity", "dividends_paid"),
        category="growth",
        lag=False,  # no LAG required — uses current-period data
    ),
    # ── Sequential / margin changes ────────────────────────────────
    _growth(
        "sequential_revenue_growth", "revenue", ("revenue",)
    ),
    _change(
        "operating_margin_change",
        "operating_income / NULLIF(revenue, 0)",
        ("operating_income", "revenue"),
    ),
    _change(
        "net_margin_change",
        "net_income / NULLIF(revenue, 0)",
        ("net_income", "revenue"),
    ),
    _change(
        "debt_to_equity_change",
        "total_debt / NULLIF(total_stockholders_equity, 0)",
        ("total_debt", "total_stockholders_equity"),
    ),
    _change(
        "current_ratio_change",
        "total_current_assets / NULLIF(total_current_liabilities, 0)",
        ("total_current_assets", "total_current_liabilities"),
    ),
    # ── Expense / investment growth ────────────────────────────────
    _growth("capex_growth_rate", "ABS(capex)", ("capex",)),
    _growth("rd_growth", "rd_expenses", ("rd_expenses",)),
    _growth("sga_growth", "sga_expenses", ("sga_expenses",)),
    # ── Working-capital & share-count changes ──────────────────────
    _change(
        "working_capital_change",
        "total_current_assets - total_current_liabilities",
        ("total_current_assets", "total_current_liabilities"),
    ),
    _growth(
        "share_count_change",
        "weighted_avg_shares_diluted",
        ("weighted_avg_shares_diluted",),
    ),
    # ── CAGR features (multi-year compounding) ───────────────────────
    _d(
        "revenue_cagr_3y",
        "POWER(revenue / NULLIF(LAG(revenue, 3) OVER w, 0), 1.0 / 3) - 1",
        ("revenue",),
        category="growth",
        lag=True,
    ),
    _d(
        "revenue_cagr_5y",
        "POWER(revenue / NULLIF(LAG(revenue, 5) OVER w, 0), 1.0 / 5) - 1",
        ("revenue",),
        category="growth",
        lag=True,
    ),
    _d(
        "eps_cagr_3y",
        "POWER(ABS(eps_diluted)"
        " / NULLIF(ABS(LAG(eps_diluted, 3) OVER w), 0), 1.0 / 3) - 1",
        ("eps_diluted",),
        category="growth",
        lag=True,
    ),
    _d(
        "eps_cagr_5y",
        "POWER(ABS(eps_diluted)"
        " / NULLIF(ABS(LAG(eps_diluted, 5) OVER w), 0), 1.0 / 5) - 1",
        ("eps_diluted",),
        category="growth",
        lag=True,
    ),
    _d(
        "dividend_growth_3y",
        "POWER(adj_dividend"
        " / NULLIF(LAG(adj_dividend, 3) OVER w, 0), 1.0 / 3) - 1",
        ("adj_dividend",),
        category="growth",
        lag=True,
    ),
    _d(
        "market_cap_growth",
        "(market_cap - LAG(market_cap) OVER w)"
        " / NULLIF(ABS(LAG(market_cap) OVER w), 0)",
        ("market_cap",),
        category="growth",
        lag=True,
    ),
    # ── 10-year CAGR features ───────────────────────────────────────────
    _d(
        "revenue_cagr_10y",
        "POWER(revenue / NULLIF(LAG(revenue, 10) OVER w, 0), 1.0 / 10) - 1",
        ("revenue",),
        category="growth",
        lag=True,
    ),
    _d(
        "eps_cagr_10y",
        "POWER(ABS(eps_diluted)"
        " / NULLIF(ABS(LAG(eps_diluted, 10) OVER w), 0), 1.0 / 10) - 1",
        ("eps_diluted",),
        category="growth",
        lag=True,
    ),
    _d(
        "dividend_growth_5y",
        "POWER(adj_dividend"
        " / NULLIF(LAG(adj_dividend, 5) OVER w, 0), 1.0 / 5) - 1",
        ("adj_dividend",),
        category="growth",
        lag=True,
    ),
    # ── Revenue growth consistency (5-period rolling stddev of YoY %) ───
    _d(
        "revenue_growth_consistency",
        "STDDEV(((revenue - LAG(revenue) OVER w)"
        " / NULLIF(ABS(LAG(revenue) OVER w), 0)))"
        " OVER (PARTITION BY symbol ORDER BY date"
        " ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)",
        ("revenue",),
        category="growth",
        lag=True,
    ),
]
