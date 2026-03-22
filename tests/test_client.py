from __future__ import annotations

import os
import pytest
from fmp import FMPClient, FMPError


def test_requires_api_key():
    """Client raises if no key is provided and env var is unset."""
    env = os.environ.copy()
    env.pop("FMP_API_KEY", None)
    os.environ.clear()
    os.environ.update(env)
    with pytest.raises(FMPError, match="API key required"):
        FMPClient(cache_path=None)


def test_env_var_fallback(httpx_mock, monkeypatch):
    """Client picks up FMP_API_KEY from the environment."""
    monkeypatch.setenv("FMP_API_KEY", "env-key")
    httpx_mock.add_response(json=[{"symbol": "AAPL"}])
    c = FMPClient(cache_path=None)
    result = c.quote("AAPL")
    assert result[0]["symbol"] == "AAPL"
    # Verify the header was set
    req = httpx_mock.get_requests()[0]
    assert req.headers["apikey"] == "env-key"
    c.close()


def test_context_manager(httpx_mock):
    """Client works as a context manager."""
    httpx_mock.add_response(json=[{"symbol": "AAPL"}])
    with FMPClient(api_key="test", cache_path=None) as c:
        result = c.quote("AAPL")
    assert result[0]["symbol"] == "AAPL"


def test_clear_cache(client, httpx_mock):
    """clear_cache removes entries."""
    httpx_mock.add_response(json=[{"symbol": "AAPL"}])
    client.quote("AAPL")
    deleted = client.clear_cache()
    assert deleted >= 1


def test_sql(client, httpx_mock):
    """sql() returns results from the cache database."""
    httpx_mock.add_response(json=[{"symbol": "AAPL", "price": 100}])
    client.quote("AAPL")
    rows = client.sql("SELECT cache_key FROM _raw_cache")
    assert len(rows) >= 1
    assert "cache_key" in rows[0]
