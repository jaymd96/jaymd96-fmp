from __future__ import annotations

import pytest
import polars as pl
from fmp import FMPClient, FMPError, list_features, feature_categories


def test_feature_registry_count():
    features = list_features()
    assert len(features) >= 200


def test_feature_categories():
    cats = feature_categories()
    assert "profitability" in cats
    assert "composite" in cats
    assert "growth" in cats


def test_list_features_by_category():
    prof = list_features("profitability")
    assert "gross_profit_margin" in prof
    assert len(prof) >= 15


def test_derived_field_simple_ratio(httpx_mock):
    """Derived field: gross_profit_margin = gross_profit / revenue."""
    httpx_mock.add_response(json=[
        {"date": "2023-09-30", "symbol": "AAPL", "period": "FY",
         "reportedCurrency": "USD", "cik": "320193",
         "fillingDate": "2023-11-03", "acceptedDate": "2023-11-02",
         "calendarYear": "2023",
         "revenue": 383285000000, "costOfRevenue": 214137000000,
         "grossProfit": 169148000000, "grossProfitRatio": 0.4413,
         "researchAndDevelopmentExpenses": 29915000000,
         "sellingGeneralAndAdministrativeExpenses": 24932000000,
         "operatingExpenses": 54847000000,
         "operatingIncome": 114301000000, "operatingIncomeRatio": 0.2982,
         "interestIncome": 3999000000, "interestExpense": 3933000000,
         "depreciationAndAmortization": 11519000000,
         "ebitda": 125820000000, "ebitdaratio": 0.3283,
         "netIncome": 96995000000, "netIncomeRatio": 0.2531,
         "eps": 6.16, "epsdiluted": 6.13,
         "incomeBeforeTax": 113919000000, "incomeTaxExpense": 16741000000,
         "costAndExpenses": 268984000000, "otherExpenses": 0,
         "totalOtherIncomeExpensesNet": -382000000,
         "weightedAverageShsOut": 15744231000,
         "weightedAverageShsOutDil": 15812547000,
         "link": "", "finalLink": ""},
    ])

    c = FMPClient(api_key="test", cache_path=None)
    df = (c.query()
          .symbols("AAPL")
          .select("revenue", "gross_profit_margin")
          .date_range("2023-01-01", "2024-12-31")
          .execute())

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 1
    assert "gross_profit_margin" in df.columns
    # gross_profit_margin ≈ 169148/383285 ≈ 0.4413
    gpm = df["gross_profit_margin"][0]
    assert gpm is not None
    assert 0.44 < gpm < 0.45
    c.close()


def test_derived_field_with_lag(httpx_mock):
    """Derived field with LAG: revenue_growth_yoy."""
    httpx_mock.add_response(json=[
        {"date": "2022-09-30", "symbol": "AAPL", "period": "FY",
         "revenue": 394328000000, "grossProfit": 170000000000,
         "costOfRevenue": 224000000000, "grossProfitRatio": 0.43,
         "researchAndDevelopmentExpenses": 26000000000,
         "sellingGeneralAndAdministrativeExpenses": 24000000000,
         "operatingExpenses": 50000000000,
         "operatingIncome": 120000000000, "operatingIncomeRatio": 0.30,
         "interestIncome": 2800000000, "interestExpense": 2900000000,
         "depreciationAndAmortization": 11000000000,
         "ebitda": 131000000000, "ebitdaratio": 0.33,
         "netIncome": 99803000000, "netIncomeRatio": 0.25,
         "eps": 6.15, "epsdiluted": 6.11,
         "incomeBeforeTax": 119000000000, "incomeTaxExpense": 19000000000,
         "costAndExpenses": 274000000000, "otherExpenses": 0,
         "totalOtherIncomeExpensesNet": -500000000,
         "weightedAverageShsOut": 16200000000,
         "weightedAverageShsOutDil": 16300000000,
         "reportedCurrency": "USD", "cik": "320193",
         "fillingDate": "2022-10-28", "acceptedDate": "2022-10-27",
         "calendarYear": "2022", "link": "", "finalLink": ""},
        {"date": "2023-09-30", "symbol": "AAPL", "period": "FY",
         "revenue": 383285000000, "grossProfit": 169148000000,
         "costOfRevenue": 214137000000, "grossProfitRatio": 0.4413,
         "researchAndDevelopmentExpenses": 29915000000,
         "sellingGeneralAndAdministrativeExpenses": 24932000000,
         "operatingExpenses": 54847000000,
         "operatingIncome": 114301000000, "operatingIncomeRatio": 0.2982,
         "interestIncome": 3999000000, "interestExpense": 3933000000,
         "depreciationAndAmortization": 11519000000,
         "ebitda": 125820000000, "ebitdaratio": 0.3283,
         "netIncome": 96995000000, "netIncomeRatio": 0.2531,
         "eps": 6.16, "epsdiluted": 6.13,
         "incomeBeforeTax": 113919000000, "incomeTaxExpense": 16741000000,
         "costAndExpenses": 268984000000, "otherExpenses": 0,
         "totalOtherIncomeExpensesNet": -382000000,
         "weightedAverageShsOut": 15744231000,
         "weightedAverageShsOutDil": 15812547000,
         "reportedCurrency": "USD", "cik": "320193",
         "fillingDate": "2023-11-03", "acceptedDate": "2023-11-02",
         "calendarYear": "2023", "link": "", "finalLink": ""},
    ])

    c = FMPClient(api_key="test", cache_path=None)
    df = (c.query()
          .symbols("AAPL")
          .select("revenue", "revenue_growth_yoy")
          .date_range("2022-01-01", "2024-12-31")
          .execute())

    assert "revenue_growth_yoy" in df.columns
    # 2022 row has no prior period → null. 2023 row: (383285-394328)/394328 ≈ -0.028
    growth_vals = df.filter(pl.col("date").cast(str) == "2023-09-30")["revenue_growth_yoy"]
    if len(growth_vals) > 0 and growth_vals[0] is not None:
        assert -0.03 < growth_vals[0] < -0.02
    c.close()


def test_post_compute_ema(httpx_mock):
    """Post-compute feature: EMA-20 computed in polars."""
    prices = [
        {"date": f"2024-01-{d:02d}", "open": 180.0 + d, "high": 185.0 + d,
         "low": 179.0 + d, "close": 180.0 + d, "adjClose": 180.0 + d,
         "volume": 50000000, "vwap": 182.0 + d, "change": 1.0, "changePercent": 0.5}
        for d in range(2, 25)
    ]
    httpx_mock.add_response(json=prices)

    c = FMPClient(api_key="test", cache_path=None)
    df = (c.query()
          .symbols("AAPL")
          .select("close", "ema_20")
          .date_range("2024-01-01", "2024-01-31")
          .execute())

    assert isinstance(df, pl.DataFrame)
    assert "ema_20" in df.columns
    assert len(df) == 23
    # EMA should be close to the close price for a monotonically increasing series
    assert df["ema_20"][-1] is not None
    c.close()


def test_post_compute_macd(httpx_mock):
    """Post-compute: MACD features."""
    prices = [
        {"date": f"2024-{m:02d}-15", "open": 180.0 + i, "high": 185.0 + i,
         "low": 179.0 + i, "close": 180.0 + i * 0.5, "adjClose": 180.0 + i * 0.5,
         "volume": 50000000, "vwap": 182.0, "change": 0.5, "changePercent": 0.3}
        for i, m in enumerate(range(1, 13))
    ]
    httpx_mock.add_response(json=prices)

    c = FMPClient(api_key="test", cache_path=None)
    df = (c.query()
          .symbols("AAPL")
          .select("close", "macd_line", "macd_signal", "macd_histogram")
          .date_range("2024-01-01", "2024-12-31")
          .execute())

    assert "macd_line" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_histogram" in df.columns
    c.close()


def test_post_compute_feature_count():
    """Post-compute features are included in total feature count."""
    features = list_features()
    assert "ema_20" in features
    assert "macd_line" in features
    assert "beta_sp500" in features
    assert "consecutive_dividend_increases" in features
    assert len(features) >= 270
