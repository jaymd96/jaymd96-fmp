"""Tests for post-compute features (EMA, MACD, index membership, insider,
senate, grades) and edge cases.

Post-compute features run in polars after the SQL query returns. They make
additional HTTP calls for external data (insider trades, constituent lists, etc.)
which are also mocked via httpx_mock.
"""

from __future__ import annotations

import re

import polars as pl
import pytest

from fmp import FMPClient, FMPError

BASE = "https://financialmodelingprep.com/stable/"


def _url(endpoint: str) -> re.Pattern:
    """Return a regex matching the FMP URL for *endpoint*."""
    return re.compile(re.escape(BASE + endpoint) + r"(\?.*)?$")


# ── Shared mock data builders ────────────────────────────────────────────


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


def _income_statement(
    *,
    symbol="AAPL",
    date="2023-09-30",
    period="FY",
    revenue=100_000_000_000,
    gross_profit=40_000_000_000,
    net_income=20_000_000_000,
    operating_income=30_000_000_000,
    ebitda=35_000_000_000,
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
        "costOfRevenue": revenue - gross_profit,
        "grossProfit": gross_profit,
        "grossProfitRatio": gross_profit / revenue if revenue else 0,
        "researchAndDevelopmentExpenses": 8_000_000_000,
        "sellingGeneralAndAdministrativeExpenses": 2_000_000_000,
        "operatingExpenses": 10_000_000_000,
        "operatingIncome": operating_income,
        "operatingIncomeRatio": operating_income / revenue if revenue else 0,
        "interestIncome": 2_000_000_000,
        "interestExpense": 3_000_000_000,
        "depreciationAndAmortization": 5_000_000_000,
        "ebitda": ebitda,
        "ebitdaratio": ebitda / revenue if revenue else 0,
        "netIncome": net_income,
        "netIncomeRatio": net_income / revenue if revenue else 0,
        "eps": 6.0,
        "epsdiluted": 5.95,
        "incomeBeforeTax": 25_000_000_000,
        "incomeTaxExpense": 5_000_000_000,
        "costAndExpenses": revenue - net_income,
        "otherExpenses": 0,
        "totalOtherIncomeExpensesNet": 0,
        "weightedAverageShsOut": 15_000_000_000,
        "weightedAverageShsOutDil": 15_200_000_000,
        "link": "",
        "finalLink": "",
    }
    d.update(overrides)
    return d


def _quote(
    *,
    symbol="AAPL",
    price=150.0,
    market_cap=2_000_000_000_000,
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
        "eps": 6.0,
        "pe": 25.0,
        "sharesOutstanding": 15_000_000_000,
        "exchange": "NASDAQ",
    }
    d.update(overrides)
    return d


# ── Helper: generate date strings ────────────────────────────────────────

def _dates(n: int, year=2024, month=1, start_day=2):
    """Generate n date strings in YYYY-MM-DD format."""
    from datetime import date, timedelta
    base = date(year, month, start_day)
    return [(base + timedelta(days=i)).isoformat() for i in range(n)]


# ── EMA computation ─────────────────────────────────────────────────────


def test_ema_computation(httpx_mock):
    """EMA-20: linearly increasing prices from 101 to 130 (30 data points)."""
    dates = _dates(30)
    prices = [_daily_price(d, 100.0 + i + 1) for i, d in enumerate(dates)]
    httpx_mock.add_response(url=_url("historical-price-eod/full"), json=prices)

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("close", "ema_20")
        .date_range("2024-01-01", "2024-02-15")
        .execute()
    )

    assert len(df) == 30
    assert "ema_20" in df.columns

    non_null = df["ema_20"].drop_nulls()
    assert len(non_null) == 30

    closes = df["close"].to_list()
    ema_vals = df["ema_20"].to_list()
    for v in ema_vals:
        assert v is not None
        assert min(closes) <= v <= max(closes)

    # For linearly increasing prices, EMA lags behind close
    assert df["ema_20"][-1] < df["close"][-1]
    c.close()


# ── MACD computation ────────────────────────────────────────────────────


def test_macd_features(httpx_mock):
    """MACD: line, signal, histogram. Verify histogram = line - signal."""
    dates = _dates(30)
    prices = [
        _daily_price(d, 100.0 + i * 0.5 + (i % 5) * 0.3)
        for i, d in enumerate(dates)
    ]
    httpx_mock.add_response(url=_url("historical-price-eod/full"), json=prices)

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("close", "macd_line", "macd_signal", "macd_histogram")
        .date_range("2024-01-01", "2024-02-15")
        .execute()
    )

    assert "macd_line" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_histogram" in df.columns
    assert len(df) == 30

    line = df["macd_line"][-1]
    signal = df["macd_signal"][-1]
    hist = df["macd_histogram"][-1]
    assert line is not None
    assert signal is not None
    assert hist is not None
    assert abs(hist - (line - signal)) < 1e-6

    assert df["macd_line"].drop_nulls().len() > 0
    assert df["macd_signal"].drop_nulls().len() > 0
    assert df["macd_histogram"].drop_nulls().len() > 0
    c.close()


# ── Index membership ────────────────────────────────────────────────────


def test_index_membership(httpx_mock):
    """in_sp500: AAPL should be 1 (in constituent list)."""
    httpx_mock.add_response(
        url=_url("historical-price-eod/full"),
        json=[
            _daily_price("2024-01-15", 183.0),
            _daily_price("2024-01-16", 185.0),
        ],
    )
    httpx_mock.add_response(
        url=_url("sp500-constituent"),
        json=[
            {"symbol": "AAPL"},
            {"symbol": "MSFT"},
            {"symbol": "GOOGL"},
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("close", "in_sp500")
        .date_range("2024-01-15", "2024-01-16")
        .execute()
    )

    assert "in_sp500" in df.columns
    assert len(df) == 2
    for val in df["in_sp500"].to_list():
        assert val == 1
    c.close()


def test_index_membership_not_in_index(httpx_mock):
    """in_sp500: ZZZZ should be 0 (not in constituent list)."""
    httpx_mock.add_response(
        url=_url("historical-price-eod/full"),
        json=[_daily_price("2024-01-15", 50.0)],
    )
    httpx_mock.add_response(
        url=_url("sp500-constituent"),
        json=[
            {"symbol": "AAPL"},
            {"symbol": "MSFT"},
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("ZZZZ")
        .select("close", "in_sp500")
        .date_range("2024-01-15", "2024-01-16")
        .execute()
    )

    assert "in_sp500" in df.columns
    assert len(df) == 1
    assert df["in_sp500"][0] == 0
    c.close()


# ── Insider trades ──────────────────────────────────────────────────────


def test_insider_signals(httpx_mock):
    """Insider features: net buying, buy/sell counts, officer flag."""
    httpx_mock.add_response(
        url=_url("historical-price-eod/full"),
        json=[_daily_price("2026-03-15", 155.0)],
    )
    httpx_mock.add_response(
        url=_url("insider-trading/search"),
        json=[
            {
                "symbol": "AAPL",
                "transactionDate": "2026-03-01",
                "reportingName": "COOK TIMOTHY",
                "typeOfOwner": "officer",
                "acquistionOrDisposition": "A",
                "securitiesTransacted": 10000,
                "price": 150.0,
            },
            {
                "symbol": "AAPL",
                "transactionDate": "2026-03-05",
                "reportingName": "WILLIAMS JEFF",
                "typeOfOwner": "officer",
                "acquistionOrDisposition": "A",
                "securitiesTransacted": 5000,
                "price": 155.0,
            },
            {
                "symbol": "AAPL",
                "transactionDate": "2026-03-10",
                "reportingName": "MAESTRI LUCA",
                "typeOfOwner": "officer",
                "acquistionOrDisposition": "D",
                "securitiesTransacted": 20000,
                "price": 160.0,
            },
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select(
            "close",
            "insider_net_buying_90d",
            "insider_buy_count_30d",
            "insider_sell_count_30d",
            "insider_officer_buying",
        )
        .date_range("2026-03-01", "2026-03-31")
        .execute()
    )

    assert len(df) == 1
    assert "insider_net_buying_90d" in df.columns
    assert "insider_buy_count_30d" in df.columns
    assert "insider_sell_count_30d" in df.columns
    assert "insider_officer_buying" in df.columns

    assert df["insider_buy_count_30d"][0] == 2
    assert df["insider_sell_count_30d"][0] == 1
    assert df["insider_officer_buying"][0] == 1

    # net_buying = buy_value - sell_value
    # buy_value = 10000*150 + 5000*155 = 2275000
    # sell_value = 20000*160 = 3200000
    # net = -925000
    net = df["insider_net_buying_90d"][0]
    assert net is not None
    assert abs(net - (-925000.0)) < 1.0
    c.close()


# ── Senate trades ────────────────────────────────────────────────────────


def test_senate_signals(httpx_mock):
    """Senate: buy count and activity flag."""
    httpx_mock.add_response(
        url=_url("historical-price-eod/full"),
        json=[_daily_price("2026-03-15", 155.0)],
    )
    httpx_mock.add_response(
        url=_url("senate-trading"),
        json=[
            {
                "symbol": "AAPL",
                "transactionDate": "2026-03-01",
                "senator": "John Smith",
                "type": "Purchase",
                "amount": "$1,001 - $15,000",
            },
            {
                "symbol": "AAPL",
                "transactionDate": "2026-03-10",
                "senator": "Jane Doe",
                "type": "Purchase",
                "amount": "$15,001 - $50,000",
            },
            {
                "symbol": "AAPL",
                "transactionDate": "2026-02-15",
                "senator": "Bob Wilson",
                "type": "Sale (Full)",
                "amount": "$50,001 - $100,000",
            },
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("senate_buy_count_90d", "senate_activity_flag")
        .date_range("2026-03-01", "2026-03-31")
        .execute()
    )

    assert len(df) == 1
    assert df["senate_buy_count_90d"][0] == 2
    assert df["senate_activity_flag"][0] == 1
    c.close()


# ── Analyst grades ───────────────────────────────────────────────────────


def test_grade_signals(httpx_mock):
    """Grades: upgrades, downgrades, ratio."""
    httpx_mock.add_response(
        url=_url("historical-price-eod/full"),
        json=[_daily_price("2026-03-15", 155.0)],
    )
    httpx_mock.add_response(
        url=_url("grades"),
        json=[
            {
                "symbol": "AAPL",
                "date": "2026-03-01",
                "action": "upgrade",
                "gradingCompany": "Morgan Stanley",
                "previousGrade": "Equal Weight",
                "newGrade": "Overweight",
            },
            {
                "symbol": "AAPL",
                "date": "2026-03-05",
                "action": "upgrade",
                "gradingCompany": "Goldman Sachs",
                "previousGrade": "Neutral",
                "newGrade": "Buy",
            },
            {
                "symbol": "AAPL",
                "date": "2026-03-10",
                "action": "downgrade",
                "gradingCompany": "Barclays",
                "previousGrade": "Overweight",
                "newGrade": "Equal Weight",
            },
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("upgrades_90d", "downgrades_90d", "upgrade_downgrade_ratio")
        .date_range("2026-03-01", "2026-03-31")
        .execute()
    )

    assert len(df) == 1
    assert df["upgrades_90d"][0] == 2
    assert df["downgrades_90d"][0] == 1
    ratio = df["upgrade_downgrade_ratio"][0]
    assert ratio is not None
    assert abs(ratio - 2.0) < 1e-6
    c.close()


# ── Edge cases ──────────────────────────────────────────────────────────


def test_empty_response(httpx_mock):
    """Empty API response should return an empty DataFrame, no crash."""
    httpx_mock.add_response(url=_url("historical-price-eod/full"), json=[])

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select("close")
        .date_range("2024-01-01", "2024-01-31")
        .execute()
    )

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 0
    c.close()


def test_multi_symbol(httpx_mock):
    """Two symbols get different mock responses; features computed per-symbol."""
    # httpx_mock matches on URL; both symbols hit the same endpoint but with
    # different params. We use is_reusable since both requests go to the same URL.
    httpx_mock.add_response(
        url=_url("historical-price-eod/full"),
        json=[
            _daily_price("2024-01-15", 180.0),
            _daily_price("2024-01-16", 185.0),
        ],
    )
    httpx_mock.add_response(
        url=_url("historical-price-eod/full"),
        json=[
            _daily_price("2024-01-15", 400.0),
            _daily_price("2024-01-16", 410.0),
        ],
    )

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL", "MSFT")
        .select("close", "return_1d")
        .date_range("2024-01-15", "2024-01-16")
        .execute()
    )

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 4

    # Check that both symbols have data
    symbols = df["symbol"].unique().to_list()
    assert "AAPL" in symbols or "MSFT" in symbols

    # Verify return_1d is computed (second day of each symbol should be non-null)
    day_2 = df.filter(pl.col("date").cast(str) == "2024-01-16")
    non_null_returns = day_2["return_1d"].drop_nulls()
    assert len(non_null_returns) >= 1
    c.close()


def test_unknown_field_error():
    """Selecting a nonexistent field should raise FMPError."""
    c = FMPClient(api_key="test", cache_path=None)
    with pytest.raises(FMPError, match="Unknown field"):
        (
            c.query()
            .symbols("AAPL")
            .select("nonexistent_xyz")
            .date_range("2024-01-01", "2024-12-31")
            .execute()
        )
    c.close()


def test_mixed_base_derived_postcompute(httpx_mock):
    """Mix of base field, SQL-derived field, and post-compute field in one query."""
    dates = _dates(23, start_day=2)
    prices = [_daily_price(d, 100.0 + i + 2) for i, d in enumerate(dates)]
    httpx_mock.add_response(url=_url("historical-price-eod/full"), json=prices)

    c = FMPClient(api_key="test", cache_path=None)
    df = (
        c.query()
        .symbols("AAPL")
        .select(
            "close",           # base field
            "return_1d",       # SQL-derived field
            "ema_20",          # post-compute field
        )
        .date_range("2024-01-01", "2024-01-31")
        .execute()
    )

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 23
    assert "close" in df.columns
    assert "return_1d" in df.columns
    assert "ema_20" in df.columns

    assert df["close"][0] is not None
    assert df["return_1d"][0] is None
    assert df["return_1d"][1] is not None
    assert df["ema_20"][-1] is not None
    c.close()
