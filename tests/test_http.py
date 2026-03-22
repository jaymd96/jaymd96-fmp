from __future__ import annotations

import pytest
from fmp import FMPClient, FMPError, AuthenticationError, RateLimitError


def test_retry_on_429(client, httpx_mock):
    """Client retries on 429 and succeeds on subsequent attempt."""
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(json=[{"symbol": "AAPL"}])
    result = client.quote("AAPL")
    assert result[0]["symbol"] == "AAPL"
    assert len(httpx_mock.get_requests()) == 2


def test_429_exhausted(client, httpx_mock):
    """Client raises RateLimitError after exhausting retries."""
    for _ in range(3):
        httpx_mock.add_response(status_code=429)
    with pytest.raises(RateLimitError):
        client.quote("AAPL")


def test_401_raises_auth_error(client, httpx_mock):
    """Client raises AuthenticationError on 401."""
    httpx_mock.add_response(
        status_code=401,
        json={"Error Message": "Invalid API KEY."},
    )
    with pytest.raises(AuthenticationError):
        client.quote("AAPL")


def test_error_message_in_200(client, httpx_mock):
    """Client raises FMPError when 200 body contains an error object."""
    httpx_mock.add_response(
        json={"Error Message": "Limit reached."},
    )
    with pytest.raises(FMPError, match="Limit reached"):
        client.quote("AAPL")


def test_normalizes_dict_response(client, httpx_mock):
    """Single-object responses are wrapped in a list."""
    httpx_mock.add_response(json={"key": "value"})
    result = client._request("test-path")
    assert result == [{"key": "value"}]
