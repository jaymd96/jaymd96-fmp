"""§11 — Per-share derived features."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    _d(
        "eps_basic_derived",
        "net_income / NULLIF(weighted_avg_shares, 0)",
        ("net_income", "weighted_avg_shares"),
        category="per_share",
    ),
    _d(
        "eps_diluted_derived",
        "net_income / NULLIF(weighted_avg_shares_diluted, 0)",
        ("net_income", "weighted_avg_shares_diluted"),
        category="per_share",
    ),
    _d(
        "bvps",
        "total_stockholders_equity / NULLIF(shares_outstanding, 0)",
        ("total_stockholders_equity", "shares_outstanding"),
        category="per_share",
    ),
    _d(
        "tbvps",
        "(total_stockholders_equity - goodwill_and_intangibles)"
        " / NULLIF(shares_outstanding, 0)",
        ("total_stockholders_equity", "goodwill_and_intangibles", "shares_outstanding"),
        category="per_share",
    ),
    _d(
        "revenue_per_share_derived",
        "revenue / NULLIF(shares_outstanding, 0)",
        ("revenue", "shares_outstanding"),
        category="per_share",
    ),
    _d(
        "ocf_per_share",
        "operating_cash_flow / NULLIF(shares_outstanding, 0)",
        ("operating_cash_flow", "shares_outstanding"),
        category="per_share",
    ),
    _d(
        "fcf_per_share",
        "free_cash_flow / NULLIF(shares_outstanding, 0)",
        ("free_cash_flow", "shares_outstanding"),
        category="per_share",
    ),
    _d(
        "dividend_per_share",
        "adj_dividend",
        ("adj_dividend",),
        category="per_share",
    ),
    _d(
        "net_cash_per_share",
        "(cash_and_equivalents - total_debt) / NULLIF(shares_outstanding, 0)",
        ("cash_and_equivalents", "total_debt", "shares_outstanding"),
        category="per_share",
    ),
    _d(
        "ev_per_share_derived",
        "enterprise_value / NULLIF(shares_outstanding, 0)",
        ("enterprise_value", "shares_outstanding"),
        category="per_share",
    ),
    _d(
        "share_dilution_rate",
        "(weighted_avg_shares_diluted - LAG(weighted_avg_shares_diluted) OVER w)"
        " / NULLIF(ABS(LAG(weighted_avg_shares_diluted) OVER w), 0)",
        ("weighted_avg_shares_diluted",),
        category="per_share",
        lag=True,
    ),
]
