"""DuckDB-backed cache layer for FMP API responses."""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb


class DuckDBCache:
    """Cache FMP API responses in a local DuckDB database.

    Args:
        path: Path to the DuckDB file. ``None`` or ``":memory:"`` for in-memory.
              Defaults to ``"~/.fmp/cache.db"``. The ``~`` is expanded automatically.
    """

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS _raw_cache (
        cache_key   VARCHAR PRIMARY KEY,
        endpoint    VARCHAR NOT NULL,
        params_json VARCHAR,
        response    JSON NOT NULL,
        fetched_at  TIMESTAMP NOT NULL DEFAULT now(),
        ttl_seconds INTEGER NOT NULL
    );
    """

    def __init__(self, path: str | None = "~/.fmp/cache.db") -> None:
        if path is None or path == ":memory:":
            self._conn = duckdb.connect(":memory:")
        else:
            resolved = os.path.expanduser(path)
            Path(resolved).parent.mkdir(parents=True, exist_ok=True)
            self._conn = duckdb.connect(resolved)
        self._conn.execute(self._SCHEMA)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> list[dict] | None:
        """Return cached data if *key* exists and has not expired."""
        row = self._conn.execute(
            """
            SELECT response FROM _raw_cache
            WHERE cache_key = ?
              AND fetched_at + (ttl_seconds || ' seconds')::INTERVAL > now()
            """,
            [key],
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def set(
        self,
        key: str,
        endpoint: str,
        params: dict,
        data: list[dict],
        ttl: int,
    ) -> None:
        """Insert or replace a cached response."""
        self._conn.execute(
            """
            INSERT OR REPLACE INTO _raw_cache
                (cache_key, endpoint, params_json, response, fetched_at, ttl_seconds)
            VALUES (?, ?, ?, ?::JSON, now(), ?)
            """,
            [key, endpoint, json.dumps(params), json.dumps(data), ttl],
        )

    def clear(self, endpoint: str | None = None) -> int:
        """Delete cached entries. If *endpoint* is given, only that endpoint.

        Returns the number of rows deleted.
        """
        if endpoint:
            result = self._conn.execute(
                "DELETE FROM _raw_cache WHERE endpoint = ? RETURNING 1", [endpoint]
            )
        else:
            result = self._conn.execute("DELETE FROM _raw_cache RETURNING 1")
        return len(result.fetchall())

    def sql(self, query: str, params: list | None = None) -> list[dict]:
        """Execute arbitrary SQL and return results as a list of dicts."""
        result = self._conn.execute(query, params or [])
        columns = [desc[0] for desc in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Expose the raw DuckDB connection for advanced usage."""
        return self._conn

    def close(self) -> None:
        """Close the DuckDB connection."""
        self._conn.close()
