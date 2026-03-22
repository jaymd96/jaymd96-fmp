from __future__ import annotations

import pytest
from fmp import FMPClient


@pytest.fixture
def client(httpx_mock):
    """FMPClient with in-memory cache and mocked HTTP."""
    c = FMPClient(api_key="test-key", cache_path=None)
    yield c
    c.close()
