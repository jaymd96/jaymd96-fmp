"""§1 — Composite scoring model derived features."""

from __future__ import annotations

from fmp._features._base import _d

# ── Shared sub-expressions ──────────────────────────────────────────────
_X1 = "(total_current_assets - total_current_liabilities) / NULLIF(total_assets, 0)"
_X2 = "retained_earnings / NULLIF(total_assets, 0)"
_X3 = "(ebitda - depreciation_and_amortization) / NULLIF(total_assets, 0)"
_X5 = "revenue / NULLIF(total_assets, 0)"

FEATURES = [
    # ── Altman Z-Score variants ──────────────────────────────────────
    _d(
        "altman_z_score",
        f"1.2 * ({_X1}) "
        f"+ 1.4 * ({_X2}) "
        f"+ 3.3 * ({_X3}) "
        "+ 0.6 * (quote_market_cap / NULLIF(total_liabilities, 0)) "
        f"+ 1.0 * ({_X5})",
        (
            "total_current_assets",
            "total_current_liabilities",
            "total_assets",
            "retained_earnings",
            "ebitda",
            "depreciation_and_amortization",
            "total_liabilities",
            "quote_market_cap",
            "revenue",
        ),
        category="composite",
    ),
    _d(
        "altman_z_prime",
        f"0.717 * ({_X1}) "
        f"+ 0.847 * ({_X2}) "
        f"+ 3.107 * ({_X3}) "
        "+ 0.420 * (total_stockholders_equity / NULLIF(total_liabilities, 0)) "
        f"+ 0.998 * ({_X5})",
        (
            "total_current_assets",
            "total_current_liabilities",
            "total_assets",
            "retained_earnings",
            "ebitda",
            "depreciation_and_amortization",
            "total_liabilities",
            "total_stockholders_equity",
            "revenue",
        ),
        category="composite",
    ),
    _d(
        "altman_z_double_prime",
        f"3.25 + 6.56 * ({_X1}) "
        f"+ 3.26 * ({_X2}) "
        f"+ 6.72 * ({_X3}) "
        "+ 1.05 * (total_stockholders_equity / NULLIF(total_liabilities, 0))",
        (
            "total_current_assets",
            "total_current_liabilities",
            "total_assets",
            "retained_earnings",
            "ebitda",
            "depreciation_and_amortization",
            "total_liabilities",
            "total_stockholders_equity",
        ),
        category="composite",
    ),
    # ── Piotroski F-Score ────────────────────────────────────────────
    _d(
        "piotroski_f_score",
        # F1: ROA positive
        "CASE WHEN net_income > 0 THEN 1 ELSE 0 END + "
        # F2: OCF positive
        "CASE WHEN operating_cash_flow > 0 THEN 1 ELSE 0 END + "
        # F3: Delta ROA positive
        "CASE WHEN (net_income / NULLIF(total_assets, 0)) > "
        "(LAG(net_income) OVER w / NULLIF(LAG(total_assets) OVER w, 0)) "
        "THEN 1 ELSE 0 END + "
        # F4: OCF > NI (accruals quality)
        "CASE WHEN operating_cash_flow > net_income THEN 1 ELSE 0 END + "
        # F5: Leverage decreased
        "CASE WHEN (long_term_debt / NULLIF(total_assets, 0)) < "
        "(LAG(long_term_debt) OVER w / NULLIF(LAG(total_assets) OVER w, 0)) "
        "THEN 1 ELSE 0 END + "
        # F6: Current ratio improved
        "CASE WHEN (total_current_assets / NULLIF(total_current_liabilities, 0)) > "
        "(LAG(total_current_assets) OVER w / NULLIF(LAG(total_current_liabilities) OVER w, 0)) "
        "THEN 1 ELSE 0 END + "
        # F7: No dilution
        "CASE WHEN weighted_avg_shares_diluted <= LAG(weighted_avg_shares_diluted) OVER w "
        "THEN 1 ELSE 0 END + "
        # F8: Gross margin improved
        "CASE WHEN (gross_profit / NULLIF(revenue, 0)) > "
        "(LAG(gross_profit) OVER w / NULLIF(LAG(revenue) OVER w, 0)) "
        "THEN 1 ELSE 0 END + "
        # F9: Asset turnover improved
        "CASE WHEN (revenue / NULLIF(total_assets, 0)) > "
        "(LAG(revenue) OVER w / NULLIF(LAG(total_assets) OVER w, 0)) "
        "THEN 1 ELSE 0 END",
        (
            "net_income",
            "operating_cash_flow",
            "total_assets",
            "long_term_debt",
            "total_current_assets",
            "total_current_liabilities",
            "weighted_avg_shares_diluted",
            "gross_profit",
            "revenue",
        ),
        category="composite",
        dtype="INTEGER",
        lag=True,
    ),
    # ── Beneish M-Score components ───────────────────────────────────
    _d(
        "beneish_dsri",
        "(net_receivables / NULLIF(revenue, 0))"
        " / NULLIF(LAG(net_receivables) OVER w"
        " / NULLIF(LAG(revenue) OVER w, 0), 0)",
        ("net_receivables", "revenue"),
        category="composite",
        lag=True,
    ),
    _d(
        "beneish_gmi",
        "(LAG(gross_profit) OVER w / NULLIF(LAG(revenue) OVER w, 0))"
        " / NULLIF(gross_profit / NULLIF(revenue, 0), 0)",
        ("gross_profit", "revenue"),
        category="composite",
        lag=True,
    ),
    _d(
        "beneish_aqi",
        "((total_assets - total_current_assets - property_plant_equipment)"
        " / NULLIF(total_assets, 0))"
        " / NULLIF("
        "(LAG(total_assets) OVER w - LAG(total_current_assets) OVER w"
        " - LAG(property_plant_equipment) OVER w)"
        " / NULLIF(LAG(total_assets) OVER w, 0), 0)",
        ("total_assets", "total_current_assets", "property_plant_equipment"),
        category="composite",
        lag=True,
    ),
    _d(
        "beneish_sgi",
        "revenue / NULLIF(LAG(revenue) OVER w, 0)",
        ("revenue",),
        category="composite",
        lag=True,
    ),
    _d(
        "beneish_depi",
        "(LAG(depreciation_and_amortization) OVER w"
        " / NULLIF(LAG(depreciation_and_amortization) OVER w"
        " + LAG(property_plant_equipment) OVER w, 0))"
        " / NULLIF(depreciation_and_amortization"
        " / NULLIF(depreciation_and_amortization + property_plant_equipment, 0), 0)",
        ("depreciation_and_amortization", "property_plant_equipment"),
        category="composite",
        lag=True,
    ),
    _d(
        "beneish_sgai",
        "(selling_general_and_administrative / NULLIF(revenue, 0))"
        " / NULLIF(LAG(selling_general_and_administrative) OVER w"
        " / NULLIF(LAG(revenue) OVER w, 0), 0)",
        ("selling_general_and_administrative", "revenue"),
        category="composite",
        lag=True,
    ),
    _d(
        "beneish_tata",
        "(net_income - operating_cash_flow) / NULLIF(total_assets, 0)",
        ("net_income", "operating_cash_flow", "total_assets"),
        category="composite",
    ),
    _d(
        "beneish_lvgi",
        "(total_liabilities / NULLIF(total_assets, 0))"
        " / NULLIF(LAG(total_liabilities) OVER w"
        " / NULLIF(LAG(total_assets) OVER w, 0), 0)",
        ("total_liabilities", "total_assets"),
        category="composite",
        lag=True,
    ),
    # ── Beneish M-Score (composite) ──────────────────────────────────
    _d(
        "beneish_m_score",
        "-4.84"
        # DSRI
        " + 0.920 * ((net_receivables / NULLIF(revenue, 0))"
        " / NULLIF(LAG(net_receivables) OVER w"
        " / NULLIF(LAG(revenue) OVER w, 0), 0))"
        # GMI
        " + 0.528 * ((LAG(gross_profit) OVER w / NULLIF(LAG(revenue) OVER w, 0))"
        " / NULLIF(gross_profit / NULLIF(revenue, 0), 0))"
        # AQI
        " + 0.404 * (((total_assets - total_current_assets - property_plant_equipment)"
        " / NULLIF(total_assets, 0))"
        " / NULLIF("
        "(LAG(total_assets) OVER w - LAG(total_current_assets) OVER w"
        " - LAG(property_plant_equipment) OVER w)"
        " / NULLIF(LAG(total_assets) OVER w, 0), 0))"
        # SGI
        " + 0.892 * (revenue / NULLIF(LAG(revenue) OVER w, 0))"
        # DEPI
        " + 0.115 * ((LAG(depreciation_and_amortization) OVER w"
        " / NULLIF(LAG(depreciation_and_amortization) OVER w"
        " + LAG(property_plant_equipment) OVER w, 0))"
        " / NULLIF(depreciation_and_amortization"
        " / NULLIF(depreciation_and_amortization + property_plant_equipment, 0), 0))"
        # SGAI
        " - 0.172 * ((selling_general_and_administrative / NULLIF(revenue, 0))"
        " / NULLIF(LAG(selling_general_and_administrative) OVER w"
        " / NULLIF(LAG(revenue) OVER w, 0), 0))"
        # TATA
        " + 4.679 * ((net_income - operating_cash_flow) / NULLIF(total_assets, 0))"
        # LVGI
        " - 0.327 * ((total_liabilities / NULLIF(total_assets, 0))"
        " / NULLIF(LAG(total_liabilities) OVER w"
        " / NULLIF(LAG(total_assets) OVER w, 0), 0))",
        (
            "net_receivables",
            "revenue",
            "gross_profit",
            "total_assets",
            "total_current_assets",
            "property_plant_equipment",
            "depreciation_and_amortization",
            "selling_general_and_administrative",
            "net_income",
            "operating_cash_flow",
            "total_liabilities",
        ),
        category="composite",
        lag=True,
    ),
    # ── Graham Number & Margin of Safety ─────────────────────────────
    _d(
        "graham_number",
        "SQRT(22.5 * ABS(eps_diluted)"
        " * ABS(total_stockholders_equity / NULLIF(shares_outstanding, 0)))",
        ("eps_diluted", "total_stockholders_equity", "shares_outstanding"),
        category="composite",
    ),
    _d(
        "graham_margin_of_safety",
        "(SQRT(22.5 * ABS(eps_diluted)"
        " * ABS(total_stockholders_equity / NULLIF(shares_outstanding, 0)))"
        " - price) / NULLIF(price, 0)",
        ("eps_diluted", "total_stockholders_equity", "shares_outstanding", "price"),
        category="composite",
    ),
    # ── Magic Formula components ─────────────────────────────────────
    _d(
        "earnings_yield_magic",
        "(ebitda - depreciation_and_amortization) / NULLIF(enterprise_value, 0)",
        ("ebitda", "depreciation_and_amortization", "enterprise_value"),
        category="composite",
    ),
    _d(
        "return_on_capital_magic",
        "(ebitda - depreciation_and_amortization)"
        " / NULLIF(property_plant_equipment"
        " + total_current_assets - total_current_liabilities, 0)",
        (
            "ebitda",
            "depreciation_and_amortization",
            "property_plant_equipment",
            "total_current_assets",
            "total_current_liabilities",
        ),
        category="composite",
    ),
    # ── Acquirers Multiple ───────────────────────────────────────────
    _d(
        "acquirers_multiple",
        "enterprise_value / NULLIF(ebitda, 0)",
        ("enterprise_value", "ebitda"),
        category="composite",
    ),
]
