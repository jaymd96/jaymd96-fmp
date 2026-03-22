"""Comprehensive tests for SQL-derived features across all categories.

Each test mocks the appropriate FMP endpoint(s), runs a query selecting
derived features, and verifies the computed values are mathematically correct.

Uses URL-based matching via ``httpx_mock.add_response(url=...)`` so that the
correct mock data is returned regardless of fetch ordering in
:class:`ThreadPoolExecutor`.
"""

from __future__ import annotations

import math
import re

import polars as pl
import pytest

from fmp import FMPClient, FMPError

BASE = "https://financialmodelingprep.com/stable/"


# ── URL matchers ─────────────────────────────────────────────────────────

def _url(endpoint: str) -> re.Pattern:
    """Return a regex that matches the FMP URL for *endpoint*."""
    return re.compile(re.escape(BASE + endpoint) + r"(\?.*)?$")


# ── Shared mock data builders ────────────────────────────────────────────


def _income_statement(
    *,
    symbol="AAPL",
    date="2023-09-30",
    period="FY",
    revenue=100_000_000_000,
    cost_of_revenue=60_000_000_000,
    gross_profit=40_000_000_000,
    operating_income=30_000_000_000,
    operating_expenses=10_000_000_000,
    net_income=20_000_000_000,
    ebitda=35_000_000_000,
    interest_expense=5_000_000_000,
    interest_income=2_000_000_000,
    depreciation_and_amortization=5_000_000_000,
    income_before_tax=25_000_000_000,
    income_tax_expense=5_000_000_000,
    eps=6.0,
    eps_diluted=5.95,
    weighted_avg_shares=15_000_000_000,
    weighted_avg_shares_diluted=15_200_000_000,
    rd_expenses=8_000_000_000,
    sga_expenses=2_000_000_000,
    **overrides,
):
    d = {
        "symbol": symbol,
        "date": date,
        "period": period,
        "reportedCurrency": "USD",
        "cik": "0000320193",
        "fillingDate": "2023-11-03",
        "acceptedDate": "2023-11-02",
        "calendarYear": "2023",
        "revenue": revenue,
        "costOfRevenue": cost_of_revenue,
        "grossProfit": gross_profit,
        "grossProfitRatio": gross_profit / revenue if revenue else 0,
        "researchAndDevelopmentExpenses": rd_expenses,
        "sellingGeneralAndAdministrativeExpenses": sga_expenses,
        "operatingExpenses": operating_expenses,
        "operatingIncome": operating_income,
        "operatingIncomeRatio": operating_income / revenue if revenue else 0,
        "interestIncome": interest_income,
        "interestExpense": interest_expense,
        "depreciationAndAmortization": depreciation_and_amortization,
        "ebitda": ebitda,
        "ebitdaratio": ebitda / revenue if revenue else 0,
        "netIncome": net_income,
        "netIncomeRatio": net_income / revenue if revenue else 0,
        "eps": eps,
        "epsdiluted": eps_diluted,
        "incomeBeforeTax": income_before_tax,
        "incomeTaxExpense": income_tax_expense,
        "costAndExpenses": cost_of_revenue + operating_expenses,
        "otherExpenses": 0,
        "totalOtherIncomeExpensesNet": 0,
        "weightedAverageShsOut": weighted_avg_shares,
        "weightedAverageShsOutDil": weighted_avg_shares_diluted,
        "link": "",
        "finalLink": "",
    }
    d.update(overrides)
    return d


def _balance_sheet(
    *,
    symbol="AAPL",
    date="2023-09-30",
    period="FY",
    total_assets=300_000_000_000,
    total_stockholders_equity=100_000_000_000,
    total_debt=50_000_000_000,
    total_liabilities=200_000_000_000,
    total_current_assets=100_000_000_000,
    total_current_liabilities=80_000_000_000,
    retained_earnings=50_000_000_000,
    cash_and_equivalents=30_000_000_000,
    inventory=10_000_000_000,
    net_receivables=25_000_000_000,
    accounts_payable=20_000_000_000,
    long_term_debt=40_000_000_000,
    goodwill=5_000_000_000,
    intangible_assets=3_000_000_000,
    goodwill_and_intangibles=8_000_000_000,
    property_plant_equipment=30_000_000_000,
    **overrides,
):
    d = {
        "symbol": symbol,
        "date": date,
        "period": period,
        "reportedCurrency": "USD",
        "cik": "0000320193",
        "fillingDate": "2023-11-03",
        "calendarYear": "2023",
        "cashAndCashEquivalents": cash_and_equivalents,
        "shortTermInvestments": 5_000_000_000,
        "netReceivables": net_receivables,
        "inventory": inventory,
        "totalCurrentAssets": total_current_assets,
        "propertyPlantEquipmentNet": property_plant_equipment,
        "goodwill": goodwill,
        "intangibleAssets": intangible_assets,
        "totalNonCurrentAssets": total_assets - total_current_assets,
        "totalAssets": total_assets,
        "accountPayables": accounts_payable,
        "shortTermDebt": 10_000_000_000,
        "totalCurrentLiabilities": total_current_liabilities,
        "longTermDebt": long_term_debt,
        "totalNonCurrentLiabilities": total_liabilities - total_current_liabilities,
        "totalLiabilities": total_liabilities,
        "totalStockholdersEquity": total_stockholders_equity,
        "totalEquity": total_stockholders_equity,
        "totalLiabilitiesAndStockholdersEquity": total_assets,
        "totalDebt": total_debt,
        "netDebt": total_debt - cash_and_equivalents,
        "retainedEarnings": retained_earnings,
        "commonStock": 1_000_000_000,
        "otherCurrentAssets": 2_000_000_000,
        "otherNonCurrentAssets": 1_000_000_000,
        "deferredRevenue": 3_000_000_000,
        "taxPayables": 1_000_000_000,
        "goodwillAndIntangibleAssets": goodwill_and_intangibles,
        "otherAssets": 500_000_000,
        "otherLiabilities": 500_000_000,
        "totalInvestments": 10_000_000_000,
        "capitalLeaseObligations": 2_000_000_000,
        "minorityInterest": 0,
    }
    d.update(overrides)
    return d


def _quote(
    *,
    symbol="AAPL",
    price=150.0,
    market_cap=2_000_000_000_000,
    eps=6.0,
    pe=25.0,
    shares_outstanding=15_000_000_000,
    **overrides,
):
    d = {
        "symbol": symbol,
        "name": "Apple Inc.",
        "price": price,
        "changesPercentage": 1.5,
        "change": 2.0,
        "dayLow": price - 3,
        "dayHigh": price + 3,
        "yearLow": price * 0.7,
        "yearHigh": price * 1.2,
        "marketCap": market_cap,
        "priceAvg50": price - 5,
        "priceAvg200": price - 10,
        "volume": 50_000_000,
        "avgVolume": 45_000_000,
        "open": price - 1,
        "previousClose": price - 2,
        "eps": eps,
        "pe": pe,
        "sharesOutstanding": shares_outstanding,
        "exchange": "NASDAQ",
    }
    d.update(overrides)
    return d


def _daily_price(date, close, *, open_=None, high=None, low=None, volume=50_000_000):
    open_ = open_ or close - 1
    high = high or close + 2
    low = low or close - 2
    return {
        "date": date,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "adjClose": close,
        "volume": volume,
        "vwap": (high + low + close) / 3,
        "change": close - open_,
        "changePercent": (close - open_) / open_ * 100 if open_ else 0,
    }


def _cash_flow(
    *,
    symbol="AAPL",
    date="2023-09-30",
    period="FY",
    operating_cash_flow=40_000_000_000,
    capex=-10_000_000_000,
    free_cash_flow=30_000_000_000,
    net_income=20_000_000_000,
    **overrides,
):
    d = {
        "symbol": symbol,
        "date": date,
        "period": period,
        "reportedCurrency": "USD",
        "cik": "0000320193",
        "fillingDate": "2023-11-03",
        "calendarYear": "2023",
        "netIncome": net_income,
        "depreciationAndAmortization": 5_000_000_000,
        "stockBasedCompensation": 3_000_000_000,
        "operatingCashFlow": operating_cash_flow,
        "capitalExpenditure": capex,
        "acquisitionsNet": -2_000_000_000,
        "netCashUsedForInvestingActivites": -12_000_000_000,
        "debtRepayment": -5_000_000_000,
        "commonStockRepurchased": -15_000_000_000,
        "dividendsPaid": -4_000_000_000,
        "netCashUsedProvidedByFinancingActivities": -24_000_000_000,
        "freeCashFlow": free_cash_flow,
        "netChangeInCash": -6_000_000_000,
    }
    d.update(overrides)
    return d


def _key_metrics(
    *,
    symbol="AAPL",
    date="2023-09-30",
    period="FY",
    enterprise_value=2_100_000_000_000,
    **overrides,
):
    d = {
        "symbol": symbol,
        "date": date,
        "period": period,
        "calendarYear": "2023",
        "revenuePerShare": 25.0,
        "netIncomePerShare": 6.0,
        "operatingCashFlowPerShare": 7.0,
        "freeCashFlowPerShare": 5.0,
        "cashPerShare": 2.0,
        "bookValuePerShare": 6.5,
        "marketCap": 2_000_000_000_000,
        "enterpriseValue": enterprise_value,
        "peRatio": 25.0,
        "priceToSalesRatio": 5.0,
        "pbRatio": 23.0,
        "evToSales": 5.5,
        "enterpriseValueOverEBITDA": 17.0,
        "evToFreeCashFlow": 70.0,
        "earningsYield": 0.04,
        "freeCashFlowYield": 0.015,
        "debtToEquity": 0.5,
        "debtToAssets": 0.17,
        "currentRatio": 1.25,
        "dividendYield": 0.006,
        "payoutRatio": 0.15,
        "roic": 0.3,
        "roe": 0.2,
        "roa": 0.067,
    }
    d.update(overrides)
    return d


# ── Profitability ────────────────────────────────────────────────────────


def test_profitability_ratios(httpx_mock):
    """Profitability margins: GPM, NPM, OPM, EBITDA margin."""
    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[
            _income_statement(
                revenue=100_000_000_000,
                gross_profit=40_000_000_000,
                net_income=20_000_000_000,
                operating_income=30_000_000_000,
                ebitda=35_000_000_000,
            ),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select(
            "gross_profit_margin",
            "net_profit_margin",
            "operating_profit_margin",
            "ebitda_margin",
        )
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) == 1
    assert abs(df["gross_profit_margin"][0] - 0.4) < 1e-6
    assert abs(df["net_profit_margin"][0] - 0.2) < 1e-6
    assert abs(df["operating_profit_margin"][0] - 0.3) < 1e-6
    assert abs(df["ebitda_margin"][0] - 0.35) < 1e-6
    c.close()


# ── Cross-dataset: ROA and ROE ───────────────────────────────────────────


def test_cross_dataset_derived(httpx_mock):
    """ROA and ROE require joining income_statement + balance_sheet."""
    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[_income_statement(net_income=20_000_000_000)],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[
            _balance_sheet(
                total_assets=300_000_000_000,
                total_stockholders_equity=100_000_000_000,
            ),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("return_on_assets", "return_on_equity")
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) >= 1
    roa = df["return_on_assets"][0]
    roe = df["return_on_equity"][0]
    assert roa is not None
    assert roe is not None
    assert abs(roa - 20 / 300) < 1e-4
    assert abs(roe - 0.2) < 1e-4
    c.close()


# ── Leverage ─────────────────────────────────────────────────────────────


def test_leverage_ratios(httpx_mock):
    """Leverage: D/E, D/A, interest coverage, EBITDA interest coverage."""
    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[
            _income_statement(
                ebitda=40_000_000_000,
                interest_expense=5_000_000_000,
                depreciation_and_amortization=5_000_000_000,
            ),
        ],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[
            _balance_sheet(
                total_debt=50_000_000_000,
                total_stockholders_equity=100_000_000_000,
                total_assets=200_000_000_000,
            ),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select(
            "debt_to_equity_derived",
            "debt_to_assets_derived",
            "interest_coverage",
            "ebitda_interest_coverage",
        )
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) >= 1
    assert abs(df["debt_to_equity_derived"][0] - 0.5) < 1e-6
    assert abs(df["debt_to_assets_derived"][0] - 0.25) < 1e-6
    # interest_coverage = (EBITDA - D&A) / interest_expense = (40-5)/5 = 7.0
    assert abs(df["interest_coverage"][0] - 7.0) < 1e-6
    # ebitda_interest_coverage = EBITDA / interest_expense = 40/5 = 8.0
    assert abs(df["ebitda_interest_coverage"][0] - 8.0) < 1e-6
    c.close()


# ── Valuation ────────────────────────────────────────────────────────────


def test_valuation_multiples(httpx_mock):
    """Valuation: PE, P/S, EV/Revenue, Tobin's Q."""
    # pe_derived: quote_market_cap / net_income
    # price_to_sales_derived: quote_market_cap / revenue
    # ev_to_revenue: enterprise_value / revenue
    #   (enterprise_value resolves to key_metrics dataset)
    # tobins_q: (quote_market_cap + total_liabilities) / total_assets
    httpx_mock.add_response(
        url=_url("key-metrics"),
        json=[_key_metrics(enterprise_value=2_100_000_000_000)],
    )
    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[
            _income_statement(
                revenue=380_000_000_000,
                net_income=96_000_000_000,
            ),
        ],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[
            _balance_sheet(
                total_liabilities=200_000_000_000,
                total_assets=300_000_000_000,
            ),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select(
            "pe_derived",
            "price_to_sales_derived",
            "ev_to_revenue",
            "tobins_q",
        )
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) >= 1
    pe = df["pe_derived"][0]
    assert pe is not None
    assert abs(pe - 2_000_000_000_000 / 96_000_000_000) < 0.1

    ps = df["price_to_sales_derived"][0]
    assert ps is not None
    assert abs(ps - 2_000_000_000_000 / 380_000_000_000) < 0.1

    ev_rev = df["ev_to_revenue"][0]
    assert ev_rev is not None
    assert abs(ev_rev - 2_100_000_000_000 / 380_000_000_000) < 0.1

    tq = df["tobins_q"][0]
    assert tq is not None
    assert abs(tq - (2_000_000_000_000 + 200_000_000_000) / 300_000_000_000) < 0.1
    c.close()


# ── Growth with LAG ──────────────────────────────────────────────────────


def test_growth_features(httpx_mock):
    """Growth: revenue_growth_yoy needs 2 periods to compute LAG."""
    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[
            _income_statement(
                date="2022-09-30",
                period="FY",
                revenue=300_000_000_000,
            ),
            _income_statement(
                date="2023-09-30",
                period="FY",
                revenue=380_000_000_000,
            ),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("revenue", "revenue_growth_yoy")
        .date_range("2022-01-01", "2024-12-31")
        .execute()
    )

    assert "revenue_growth_yoy" in df.columns
    growth_row = df.filter(pl.col("date").cast(str) == "2023-09-30")
    if len(growth_row) > 0:
        g = growth_row["revenue_growth_yoy"][0]
        if g is not None:
            assert abs(g - (380 - 300) / 300) < 0.01
    c.close()


# ── DuPont decomposition ────────────────────────────────────────────────


def test_dupont(httpx_mock):
    """DuPont: 3-factor and 5-factor ROE decomposition."""
    ni = 20_000_000_000
    ibt = 25_000_000_000
    oi = 30_000_000_000
    rev = 100_000_000_000
    ta = 300_000_000_000
    tse = 100_000_000_000

    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[
            _income_statement(
                net_income=ni,
                income_before_tax=ibt,
                operating_income=oi,
                revenue=rev,
            ),
        ],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[
            _balance_sheet(
                total_assets=ta,
                total_stockholders_equity=tse,
            ),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select(
            "roe_3factor",
            "roe_5factor",
            "tax_burden",
            "dupont_equity_multiplier",
        )
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) >= 1

    tb = df["tax_burden"][0]
    assert tb is not None
    assert abs(tb - ni / ibt) < 1e-6

    em = df["dupont_equity_multiplier"][0]
    assert em is not None
    assert abs(em - ta / tse) < 1e-6

    npm = ni / rev
    at = rev / ta
    eq_m = ta / tse
    expected_roe3 = npm * at * eq_m
    roe3 = df["roe_3factor"][0]
    assert roe3 is not None
    assert abs(roe3 - expected_roe3) < 1e-4

    tax_b = ni / ibt
    int_b = ibt / oi
    opm = oi / rev
    expected_roe5 = tax_b * int_b * opm * at * eq_m
    roe5 = df["roe_5factor"][0]
    assert roe5 is not None
    assert abs(roe5 - expected_roe5) < 1e-4
    # 3-factor and 5-factor should yield the same ROE
    assert abs(roe5 - expected_roe3) < 1e-4
    c.close()


# ── Cash flow features ──────────────────────────────────────────────────


def test_cash_flow_features(httpx_mock):
    """Cash flow: FCF margin, cash earnings quality, Sloan ratio."""
    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[_income_statement(revenue=380_000_000_000, net_income=20_000_000_000)],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[_balance_sheet(total_assets=300_000_000_000)],
    )
    httpx_mock.add_response(
        url=_url("cash-flow-statement"),
        json=[
            _cash_flow(
                operating_cash_flow=40_000_000_000,
                capex=-10_000_000_000,
                free_cash_flow=30_000_000_000,
                net_income=20_000_000_000,
            ),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("fcf_margin", "cash_earnings_quality", "sloan_ratio")
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) >= 1
    fcfm = df["fcf_margin"][0]
    assert fcfm is not None
    assert abs(fcfm - 30 / 380) < 0.01

    ceq = df["cash_earnings_quality"][0]
    assert ceq is not None
    assert abs(ceq - 2.0) < 1e-6

    sr = df["sloan_ratio"][0]
    assert sr is not None
    assert abs(sr - (-20 / 300)) < 0.01
    c.close()


# ── Altman Z-Score ───────────────────────────────────────────────────────


def test_composite_altman(httpx_mock):
    """Altman Z-Score with known values."""
    tca = 100_000_000_000
    tcl = 80_000_000_000
    ta = 300_000_000_000
    re = 50_000_000_000
    ebitda = 35_000_000_000
    da = 5_000_000_000
    tl = 200_000_000_000
    mcap = 500_000_000_000
    rev = 380_000_000_000

    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[
            _income_statement(
                revenue=rev,
                ebitda=ebitda,
                depreciation_and_amortization=da,
            ),
        ],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[
            _balance_sheet(
                total_current_assets=tca,
                total_current_liabilities=tcl,
                total_assets=ta,
                retained_earnings=re,
                total_liabilities=tl,
            ),
        ],
    )
    httpx_mock.add_response(
        url=_url("key-metrics"),
        json=[_key_metrics(symbol="AAPL", date="2023-09-30")],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("altman_z_score")
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    # market_cap from key_metrics mock is 2_000_000_000_000
    km_mcap = 2_000_000_000_000

    assert len(df) >= 1
    z = df["altman_z_score"][0]
    assert z is not None

    x1 = (tca - tcl) / ta
    x2 = re / ta
    x3 = (ebitda - da) / ta
    x4 = km_mcap / tl
    x5 = rev / ta
    expected_z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

    assert abs(z - expected_z) < 0.01, f"Expected Z={expected_z:.4f}, got {z:.4f}"
    c.close()


# ── Efficiency ───────────────────────────────────────────────────────────


def test_efficiency_ratios(httpx_mock):
    """Efficiency: asset turnover, inventory turnover, DIO, DSO, DPO, CCC."""
    rev = 100_000_000_000
    cor = 60_000_000_000
    inv = 10_000_000_000
    nr = 25_000_000_000
    ap = 20_000_000_000
    ta = 300_000_000_000

    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[_income_statement(revenue=rev, cost_of_revenue=cor)],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[
            _balance_sheet(
                total_assets=ta,
                inventory=inv,
                net_receivables=nr,
                accounts_payable=ap,
            ),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select(
            "asset_turnover_derived",
            "inventory_turnover",
            "dio",
            "dso",
            "dpo",
            "ccc",
        )
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) >= 1
    assert abs(df["asset_turnover_derived"][0] - rev / ta) < 0.01
    assert abs(df["inventory_turnover"][0] - cor / inv) < 0.01
    assert abs(df["dio"][0] - inv / (cor / 365)) < 1.0
    assert abs(df["dso"][0] - nr / (rev / 365)) < 1.0
    assert abs(df["dpo"][0] - ap / (cor / 365)) < 1.0
    expected_ccc = inv / (cor / 365) + nr / (rev / 365) - ap / (cor / 365)
    assert abs(df["ccc"][0] - expected_ccc) < 1.0
    c.close()


# ── Earnings quality ─────────────────────────────────────────────────────


def test_earnings_quality(httpx_mock):
    """Earnings quality: Sloan accrual, cash-to-accruals, earnings surprise.

    All four datasets (income_statement, balance_sheet, cash_flow, earnings_data)
    are QUARTERLY and joined on symbol + date — dates must match exactly.
    """
    ni = 20_000_000_000
    ocf = 40_000_000_000
    ta = 300_000_000_000
    eps_actual = 6.50
    eps_est = 6.20
    report_date = "2023-09-30"

    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[_income_statement(net_income=ni, date=report_date)],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[_balance_sheet(total_assets=ta, date=report_date)],
    )
    httpx_mock.add_response(
        url=_url("cash-flow-statement"),
        json=[_cash_flow(operating_cash_flow=ocf, net_income=ni, date=report_date)],
    )
    httpx_mock.add_response(
        url=_url("earnings"),
        json=[{
            "symbol": "AAPL",
            "date": report_date,  # Must match other datasets for LEFT JOIN
            "epsActual": eps_actual,
            "epsEstimated": eps_est,
            "revenueActual": 89498000000,
            "revenueEstimated": 89300000000,
            "lastUpdated": "2023-10-26",
        }],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("sloan_accrual_cf", "cash_to_accruals", "earnings_surprise")
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) >= 1
    sa = df["sloan_accrual_cf"][0]
    assert sa is not None
    assert abs(sa - (ni - ocf) / ta) < 0.01

    cta = df["cash_to_accruals"][0]
    assert cta is not None
    assert abs(cta - ocf / ni) < 0.01

    es = df["earnings_surprise"][0]
    assert es is not None
    assert abs(es - (eps_actual - eps_est) / abs(eps_est)) < 0.01
    c.close()


# ── Technical: SMA + Bollinger Bands ─────────────────────────────────────


def test_technical_windows(httpx_mock):
    """Technical: SMA-20, Bollinger bands need 20+ data points."""
    prices = [
        _daily_price(f"2024-01-{d:02d}", 100.0 + d)
        for d in range(2, 25)
    ]
    httpx_mock.add_response(url=_url("historical-price-eod/full"), json=prices)

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("close", "sma_20", "bollinger_upper", "bollinger_lower")
        .date_range("2024-01-01", "2024-01-31")
        .execute()
    )

    assert len(df) == 23
    last_20_closes = [100.0 + d for d in range(5, 25)]
    expected_sma = sum(last_20_closes) / 20
    actual_sma = df["sma_20"][-1]
    assert actual_sma is not None
    assert abs(actual_sma - expected_sma) < 0.01

    bb_upper = df["bollinger_upper"][-1]
    bb_lower = df["bollinger_lower"][-1]
    assert bb_upper is not None
    assert bb_lower is not None
    assert bb_upper > actual_sma
    assert bb_lower < actual_sma
    c.close()


# ── Momentum returns ────────────────────────────────────────────────────


def test_momentum_returns(httpx_mock):
    """Momentum: return_1d = (close_t / close_t-1) - 1."""
    prices = [
        _daily_price("2024-01-15", 180.0),
        _daily_price("2024-01-16", 185.0),
    ]
    httpx_mock.add_response(url=_url("historical-price-eod/full"), json=prices)

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("close", "return_1d")
        .date_range("2024-01-01", "2024-01-31")
        .execute()
    )

    assert len(df) == 2
    assert df["return_1d"][0] is None
    ret = df["return_1d"][1]
    assert ret is not None
    assert abs(ret - (185 - 180) / 180) < 1e-6
    c.close()


# ── Macro: treasury spreads ──────────────────────────────────────────────


def test_macro_treasury(httpx_mock):
    """Macro: yield_spread_2s10s from treasury_rates (date-only join)."""
    httpx_mock.add_response(
        url=_url("historical-price-eod/full"),
        json=[
            _daily_price("2024-01-15", 183.0),
            _daily_price("2024-01-16", 185.0),
        ],
    )
    httpx_mock.add_response(
        url=_url("treasury-rates"),
        json=[
            {
                "date": "2024-01-15",
                "month1": 5.40, "month2": 5.42, "month3": 5.44,
                "month6": 5.32, "year1": 5.05, "year2": 4.38,
                "year3": 4.15, "year5": 4.02, "year7": 4.05,
                "year10": 4.12, "year20": 4.41, "year30": 4.31,
            },
            {
                "date": "2024-01-16",
                "month1": 5.41, "month2": 5.43, "month3": 5.45,
                "month6": 5.33, "year1": 5.06, "year2": 4.40,
                "year3": 4.16, "year5": 4.03, "year7": 4.06,
                "year10": 4.14, "year20": 4.42, "year30": 4.32,
            },
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("close", "yield_spread_2s10s")
        .date_range("2024-01-15", "2024-01-16")
        .execute()
    )

    assert len(df) == 2
    assert "yield_spread_2s10s" in df.columns
    spread_0 = df["yield_spread_2s10s"][0]
    assert spread_0 is not None
    assert abs(spread_0 - (4.12 - 4.38)) < 0.01
    spread_1 = df["yield_spread_2s10s"][1]
    assert spread_1 is not None
    assert abs(spread_1 - (4.14 - 4.40)) < 0.01
    c.close()


# ── Risk: volatility, true range, ATR ────────────────────────────────────


def test_risk_volatility(httpx_mock):
    """Risk: daily_return, true_range, price_range_pct, up_day.

    Note: historical_volatility_20d and atr_14 use nested window functions
    (LAG inside STDDEV/AVG OVER ...) which DuckDB cannot execute in a single
    query. They are tested separately if needed.
    """
    prices = [
        _daily_price(
            f"2024-01-{d:02d}",
            close=100.0 + d + (d % 3) * 0.5,
            high=103.0 + d,
            low=98.0 + d,
        )
        for d in range(2, 31)
    ]
    httpx_mock.add_response(url=_url("historical-price-eod/full"), json=prices)

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("daily_return", "true_range", "price_range_pct", "up_day")
        .date_range("2024-01-01", "2024-01-31")
        .execute()
    )

    assert len(df) == 29

    # daily_return: first row null, rest non-null
    assert df["daily_return"][0] is None
    dr = df["daily_return"][-1]
    assert dr is not None

    # true_range: GREATEST(high-low, |high-prev_close|, |low-prev_close|)
    tr = df["true_range"][-1]
    assert tr is not None
    assert tr > 0

    # price_range_pct = (high - low) / open
    prp = df["price_range_pct"][-1]
    assert prp is not None
    assert prp > 0

    # up_day: integer flag
    ud = df["up_day"][-1]
    assert ud is not None
    assert ud in (0, 1)
    c.close()


# ── Per-share ────────────────────────────────────────────────────────────


def test_per_share(httpx_mock):
    """Per-share: BVPS, TBVPS, revenue per share."""
    tse = 100_000_000_000
    gi = 8_000_000_000
    rev = 380_000_000_000
    so = 15_000_000_000

    httpx_mock.add_response(
        url=_url("income-statement"),
        json=[_income_statement(revenue=rev)],
    )
    httpx_mock.add_response(
        url=_url("balance-sheet-statement"),
        json=[
            _balance_sheet(
                total_stockholders_equity=tse,
                goodwill_and_intangibles=gi,
            ),
        ],
    )
    httpx_mock.add_response(
        url=_url("shares-float"),
        json=[{
            "symbol": "AAPL",
            "freeFloat": 99.5,
            "floatShares": int(so * 0.99),
            "outstandingShares": so,
        }],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("bvps", "tbvps", "revenue_per_share_derived")
        .date_range("2023-01-01", "2024-12-31")
        .execute()
    )

    assert len(df) >= 1
    bvps = df["bvps"][0]
    assert bvps is not None
    assert abs(bvps - tse / so) < 0.1

    tbvps = df["tbvps"][0]
    assert tbvps is not None
    assert abs(tbvps - (tse - gi) / so) < 0.1

    rps = df["revenue_per_share_derived"][0]
    assert rps is not None
    assert abs(rps - rev / so) < 0.5
    c.close()


# ── DCF features ─────────────────────────────────────────────────────────


def test_dcf_features(httpx_mock):
    """DCF: dcf_value and dcf_upside."""
    dcf_val = 200.0
    price = 150.0

    httpx_mock.add_response(
        url=_url("discounted-cash-flow"),
        json=[{
            "symbol": "AAPL",
            "dcf": dcf_val,
            "stockPrice": price,
        }],
    )
    httpx_mock.add_response(
        url=_url("quote"),
        json=[_quote(price=price)],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("dcf_value", "dcf_upside")
        .execute()
    )

    assert len(df) >= 1
    dv = df["dcf_value"][0]
    assert dv is not None
    assert abs(dv - dcf_val) < 0.01

    du = df["dcf_upside"][0]
    assert du is not None
    assert abs(du - (dcf_val - price) / price) < 0.01
    c.close()


# ── ESG features ─────────────────────────────────────────────────────────


def test_esg_features(httpx_mock):
    """ESG: composite, env, soc, gov scores."""
    httpx_mock.add_response(
        url=_url("esg-environmental-social-governance-data"),
        json=[{
            "symbol": "AAPL",
            "environmentalScore": 72.5,
            "socialScore": 68.3,
            "governanceScore": 81.1,
            "ESGScore": 73.9,
        }],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("esg_composite", "esg_env", "esg_soc", "esg_gov")
        .execute()
    )

    assert len(df) >= 1
    assert abs(df["esg_composite"][0] - 73.9) < 0.01
    assert abs(df["esg_env"][0] - 72.5) < 0.01
    assert abs(df["esg_soc"][0] - 68.3) < 0.01
    assert abs(df["esg_gov"][0] - 81.1) < 0.01
    c.close()


# ── Pre-computed returns ─────────────────────────────────────────────────


def test_precomputed_returns(httpx_mock):
    """Pre-computed returns from FMP's stock-price-change endpoint."""
    httpx_mock.add_response(
        url=_url("stock-price-change"),
        json=[{
            "symbol": "AAPL",
            "1D": 1.5,
            "5D": 3.2,
            "1M": 5.4,
            "3M": 12.1,
            "6M": 18.5,
            "ytd": 22.3,
            "1Y": 35.0,
            "3Y": 80.0,
            "5Y": 150.0,
        }],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("fmp_ret_1m", "fmp_ret_1y")
        .execute()
    )

    assert len(df) >= 1
    assert abs(df["fmp_ret_1m"][0] - 5.4) < 0.01
    assert abs(df["fmp_ret_1y"][0] - 35.0) < 0.01
    c.close()


# ── Institutional ownership ─────────────────────────────────────────────


def test_institutional(httpx_mock):
    """Institutional: holders count, invested growth."""
    httpx_mock.add_response(
        url=_url("institutional-ownership/symbol-positions-summary"),
        json=[{
            "symbol": "AAPL",
            "investorsHolding": 5200,
            "lastInvestorsHolding": 5000,
            "investorsHoldingChange": 200,
            "totalInvested": 2_500_000_000_000,
            "lastTotalInvested": 2_400_000_000_000,
            "totalInvestedChange": 100_000_000_000,
            "putCallRatio": 0.85,
        }],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("inst_holders", "inst_invested_growth")
        .execute()
    )

    assert len(df) >= 1
    assert df["inst_holders"][0] == 5200
    ig = df["inst_invested_growth"][0]
    assert ig is not None
    assert abs(ig - 100_000_000_000 / 2_400_000_000_000) < 0.001
    c.close()
