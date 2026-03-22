"""Historical / point-in-time derived features.

These use daily market cap and other historical datasets to compute
valuation multiples and metrics at the correct point in time,
avoiding look-ahead bias in backtesting.
"""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # ── Daily valuation multiples (using hist_market_cap) ─────────────
    _d("hist_shares_outstanding",
       "hist_market_cap / NULLIF(close, 0)",
       ("hist_market_cap", "close"),
       category="historical", dtype="BIGINT"),

    _d("hist_pe_daily",
       "hist_market_cap / NULLIF(net_income, 0)",
       ("hist_market_cap", "net_income"),
       category="historical"),

    _d("hist_ps_daily",
       "hist_market_cap / NULLIF(revenue, 0)",
       ("hist_market_cap", "revenue"),
       category="historical"),

    _d("hist_pb_daily",
       "hist_market_cap / NULLIF(total_stockholders_equity, 0)",
       ("hist_market_cap", "total_stockholders_equity"),
       category="historical"),

    _d("hist_ev_daily",
       "hist_market_cap + total_debt - cash_and_equivalents",
       ("hist_market_cap", "total_debt", "cash_and_equivalents"),
       category="historical", dtype="BIGINT"),

    _d("hist_ev_to_ebitda_daily",
       "(hist_market_cap + total_debt - cash_and_equivalents) / NULLIF(ebitda, 0)",
       ("hist_market_cap", "total_debt", "cash_and_equivalents", "ebitda"),
       category="historical"),

    _d("hist_ev_to_revenue_daily",
       "(hist_market_cap + total_debt - cash_and_equivalents) / NULLIF(revenue, 0)",
       ("hist_market_cap", "total_debt", "cash_and_equivalents", "revenue"),
       category="historical"),

    _d("hist_ev_to_fcf_daily",
       "(hist_market_cap + total_debt - cash_and_equivalents) / NULLIF(free_cash_flow, 0)",
       ("hist_market_cap", "total_debt", "cash_and_equivalents", "free_cash_flow"),
       category="historical"),

    _d("hist_earnings_yield_daily",
       "net_income / NULLIF(hist_market_cap, 0)",
       ("net_income", "hist_market_cap"),
       category="historical"),

    _d("hist_fcf_yield_daily",
       "free_cash_flow / NULLIF(hist_market_cap, 0)",
       ("free_cash_flow", "hist_market_cap"),
       category="historical"),

    _d("hist_market_cap_growth",
       "(hist_market_cap - LAG(hist_market_cap) OVER w) / NULLIF(ABS(LAG(hist_market_cap) OVER w), 0)",
       ("hist_market_cap",),
       category="historical", lag=True),

    _d("hist_dividend_yield_daily",
       "ABS(dividends_paid) / NULLIF(hist_market_cap, 0)",
       ("dividends_paid", "hist_market_cap"),
       category="historical"),

    # ── Daily Altman Z-Score (uses daily market cap instead of snapshot) ──
    _d("hist_altman_z_daily",
       "1.2 * ((total_current_assets - total_current_liabilities) / NULLIF(total_assets, 0)) "
       "+ 1.4 * (retained_earnings / NULLIF(total_assets, 0)) "
       "+ 3.3 * ((ebitda - depreciation_and_amortization) / NULLIF(total_assets, 0)) "
       "+ 0.6 * (hist_market_cap / NULLIF(total_liabilities, 0)) "
       "+ 1.0 * (revenue / NULLIF(total_assets, 0))",
       ("total_current_assets", "total_current_liabilities", "total_assets",
        "retained_earnings", "ebitda", "depreciation_and_amortization",
        "total_liabilities", "hist_market_cap", "revenue"),
       category="historical"),

    # ── Historical analyst consensus metrics ──────────────────────────
    _d("hist_consensus_score",
       "(hist_strong_buy * 5.0 + hist_buy * 4.0 + hist_hold * 3.0 "
       "+ hist_sell * 2.0 + hist_strong_sell * 1.0) "
       "/ NULLIF(hist_strong_buy + hist_buy + hist_hold + hist_sell + hist_strong_sell, 0)",
       ("hist_strong_buy", "hist_buy", "hist_hold", "hist_sell", "hist_strong_sell"),
       category="historical"),

    _d("hist_buy_pct",
       "(hist_strong_buy + hist_buy) * 1.0 "
       "/ NULLIF(hist_strong_buy + hist_buy + hist_hold + hist_sell + hist_strong_sell, 0)",
       ("hist_strong_buy", "hist_buy", "hist_hold", "hist_sell", "hist_strong_sell"),
       category="historical"),

    _d("hist_sell_pct",
       "(hist_sell + hist_strong_sell) * 1.0 "
       "/ NULLIF(hist_strong_buy + hist_buy + hist_hold + hist_sell + hist_strong_sell, 0)",
       ("hist_strong_buy", "hist_buy", "hist_hold", "hist_sell", "hist_strong_sell"),
       category="historical"),

    _d("hist_analyst_count",
       "hist_strong_buy + hist_buy + hist_hold + hist_sell + hist_strong_sell",
       ("hist_strong_buy", "hist_buy", "hist_hold", "hist_sell", "hist_strong_sell"),
       category="historical", dtype="INTEGER"),

    # ── Historical institutional ownership metrics ────────────────────
    _d("hist_inst_ownership_growth",
       "hist_inst_holders_change / NULLIF(ABS(hist_inst_holders - hist_inst_holders_change), 0)",
       ("hist_inst_holders", "hist_inst_holders_change"),
       category="historical"),

    _d("hist_inst_investment_growth",
       "hist_inst_invested_change / NULLIF(ABS(hist_inst_invested - hist_inst_invested_change), 0)",
       ("hist_inst_invested", "hist_inst_invested_change"),
       category="historical"),
]
