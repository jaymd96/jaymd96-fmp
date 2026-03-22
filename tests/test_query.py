from __future__ import annotations

import duckdb
import pytest
import polars as pl

from fmp import FMPClient, FMPError
from fmp._store import BitemporalStore
from fmp._query import QueryBuilder


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def query_client(httpx_mock):
    """FMPClient with in-memory cache for query builder tests."""
    c = FMPClient(api_key="test-key", cache_path=None)
    yield c
    c.close()


# ── Validation tests ─────────────────────────────────────────────────

def test_no_symbols_raises(query_client):
    with pytest.raises(FMPError, match="No symbols"):
        query_client.query().select("close").date_range("2024-01-01", "2024-12-31").execute()


def test_no_fields_raises(query_client):
    with pytest.raises(FMPError, match="No fields"):
        query_client.query().symbols("AAPL").date_range("2024-01-01", "2024-12-31").execute()


def test_unknown_field_raises(query_client):
    with pytest.raises(FMPError, match="Unknown field"):
        (query_client.query()
         .symbols("AAPL")
         .select("close", "nonexistent_field_xyz")
         .date_range("2024-01-01", "2024-12-31")
         .execute())


# ── Single-dataset queries ───────────────────────────────────────────

def test_single_dataset_daily(query_client, httpx_mock):
    """Query a single daily dataset."""
    httpx_mock.add_response(json=[
        {"date": "2024-01-15", "open": 180.0, "high": 185.0, "low": 179.0,
         "close": 183.0, "adjClose": 183.0, "volume": 50000000,
         "vwap": 182.0, "change": 3.0, "changePercent": 1.5},
        {"date": "2024-01-16", "open": 183.0, "high": 186.0, "low": 182.0,
         "close": 185.0, "adjClose": 185.0, "volume": 48000000,
         "vwap": 184.0, "change": 2.0, "changePercent": 1.1},
    ])

    df = (query_client.query()
          .symbols("AAPL")
          .select("close", "volume")
          .date_range("2024-01-01", "2024-12-31")
          .execute())

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 2
    assert "close" in df.columns
    assert "volume" in df.columns
    assert "symbol" in df.columns


def test_single_dataset_snapshot(query_client, httpx_mock):
    """Query a snapshot dataset."""
    httpx_mock.add_response(json=[
        {"symbol": "AAPL", "name": "Apple", "price": 182.52,
         "changesPercentage": 1.29, "change": 2.33, "dayLow": 179.0,
         "dayHigh": 183.0, "yearLow": 124.0, "yearHigh": 199.0,
         "marketCap": 2890000000000, "priceAvg50": 178.0, "priceAvg200": 170.0,
         "volume": 54000000, "avgVolume": 48000000, "open": 180.0,
         "previousClose": 180.0, "eps": 6.57, "pe": 27.78,
         "sharesOutstanding": 15800000000, "exchange": "NASDAQ"},
    ])

    df = (query_client.query()
          .symbols("AAPL")
          .select("price", "day_high")
          .execute())

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 1
    assert df["price"][0] == 182.52
    assert df["day_high"][0] == 183.0


# ── Cross-dataset queries ────────────────────────────────────────────

def test_cross_dataset_daily_periodic(query_client, httpx_mock):
    """Query daily prices + quarterly financials → ASOF join."""
    # daily_price response
    httpx_mock.add_response(json=[
        {"date": "2024-01-15", "open": 180.0, "high": 185.0, "low": 179.0,
         "close": 183.0, "adjClose": 183.0, "volume": 50000000,
         "vwap": 182.0, "change": 3.0, "changePercent": 1.5},
        {"date": "2024-01-16", "open": 183.0, "high": 186.0, "low": 182.0,
         "close": 185.0, "adjClose": 185.0, "volume": 48000000,
         "vwap": 184.0, "change": 2.0, "changePercent": 1.1},
    ])
    # income_statement response
    httpx_mock.add_response(json=[
        {"date": "2023-09-30", "symbol": "AAPL", "period": "FY",
         "reportedCurrency": "USD", "cik": "0000320193",
         "fillingDate": "2023-11-03", "acceptedDate": "2023-11-02",
         "calendarYear": "2023", "revenue": 383285000000,
         "costOfRevenue": 214137000000, "grossProfit": 169148000000,
         "grossProfitRatio": 0.4413,
         "researchAndDevelopmentExpenses": 29915000000,
         "sellingGeneralAndAdministrativeExpenses": 24932000000,
         "operatingExpenses": 54847000000,
         "operatingIncome": 114301000000, "operatingIncomeRatio": 0.2982,
         "interestIncome": 3999000000, "interestExpense": 3933000000,
         "ebitda": 125820000000, "ebitdaratio": 0.3283,
         "netIncome": 96995000000, "netIncomeRatio": 0.2531,
         "eps": 6.16, "epsdiluted": 6.13,
         "weightedAverageShsOut": 15744231000,
         "weightedAverageShsOutDil": 15812547000,
         "link": "", "finalLink": ""},
    ])

    df = (query_client.query()
          .symbols("AAPL")
          .select("close", "revenue")
          .date_range("2024-01-01", "2024-12-31")
          .execute())

    assert isinstance(df, pl.DataFrame)
    assert "close" in df.columns
    assert "revenue" in df.columns
    # Should have 2 rows (daily granularity is the anchor)
    assert len(df) == 2
    # Revenue should be ASOF-joined (carried forward from 2023-09-30)
    assert df["revenue"][0] == 383285000000


def test_grain_override_quarterly(query_client, httpx_mock):
    """Query with explicit quarterly grain → daily prices rolled up."""
    # daily_price
    httpx_mock.add_response(json=[
        {"date": "2024-01-15", "open": 180.0, "high": 185.0, "low": 179.0,
         "close": 183.0, "adjClose": 183.0, "volume": 50000000,
         "vwap": 182.0, "change": 3.0, "changePercent": 1.5},
        {"date": "2024-01-16", "open": 183.0, "high": 186.0, "low": 182.0,
         "close": 185.0, "adjClose": 185.0, "volume": 48000000,
         "vwap": 184.0, "change": 2.0, "changePercent": 1.1},
    ])
    # income_statement
    httpx_mock.add_response(json=[
        {"date": "2023-12-31", "symbol": "AAPL", "period": "Q1",
         "reportedCurrency": "USD", "cik": "320193", "fillingDate": "2024-02-01",
         "acceptedDate": "2024-02-01", "calendarYear": "2024",
         "revenue": 119580000000, "costOfRevenue": 64000000000,
         "grossProfit": 55580000000, "grossProfitRatio": 0.46,
         "researchAndDevelopmentExpenses": 7500000000,
         "sellingGeneralAndAdministrativeExpenses": 6500000000,
         "operatingExpenses": 14000000000, "operatingIncome": 41580000000,
         "operatingIncomeRatio": 0.35, "interestIncome": 1000000000,
         "interestExpense": 900000000, "ebitda": 45000000000,
         "ebitdaratio": 0.376, "netIncome": 33916000000,
         "netIncomeRatio": 0.284, "eps": 2.18, "epsdiluted": 2.18,
         "weightedAverageShsOut": 15560000000,
         "weightedAverageShsOutDil": 15600000000,
         "link": "", "finalLink": ""},
    ])

    df = (query_client.query()
          .symbols("AAPL")
          .select("close", "volume", "revenue")
          .date_range("2024-01-01", "2024-03-31")
          .grain("quarterly")
          .execute())

    assert isinstance(df, pl.DataFrame)
    # Rolled up to 1 quarter
    assert len(df) == 1
    # Volume should be summed (ontology default for volume is sum)
    assert df["volume"][0] == 98000000  # 50M + 48M


# ── Backend test ──────────────────────────────────────────────────────

def test_pandas_backend(query_client, httpx_mock):
    """execute(backend='pandas') returns a pandas DataFrame."""
    import pandas as pd
    httpx_mock.add_response(json=[
        {"date": "2024-01-15", "open": 180.0, "high": 185.0, "low": 179.0,
         "close": 183.0, "adjClose": 183.0, "volume": 50000000,
         "vwap": 182.0, "change": 3.0, "changePercent": 1.5},
    ])

    df = (query_client.query()
          .symbols("AAPL")
          .select("close")
          .date_range("2024-01-01", "2024-12-31")
          .execute(backend="pandas"))

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1


# ── Caching / force_refresh ──────────────────────────────────────────

def test_cached_data_not_refetched(query_client, httpx_mock):
    """Second query uses cached data, no new HTTP calls."""
    httpx_mock.add_response(json=[
        {"date": "2024-01-15", "open": 180.0, "high": 185.0, "low": 179.0,
         "close": 183.0, "adjClose": 183.0, "volume": 50000000,
         "vwap": 182.0, "change": 3.0, "changePercent": 1.5},
    ])

    query_client.query().symbols("AAPL").select("close").date_range("2024-01-01", "2024-12-31").execute()

    # Second query — should not make another HTTP call
    df2 = query_client.query().symbols("AAPL").select("close").date_range("2024-01-01", "2024-12-31").execute()
    assert len(httpx_mock.get_requests()) == 1
    assert len(df2) == 1


def test_force_refresh_refetches(query_client, httpx_mock):
    """force_refresh bypasses cache."""
    httpx_mock.add_response(json=[
        {"date": "2024-01-15", "close": 183.0, "open": 180.0, "high": 185.0,
         "low": 179.0, "adjClose": 183.0, "volume": 50000000,
         "vwap": 182.0, "change": 3.0, "changePercent": 1.5},
    ])
    httpx_mock.add_response(json=[
        {"date": "2024-01-15", "close": 190.0, "open": 188.0, "high": 191.0,
         "low": 187.0, "adjClose": 190.0, "volume": 55000000,
         "vwap": 189.0, "change": 7.0, "changePercent": 3.5},
    ])

    query_client.query().symbols("AAPL").select("close").date_range("2024-01-01", "2024-12-31").execute()
    df2 = (query_client.query()
           .symbols("AAPL").select("close").date_range("2024-01-01", "2024-12-31")
           .force_refresh().execute())

    assert len(httpx_mock.get_requests()) == 2
    # Latest version should be returned
    assert df2["close"][0] == 190.0
