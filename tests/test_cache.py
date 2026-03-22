from __future__ import annotations

import time
from fmp._cache import DuckDBCache


def test_get_set():
    """Basic cache round-trip."""
    cache = DuckDBCache(None)
    cache.set("k1", "endpoint", {"a": "1"}, [{"x": 1}], ttl=3600)
    result = cache.get("k1")
    assert result == [{"x": 1}]
    cache.close()


def test_get_expired():
    """Expired entries return None."""
    cache = DuckDBCache(None)
    cache.set("k1", "endpoint", {}, [{"x": 1}], ttl=3600)
    # Manually expire by setting fetched_at in the past
    cache.connection.execute(
        "UPDATE _raw_cache SET fetched_at = now() - INTERVAL '2 HOURS' WHERE cache_key = 'k1'"
    )
    assert cache.get("k1") is None
    cache.close()


def test_get_miss():
    """Cache miss returns None."""
    cache = DuckDBCache(None)
    assert cache.get("nonexistent") is None
    cache.close()


def test_clear_all():
    """clear() with no args deletes everything."""
    cache = DuckDBCache(None)
    cache.set("k1", "ep1", {}, [{"a": 1}], ttl=3600)
    cache.set("k2", "ep2", {}, [{"b": 2}], ttl=3600)
    deleted = cache.clear()
    assert deleted == 2
    assert cache.get("k1") is None
    cache.close()


def test_clear_by_endpoint():
    """clear(endpoint=...) only deletes matching entries."""
    cache = DuckDBCache(None)
    cache.set("k1", "ep1", {}, [{"a": 1}], ttl=3600)
    cache.set("k2", "ep2", {}, [{"b": 2}], ttl=3600)
    deleted = cache.clear(endpoint="ep1")
    assert deleted == 1
    assert cache.get("k2") == [{"b": 2}]
    cache.close()


def test_upsert():
    """set() replaces existing entries with the same key."""
    cache = DuckDBCache(None)
    cache.set("k1", "ep", {}, [{"v": 1}], ttl=3600)
    cache.set("k1", "ep", {}, [{"v": 2}], ttl=3600)
    assert cache.get("k1") == [{"v": 2}]
    cache.close()


def test_sql():
    """sql() returns list of dicts."""
    cache = DuckDBCache(None)
    cache.set("k1", "ep", {}, [{"v": 1}], ttl=3600)
    rows = cache.sql("SELECT cache_key, endpoint FROM _raw_cache")
    assert rows == [{"cache_key": "k1", "endpoint": "ep"}]
    cache.close()
