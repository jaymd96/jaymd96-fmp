"""§12 — Dividend & shareholder-return derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    _d(
        "trailing_dividend_yield",
        "adj_dividend * 4 / NULLIF(price, 0)",
        ("adj_dividend", "price"),
        category="dividend",
    ),
    _d(
        "dividend_payout_ratio",
        "adj_dividend / NULLIF(eps_diluted, 0)",
        ("adj_dividend", "eps_diluted"),
        category="dividend",
    ),
    _d(
        "fcf_payout_ratio",
        "ABS(dividends_paid) / NULLIF(free_cash_flow, 0)",
        ("dividends_paid", "free_cash_flow"),
        category="dividend",
    ),
    _d(
        "dividend_coverage",
        "eps_diluted / NULLIF(adj_dividend, 0)",
        ("eps_diluted", "adj_dividend"),
        category="dividend",
    ),
    _d(
        "buyback_yield",
        "ABS(share_repurchase) / NULLIF(quote_market_cap, 0)",
        ("share_repurchase", "quote_market_cap"),
        category="dividend",
    ),
    _d(
        "shareholder_yield_total",
        "(ABS(dividends_paid) + ABS(share_repurchase))"
        " / NULLIF(quote_market_cap, 0)",
        ("dividends_paid", "share_repurchase", "quote_market_cap"),
        category="dividend",
    ),
    _d(
        "dividend_growth",
        "(adj_dividend - LAG(adj_dividend) OVER w)"
        " / NULLIF(ABS(LAG(adj_dividend) OVER w), 0)",
        ("adj_dividend",),
        category="dividend",
        lag=True,
    ),
    _d(
        "net_issuance_rate",
        "(weighted_avg_shares_diluted - LAG(weighted_avg_shares_diluted) OVER w)"
        " / NULLIF(ABS(LAG(weighted_avg_shares_diluted) OVER w), 0)",
        ("weighted_avg_shares_diluted",),
        category="dividend",
        lag=True,
    ),
    _d(
        "dividends_to_net_income",
        "ABS(dividends_paid) / NULLIF(net_income, 0)",
        ("dividends_paid", "net_income"),
        category="dividend",
    ),
    # total_shareholder_return_proxy: requires change_pct which is not a base
    # ontology field. Approximated with dividend yield component only.
    _d(
        "total_shareholder_return_proxy",
        "(close - LAG(close) OVER w) / NULLIF(LAG(close) OVER w, 0)"
        " + (adj_dividend / NULLIF(close, 0))",
        ("close", "adj_dividend"),
        category="dividend",
        lag=True,
    ),
]
