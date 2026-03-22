from __future__ import annotations

import duckdb
import pytest
from fmp._store import BitemporalStore


@pytest.fixture
def store():
    conn = duckdb.connect(":memory:")
    s = BitemporalStore(conn)
    yield s
    conn.close()


def test_tables_created(store):
    """All ontology tables are created."""
    tables = store._conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    table_names = {t[0] for t in tables}
    assert "daily_price" in table_names
    assert "income_statement" in table_names
    assert "quote" in table_names


def test_write_and_read(store):
    """Basic write + read round-trip."""
    rows = [
        {"symbol": "AAPL", "date": "2024-01-15", "open": 180.0, "high": 185.0,
         "low": 179.0, "close": 183.0, "adjClose": 183.0, "volume": 50000000,
         "vwap": 182.0, "change": 3.0, "changePercent": 1.5},
    ]
    count = store.write("daily_price", rows)
    assert count == 1

    result = store.read("daily_price", ["AAPL"])
    assert len(result) == 1
    assert result[0]["symbol"] == "AAPL"
    assert result[0]["close"] == 183.0


def test_bitemporal_dedup(store):
    """Second write appends; read returns latest version."""
    row_v1 = [{"symbol": "AAPL", "date": "2024-01-15", "close": 183.0,
               "open": 180.0, "high": 185.0, "low": 179.0, "adjClose": 183.0,
               "volume": 50000000, "vwap": 182.0, "change": 3.0, "changePercent": 1.5}]
    store.write("daily_price", row_v1)

    # Manually backdate the first write
    store._conn.execute(
        "UPDATE daily_price SET _fetched_at = now() - INTERVAL '1 HOUR' "
        "WHERE symbol = 'AAPL'"
    )

    row_v2 = [{"symbol": "AAPL", "date": "2024-01-15", "close": 185.0,
               "open": 180.0, "high": 186.0, "low": 179.0, "adjClose": 185.0,
               "volume": 55000000, "vwap": 183.0, "change": 5.0, "changePercent": 2.5}]
    store.write("daily_price", row_v2)

    # Total rows = 2 (append-only)
    assert store.row_count("daily_price") == 2

    # Read returns only the latest
    result = store.read("daily_price", ["AAPL"])
    assert len(result) == 1
    assert result[0]["close"] == 185.0


def test_read_date_filter(store):
    rows = [
        {"symbol": "AAPL", "date": "2024-01-10", "close": 180.0,
         "open": 179.0, "high": 181.0, "low": 178.0, "adjClose": 180.0,
         "volume": 40000000, "vwap": 180.0, "change": 1.0, "changePercent": 0.5},
        {"symbol": "AAPL", "date": "2024-01-20", "close": 190.0,
         "open": 188.0, "high": 191.0, "low": 187.0, "adjClose": 190.0,
         "volume": 45000000, "vwap": 189.0, "change": 2.0, "changePercent": 1.0},
    ]
    store.write("daily_price", rows)

    result = store.read("daily_price", ["AAPL"], start="2024-01-15")
    assert len(result) == 1
    assert result[0]["close"] == 190.0


def test_is_fresh(store):
    rows = [{"symbol": "AAPL", "date": "2024-01-15", "close": 183.0,
             "open": 180.0, "high": 185.0, "low": 179.0, "adjClose": 183.0,
             "volume": 50000000, "vwap": 182.0, "change": 3.0, "changePercent": 1.5}]
    store.write("daily_price", rows)
    assert store.is_fresh("daily_price", "AAPL", ttl=3600) is True
    assert store.is_fresh("daily_price", "MSFT", ttl=3600) is False


def test_is_fresh_expired(store):
    rows = [{"symbol": "AAPL", "date": "2024-01-15", "close": 183.0,
             "open": 180.0, "high": 185.0, "low": 179.0, "adjClose": 183.0,
             "volume": 50000000, "vwap": 182.0, "change": 3.0, "changePercent": 1.5}]
    store.write("daily_price", rows)
    store._conn.execute(
        "UPDATE daily_price SET _fetched_at = now() - INTERVAL '2 HOURS' WHERE symbol = 'AAPL'"
    )
    assert store.is_fresh("daily_price", "AAPL", ttl=3600) is False


def test_revisions(store):
    row_v1 = [{"symbol": "AAPL", "date": "2024-01-15", "close": 183.0,
               "open": 180.0, "high": 185.0, "low": 179.0, "adjClose": 183.0,
               "volume": 50000000, "vwap": 182.0, "change": 3.0, "changePercent": 1.5}]
    store.write("daily_price", row_v1)
    store._conn.execute(
        "UPDATE daily_price SET _fetched_at = now() - INTERVAL '1 HOUR' WHERE symbol = 'AAPL'"
    )

    row_v2 = [{"symbol": "AAPL", "date": "2024-01-15", "close": 185.0,
               "open": 180.0, "high": 186.0, "low": 179.0, "adjClose": 185.0,
               "volume": 55000000, "vwap": 183.0, "change": 5.0, "changePercent": 2.5}]
    store.write("daily_price", row_v2)

    revs = store.revisions("daily_price", "AAPL", date="2024-01-15")
    assert len(revs) == 2
    assert revs[0]["close"] == 183.0  # older
    assert revs[1]["close"] == 185.0  # newer


def test_snapshot_dataset(store):
    """Snapshot datasets (no date key) work correctly."""
    rows = [{"symbol": "AAPL", "name": "Apple Inc.", "price": 182.52,
             "changesPercentage": 1.29, "change": 2.33, "dayLow": 179.0,
             "dayHigh": 183.0, "yearLow": 124.0, "yearHigh": 199.0,
             "marketCap": 2890000000000, "priceAvg50": 178.0, "priceAvg200": 170.0,
             "volume": 54000000, "avgVolume": 48000000, "open": 180.0,
             "previousClose": 180.0, "eps": 6.57, "pe": 27.78,
             "sharesOutstanding": 15800000000, "exchange": "NASDAQ"}]
    store.write("quote", rows)

    result = store.read("quote", ["AAPL"])
    assert len(result) == 1
    assert result[0]["price"] == 182.52
