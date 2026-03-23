"""Bitemporal typed storage backed by DuckDB."""

from __future__ import annotations

import threading
from typing import Any

import duckdb

from fmp._ontology import DATASETS, DatasetDef


class BitemporalStore:
    """Append-only typed DuckDB tables generated from the ontology.

    Every fetch adds rows with ``_fetched_at = now()``.  The "current" view
    uses ``QUALIFY ROW_NUMBER() OVER (... ORDER BY _fetched_at DESC) = 1``
    to de-duplicate.

    Args:
        conn: A DuckDB connection (typically ``cache.connection``).
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._lock = threading.RLock()
        self._init_tables()

    def _execute(self, sql: str, params: list | None = None):
        """Thread-safe execute on the DuckDB connection."""
        with self._lock:
            if params:
                return self._conn.execute(sql, params)
            return self._conn.execute(sql)

    def _fetchall(self, sql: str, params: list | None = None) -> list[tuple]:
        """Thread-safe execute + fetchall."""
        with self._lock:
            result = self._conn.execute(sql, params or [])
            return result.fetchall()

    def _fetchall_with_cols(self, sql: str, params: list | None = None) -> tuple[list[str], list[tuple]]:
        """Thread-safe execute + fetchall returning (column_names, rows)."""
        with self._lock:
            result = self._conn.execute(sql, params or [])
            cols = [desc[0] for desc in result.description]
            return cols, result.fetchall()

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    def _init_tables(self) -> None:
        for ds in DATASETS.values():
            self._execute(self._ddl(ds))

    @staticmethod
    def _ddl(ds: DatasetDef) -> str:
        cols: list[str] = []

        # Key columns
        for k in ds.keys:
            if k == "symbol":
                cols.append("    symbol VARCHAR NOT NULL")
            elif k == "date":
                cols.append("    date DATE")
            elif k == "period":
                cols.append("    period VARCHAR")

        # Value columns
        for field in ds.fields.values():
            # Skip fields whose name collides with a key column
            if field.name in ds.keys:
                continue
            cols.append(f"    {field.name} {field.dtype}")

        # Transaction-time column
        cols.append("    _fetched_at TIMESTAMP NOT NULL DEFAULT now()")

        return f"CREATE TABLE IF NOT EXISTS {ds.name} (\n{','.join(chr(10) + c for c in cols)}\n);"

    # ------------------------------------------------------------------
    # Write (append-only)
    # ------------------------------------------------------------------

    def write(self, dataset: str, rows: list[dict]) -> int:
        """Write API response rows to the typed table.

        Translates camelCase API field names to snake_case column names.
        Unknown API fields are silently dropped.  Returns row count.
        Uses pandas DataFrame for fast columnar ingestion into DuckDB.
        """
        if not rows:
            return 0

        ds = DATASETS[dataset]

        # Filter out rows missing required key values (e.g., null symbol from bulk CSV)
        if "symbol" in ds.keys:
            rows = [r for r in rows if r.get("symbol")]
        if not rows:
            return 0

        # Build column_name → api_name reverse mapping (O(1) lookup)
        col_to_api: dict[str, str] = {}
        for field in ds.fields.values():
            col_to_api[field.name] = field.api_name
        col_to_api.setdefault("symbol", "symbol")
        col_to_api.setdefault("date", ds.date_api_name)
        if "period" in ds.keys:
            col_to_api.setdefault("period", "period")

        # Determine columns present in the data
        all_table_cols = list(ds.keys)
        for field in ds.fields.values():
            if field.name not in ds.keys:
                all_table_cols.append(field.name)

        # Build lookup list once
        api_keys = [col_to_api.get(col) for col in all_table_cols]

        # Identify DATE columns for empty-string → None coercion
        date_cols = {f.name for f in ds.fields.values() if f.dtype == "DATE"}
        date_cols |= {"date"} if "date" in ds.keys else set()

        # Build pandas DataFrame for fast DuckDB ingestion
        import pandas as pd

        data = {}
        for col, ak in zip(all_table_cols, api_keys):
            values = [row.get(ak) if ak else None for row in rows]
            if col in date_cols:
                values = [v if v else None for v in values]
            data[col] = values
        df = pd.DataFrame(data)

        col_names = ", ".join(all_table_cols)
        view_name = f"_bulk_{threading.get_ident()}"
        with self._lock:
            self._conn.register(view_name, df)
            self._conn.execute(
                f"INSERT INTO {ds.name} ({col_names}) SELECT {col_names} FROM {view_name}"
            )
            self._conn.unregister(view_name)

        return len(rows)

    # ------------------------------------------------------------------
    # Read (bitemporal de-dup)
    # ------------------------------------------------------------------

    def read(
        self,
        dataset: str,
        symbols: list[str],
        start: str | None = None,
        end: str | None = None,
        columns: list[str] | None = None,
    ) -> list[dict]:
        """Read the latest version of each row, optionally filtered."""
        ds = DATASETS[dataset]

        # Project columns
        if columns:
            select_cols = list(ds.keys) + [c for c in columns if c not in ds.keys]
        else:
            all_cols = list(ds.keys) + [
                f.name for f in ds.fields.values() if f.name not in ds.keys
            ]
            select_cols = all_cols

        select_str = ", ".join(select_cols)
        partition_keys = ", ".join(ds.keys)

        where_parts: list[str] = []
        params: list[Any] = []

        if symbols:
            placeholders = ", ".join(["?"] * len(symbols))
            where_parts.append(f"symbol IN ({placeholders})")
            params.extend(symbols)

        if "date" in ds.keys:
            if start:
                where_parts.append("date >= ?")
                params.append(start)
            if end:
                where_parts.append("date <= ?")
                params.append(end)

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        sql = f"""
            SELECT {select_str}
            FROM {ds.name}
            {where_clause}
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY {partition_keys}
                ORDER BY _fetched_at DESC
            ) = 1
            ORDER BY {partition_keys}
        """

        cols, rows = self._fetchall_with_cols(sql, params)
        return [dict(zip(cols, row)) for row in rows]

    def read_raw(
        self,
        dataset: str,
        symbols: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict]:
        """Read deduped rows with original API (camelCase) field names.

        Useful for consumers that expect the raw FMP response format.
        """
        ds = DATASETS[dataset]

        # Build col_to_api mapping (snake_case → camelCase)
        col_to_api: dict[str, str] = {}
        for field in ds.fields.values():
            col_to_api[field.name] = field.api_name
        for k in ds.keys:
            col_to_api[k] = k  # symbol, date, period stay as-is

        rows = self.read(dataset, symbols or [], start, end)
        return [
            {col_to_api.get(k, k): v for k, v in row.items()}
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Freshness check
    # ------------------------------------------------------------------

    def is_fresh(self, dataset: str, symbol: str | None, ttl: int) -> bool:
        """Return True if data was fetched within *ttl* seconds.

        For symbol-keyed datasets, checks freshness per symbol.
        For date-only datasets (e.g., treasury_rates), *symbol* is ignored.
        """
        ds = DATASETS[dataset]
        if "symbol" in ds.keys and symbol:
            rows = self._fetchall(
                f"SELECT 1 FROM {dataset} WHERE symbol = ? AND _fetched_at + (? || ' seconds')::INTERVAL > now() LIMIT 1",
                [symbol, ttl],
            )
        else:
            rows = self._fetchall(
                f"SELECT 1 FROM {dataset} WHERE _fetched_at + (? || ' seconds')::INTERVAL > now() LIMIT 1",
                [ttl],
            )
        return len(rows) > 0

    # ------------------------------------------------------------------
    # Data existence checks (for sync — no TTL, just "is data there?")
    # ------------------------------------------------------------------

    def has_data(
        self, dataset: str, symbol: str | None,
        start: str | None = None, end: str | None = None,
    ) -> bool:
        """Check if any data exists for this dataset/symbol (ignoring TTL)."""
        ds = DATASETS[dataset]
        where_parts: list[str] = []
        params: list = []

        if "symbol" in ds.keys and symbol:
            where_parts.append("symbol = ?")
            params.append(symbol)
        if "date" in ds.keys and start:
            where_parts.append("date >= ?")
            params.append(start)
        if "date" in ds.keys and end:
            where_parts.append("date <= ?")
            params.append(end)

        where = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        rows = self._fetchall(f"SELECT 1 FROM {dataset} {where} LIMIT 1", params)
        return len(rows) > 0

    def has_bulk_data(self, dataset: str, year: int) -> bool:
        """Check if bulk data for a given year has been loaded."""
        ds = DATASETS[dataset]
        if "date" not in ds.keys:
            return self.row_count(dataset) > 0
        rows = self._fetchall(
            f"SELECT 1 FROM {dataset} WHERE EXTRACT(YEAR FROM date) = ? LIMIT 1",
            [year],
        )
        return len(rows) > 0

    def symbols_with_data(self, dataset: str) -> list[str]:
        """List all symbols that have data in this dataset."""
        ds = DATASETS[dataset]
        if "symbol" not in ds.keys:
            return []
        rows = self._fetchall(f"SELECT DISTINCT symbol FROM {dataset} ORDER BY symbol")
        return [r[0] for r in rows]

    # ------------------------------------------------------------------
    # Revisions
    # ------------------------------------------------------------------

    def revisions(self, dataset: str, symbol: str, **filters: Any) -> list[dict]:
        """Return all historical versions for a symbol, ordered by fetch time."""
        ds = DATASETS[dataset]

        where_parts = ["symbol = ?"]
        params: list[Any] = [symbol]

        for key, value in filters.items():
            where_parts.append(f"{key} = ?")
            params.append(value)

        where_clause = " AND ".join(where_parts)

        all_cols = list(ds.keys) + [
            f.name for f in ds.fields.values() if f.name not in ds.keys
        ] + ["_fetched_at"]

        sql = f"""
            SELECT {', '.join(all_cols)}
            FROM {ds.name}
            WHERE {where_clause}
            ORDER BY _fetched_at
        """

        cols, rows = self._fetchall_with_cols(sql, params)
        return [dict(zip(cols, row)) for row in rows]

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def compact(self, dataset: str, keep_latest_n: int = 1) -> int:
        """Delete old versions, keeping the latest *n* per key combination."""
        ds = DATASETS[dataset]
        partition_keys = ", ".join(ds.keys)

        with self._lock:
            result = self._conn.execute(f"""
                DELETE FROM {ds.name}
                WHERE rowid IN (
                    SELECT rowid FROM (
                        SELECT rowid,
                               ROW_NUMBER() OVER (
                                   PARTITION BY {partition_keys}
                                   ORDER BY _fetched_at DESC
                               ) AS rn
                        FROM {ds.name}
                    ) sub
                    WHERE rn > ?
                )
            """, [keep_latest_n])
            return result.fetchone()[0] if result.description else 0

    def row_count(self, dataset: str) -> int:
        """Total rows in the typed table."""
        rows = self._fetchall(f"SELECT COUNT(*) FROM {dataset}")
        return rows[0][0] if rows else 0
