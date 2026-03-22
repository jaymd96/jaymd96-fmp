from __future__ import annotations

import re


def test_quote(client, httpx_mock):
    httpx_mock.add_response(json=[{"symbol": "AAPL", "price": 182.52}])
    result = client.quote("AAPL")
    assert result[0]["symbol"] == "AAPL"
    assert result[0]["price"] == 182.52


def test_quote_cached(client, httpx_mock):
    """Second call should be served from cache."""
    httpx_mock.add_response(json=[{"symbol": "AAPL", "price": 182.52}])
    client.quote("AAPL")
    result = client.quote("AAPL")
    assert len(httpx_mock.get_requests()) == 1
    assert result[0]["price"] == 182.52


def test_quote_force_refresh(client, httpx_mock):
    httpx_mock.add_response(json=[{"symbol": "AAPL", "price": 182.52}])
    httpx_mock.add_response(json=[{"symbol": "AAPL", "price": 185.00}])
    client.quote("AAPL")
    result = client.quote("AAPL", force_refresh=True)
    assert len(httpx_mock.get_requests()) == 2
    assert result[0]["price"] == 185.00


def test_quote_list_of_symbols(client, httpx_mock):
    """quote() with a list should join symbols with comma."""
    httpx_mock.add_response(
        json=[{"symbol": "AAPL"}, {"symbol": "MSFT"}]
    )
    result = client.quote(["AAPL", "MSFT"])
    assert len(result) == 2
    req = httpx_mock.get_requests()[0]
    assert "AAPL,MSFT" in str(req.url) or "AAPL%2CMSFT" in str(req.url)


def test_batch_quote(client, httpx_mock):
    httpx_mock.add_response(
        json=[{"symbol": "AAPL"}, {"symbol": "GOOG"}]
    )
    result = client.batch_quote(["AAPL", "GOOG"])
    assert len(result) == 2


def test_stock_price_change(client, httpx_mock):
    httpx_mock.add_response(json=[{"symbol": "AAPL", "1D": 1.29}])
    result = client.stock_price_change("AAPL")
    assert result[0]["1D"] == 1.29
