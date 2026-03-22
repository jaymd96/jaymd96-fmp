"""Tests for the sync system and store-first architecture."""

from __future__ import annotations

import re
import pytest
import polars as pl
from fmp import FMPClient


# ── Helpers ──────────────────────────────────────────────────────────

def _income_row(symbol="AAPL", year="2023", revenue=383285000000):
    return {
        "date": f"{year}-09-30", "symbol": symbol, "period": "FY",
        "reportedCurrency": "USD", "cik": "320193",
        "fillingDate": f"{year}-11-03", "acceptedDate": f"{year}-11-02",
        "calendarYear": year, "revenue": revenue,
        "costOfRevenue": int(revenue * 0.56), "grossProfit": int(revenue * 0.44),
        "grossProfitRatio": 0.44,
        "researchAndDevelopmentExpenses": 30000000000,
        "sellingGeneralAndAdministrativeExpenses": 25000000000,
        "operatingExpenses": 55000000000,
        "operatingIncome": int(revenue * 0.30), "operatingIncomeRatio": 0.30,
        "interestIncome": 4000000000, "interestExpense": 4000000000,
        "depreciationAndAmortization": 12000000000,
        "ebitda": int(revenue * 0.33), "ebitdaratio": 0.33,
        "netIncome": int(revenue * 0.25), "netIncomeRatio": 0.25,
        "eps": 6.16, "epsdiluted": 6.13,
        "incomeBeforeTax": int(revenue * 0.30),
        "incomeTaxExpense": int(revenue * 0.05),
        "costAndExpenses": int(revenue * 0.70),
        "otherExpenses": 0, "totalOtherIncomeExpensesNet": 0,
        "weightedAverageShsOut": 15744000000,
        "weightedAverageShsOutDil": 15813000000,
        "link": "", "finalLink": "",
    }


def _price_row(date="2024-01-15", close=183.0):
    return {
        "date": date, "open": close - 3, "high": close + 2,
        "low": close - 4, "close": close, "adjClose": close,
        "volume": 50000000, "vwap": close - 1,
        "change": 1.0, "changePercent": 0.5,
    }


# ── Sync tests ───────────────────────────────────────────────────────

def test_sync_per_symbol(httpx_mock):
    """sync() fetches and stores per-symbol data."""
    httpx_mock.add_response(
        url=re.compile(r".*/historical-price-eod/full.*symbol=AAPL"),
        json=[_price_row("2024-01-15", 183.0), _price_row("2024-01-16", 185.0)],
    )

    c = FMPClient(api_key="test", cache_path=None)
    result = c.sync(
        symbols=["AAPL"],
        datasets=["daily_price"],
        start="2024-01-01", end="2024-12-31",
    )

    assert result["daily_price"] == 2
    # Data is in the store
    assert c.store.has_data("daily_price", "AAPL")
    c.close()


def test_sync_then_query_without_api(httpx_mock):
    """After sync, query with auto_fetch=False reads from store only."""
    httpx_mock.add_response(
        url=re.compile(r".*/historical-price-eod/full.*"),
        json=[_price_row("2024-01-15", 183.0)],
    )

    c = FMPClient(api_key="test", cache_path=None)
    c.sync(
        symbols=["AAPL"],
        datasets=["daily_price"],
        start="2024-01-01", end="2024-12-31",
    )

    # Now query — should NOT make any API calls
    initial_requests = len(httpx_mock.get_requests())
    df = (c.query()
          .symbols("AAPL")
          .select("close")
          .date_range("2024-01-01", "2024-12-31")
          .auto_fetch(False)
          .execute())

    assert len(df) == 1
    assert df["close"][0] == 183.0
    # No new API calls were made
    assert len(httpx_mock.get_requests()) == initial_requests
    c.close()


def test_sync_skips_existing_data(httpx_mock):
    """sync() doesn't re-fetch data that already exists in the store."""
    httpx_mock.add_response(
        url=re.compile(r".*/historical-price-eod/full.*"),
        json=[_price_row("2024-01-15", 183.0)],
    )

    c = FMPClient(api_key="test", cache_path=None)

    # First sync
    c.sync(symbols=["AAPL"], datasets=["daily_price"],
           start="2024-01-01", end="2024-12-31")
    first_call_count = len(httpx_mock.get_requests())

    # Second sync — should skip because data exists
    c.sync(symbols=["AAPL"], datasets=["daily_price"],
           start="2024-01-01", end="2024-12-31")
    assert len(httpx_mock.get_requests()) == first_call_count  # no new calls
    c.close()


def test_sync_bulk_financial_statements(httpx_mock):
    """sync() uses bulk endpoint for financial statements."""
    bulk_data = [
        _income_row("AAPL", "2023", 383000000000),
        _income_row("MSFT", "2023", 212000000000),
        _income_row("GOOG", "2023", 307000000000),
    ]
    httpx_mock.add_response(
        url=re.compile(r".*/income-statement-bulk.*year=2023"),
        json=bulk_data,
    )

    c = FMPClient(api_key="test", cache_path=None)
    result = c.sync(
        datasets=["income_statement"],
        start="2023-01-01", end="2023-12-31",
        use_bulk=True,
    )

    assert result["income_statement"] == 3  # all 3 symbols in one call
    assert c.store.has_data("income_statement", "AAPL")
    assert c.store.has_data("income_statement", "MSFT")
    # Only 1 API call made (bulk), not 3
    assert len(httpx_mock.get_requests()) == 1
    c.close()


def test_sync_all(httpx_mock):
    """sync_all() loads multiple years via bulk endpoints."""
    for year in [2022, 2023]:
        httpx_mock.add_response(
            url=re.compile(rf".*/income-statement-bulk.*year={year}"),
            json=[_income_row("AAPL", str(year))],
        )
        httpx_mock.add_response(
            url=re.compile(rf".*/balance-sheet-statement-bulk.*year={year}"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(rf".*/cash-flow-statement-bulk.*year={year}"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(rf".*/key-metrics-bulk.*year={year}"),
            json=[],
        )
        httpx_mock.add_response(
            url=re.compile(rf".*/ratios-bulk.*year={year}"),
            json=[],
        )
        # financial_scores uses per-symbol (not bulk) — no mock needed here
    # Paginated profile bulk, delisted companies, batch (shares float), treasury rates
    httpx_mock.add_response(url=re.compile(r".*/profile-bulk.*"), json=[])
    httpx_mock.add_response(url=re.compile(r".*/delisted-companies.*"), json=[])
    httpx_mock.add_response(url=re.compile(r".*/shares-float-all.*"), json=[])
    httpx_mock.add_response(url=re.compile(r".*/treasury-rates.*"), json=[])

    c = FMPClient(api_key="test", cache_path=None)
    result = c.sync_all(years=[2022, 2023])

    assert result["income_statement"] == 2  # 1 row per year
    c.close()


def test_query_auto_fetch_true_still_works(httpx_mock):
    """Default auto_fetch=True fetches data when missing."""
    httpx_mock.add_response(
        url=re.compile(r".*/historical-price-eod/full.*"),
        json=[_price_row("2024-01-15", 183.0)],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (c.query()
          .symbols("AAPL")
          .select("close")
          .date_range("2024-01-01", "2024-12-31")
          .execute())  # auto_fetch defaults to True

    assert len(df) == 1
    assert df["close"][0] == 183.0
    c.close()


def test_query_auto_fetch_false_empty_store(httpx_mock):
    """auto_fetch=False with empty store returns empty DataFrame."""
    c = FMPClient(api_key="test", cache_path=None)
    df = (c.query()
          .symbols("AAPL")
          .select("close")
          .date_range("2024-01-01", "2024-12-31")
          .auto_fetch(False)
          .execute())

    assert len(df) == 0
    assert len(httpx_mock.get_requests()) == 0  # no API calls
    c.close()


def test_sync_progress_callback(httpx_mock):
    """sync() calls progress callback."""
    httpx_mock.add_response(
        url=re.compile(r".*/historical-price-eod/full.*"),
        json=[_price_row()],
    )

    messages = []
    def progress(ds: str, msg: str):
        messages.append((ds, msg))

    c = FMPClient(api_key="test", cache_path=None)
    c.sync(
        symbols=["AAPL"], datasets=["daily_price"],
        start="2024-01-01", end="2024-12-31",
        on_progress=progress,
    )

    assert len(messages) > 0
    assert any("daily_price" in ds for ds, _ in messages)
    c.close()


def test_store_has_data(httpx_mock):
    """Store has_data correctly reports presence."""
    c = FMPClient(api_key="test", cache_path=None)

    # Empty store
    assert c.store.has_data("daily_price", "AAPL") is False

    # Write some data
    c.store.write("daily_price", [
        {"symbol": "AAPL", "date": "2024-01-15", "close": 183.0,
         "open": 180.0, "high": 185.0, "low": 179.0,
         "adjClose": 183.0, "volume": 50000000, "vwap": 182.0,
         "change": 3.0, "changePercent": 1.5},
    ])

    assert c.store.has_data("daily_price", "AAPL") is True
    assert c.store.has_data("daily_price", "MSFT") is False
    c.close()


def test_store_has_bulk_data():
    """has_bulk_data checks by year."""
    import duckdb
    from fmp._store import BitemporalStore

    conn = duckdb.connect(":memory:")
    store = BitemporalStore(conn)

    assert store.has_bulk_data("income_statement", 2023) is False

    store.write("income_statement", [_income_row("AAPL", "2023")])
    assert store.has_bulk_data("income_statement", 2023) is True
    assert store.has_bulk_data("income_statement", 2022) is False

    conn.close()


def test_store_symbols_with_data():
    """symbols_with_data lists all symbols in a dataset."""
    import duckdb
    from fmp._store import BitemporalStore

    conn = duckdb.connect(":memory:")
    store = BitemporalStore(conn)

    assert store.symbols_with_data("income_statement") == []

    store.write("income_statement", [
        _income_row("AAPL"), _income_row("MSFT"),
    ])
    syms = store.symbols_with_data("income_statement")
    assert set(syms) == {"AAPL", "MSFT"}

    conn.close()
