from __future__ import annotations

import re
import pytest
from fmp import FMPClient, FMPError


def test_fetch_many(httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*symbol=AAPL.*"),
        json=[{"symbol": "AAPL", "price": 180}],
    )
    httpx_mock.add_response(
        url=re.compile(r".*symbol=MSFT.*"),
        json=[{"symbol": "MSFT", "price": 400}],
    )

    c = FMPClient(api_key="test", cache_path=None)
    results = c.fetch_many(c.quote, ["AAPL", "MSFT"], max_workers=2)

    assert len(results) == 2
    symbols = {r[0]["symbol"] for r in results.values()}
    assert symbols == {"AAPL", "MSFT"}
    c.close()


def test_fetch_many_partial_failure(httpx_mock):
    """If some symbols fail but others succeed, results are returned."""
    httpx_mock.add_response(
        url=re.compile(r".*symbol=AAPL.*"),
        json=[{"symbol": "AAPL"}],
    )
    httpx_mock.add_response(
        url=re.compile(r".*symbol=INVALID.*"),
        status_code=404, text="Not found",
    )

    c = FMPClient(api_key="test", cache_path=None)
    results = c.fetch_many(c.quote, ["AAPL", "INVALID"], max_workers=2)

    assert len(results) == 1
    c.close()


def test_paginate_all(httpx_mock):
    httpx_mock.add_response(json=[{"id": i} for i in range(100)])
    httpx_mock.add_response(json=[{"id": i} for i in range(100, 150)])

    c = FMPClient(api_key="test", cache_path=None)
    results = c.paginate_all(c.stock_news_latest, limit=100, max_pages=10)

    assert len(results) == 150
    c.close()


def test_paginate_all_stops_on_short_page(httpx_mock):
    """Stops when a page has fewer results than the limit."""
    httpx_mock.add_response(json=[{"id": i} for i in range(50)])

    c = FMPClient(api_key="test", cache_path=None)
    results = c.paginate_all(c.stock_news_latest, limit=100, max_pages=10)

    assert len(results) == 50
    assert len(httpx_mock.get_requests()) == 1
    c.close()
