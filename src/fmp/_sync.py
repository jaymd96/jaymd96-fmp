"""Bulk data sync: load data from FMP API into the bitemporal DuckDB store."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Callable

from fmp._ontology import DATASETS

if TYPE_CHECKING:
    from fmp._http import HTTPClient
    from fmp._store import BitemporalStore


# ──────────────────────────────────────────────────────────────────────
# Bulk endpoint mapping
# ──────────────────────────────────────────────────────────────────────

# dataset_name → (bulk_endpoint, requires_year, requires_period)
BULK_MAP: dict[str, tuple[str, bool, bool]] = {
    "income_statement": ("income-statement-bulk", True, True),
    "balance_sheet": ("balance-sheet-statement-bulk", True, True),
    "cash_flow": ("cash-flow-statement-bulk", True, True),
    "key_metrics": ("key-metrics-bulk", True, True),
    "ratios": ("ratios-bulk", True, True),
}

# Datasets that can use batch (all symbols in one snapshot call)
BATCH_MAP: dict[str, str] = {
    "quote": "batch-request-end-of-day-prices",
}

# Datasets with no bulk/batch — must fetch per-symbol
PER_SYMBOL_DATASETS = {
    "daily_price", "enterprise_values", "earnings_data", "dividends_data",
    "analyst_estimates", "splits_data", "employee_count",
}

# Datasets that are date-only (no symbol) — fetch once
DATE_ONLY_DATASETS = {"treasury_rates"}

# Snapshot datasets — fetch per symbol, no date range
SNAPSHOT_DATASETS = {
    "profile", "financial_scores", "dcf_data", "esg_data", "price_change",
    "institutional_summary", "price_target", "grades_consensus", "ratings",
    "shares_float_data",
}


class SyncManager:
    """Manages bulk data loading from FMP into the bitemporal store."""

    def __init__(
        self,
        http: HTTPClient,
        store: BitemporalStore,
    ) -> None:
        self._http = http
        self._store = store

    def sync(
        self,
        *,
        symbols: list[str] | None = None,
        datasets: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        period: str = "annual",
        use_bulk: bool = True,
        max_workers: int = 10,
        on_progress: Callable[[str, str], None] | None = None,
    ) -> dict[str, int]:
        """Sync data from FMP API into the local DuckDB store.

        Args:
            symbols: Symbols to sync. Required for per-symbol datasets.
            datasets: Dataset names to sync. ``None`` = all datasets.
            start: Start date for time-series data (YYYY-MM-DD).
            end: End date for time-series data.
            period: ``"annual"`` or ``"quarter"`` for financial statements.
            use_bulk: Use bulk endpoints when available (recommended).
            max_workers: Max concurrent API requests.
            on_progress: Callback ``(dataset, message)`` for progress reporting.

        Returns:
            Dict of ``{dataset_name: rows_written}``.
        """
        target_datasets = datasets or [
            ds for ds in DATASETS
            if ds not in ("_raw_cache",)
        ]
        results: dict[str, int] = {}

        for ds_name in target_datasets:
            if ds_name not in DATASETS:
                continue

            def _progress(msg: str) -> None:
                if on_progress:
                    on_progress(ds_name, msg)

            if ds_name in BULK_MAP and use_bulk:
                rows = self._sync_bulk(ds_name, start, end, period, _progress)
            elif ds_name in BATCH_MAP:
                rows = self._sync_batch(ds_name, _progress)
            elif ds_name in DATE_ONLY_DATASETS:
                rows = self._sync_date_only(ds_name, start, end, _progress)
            elif ds_name in SNAPSHOT_DATASETS:
                rows = self._sync_snapshot(ds_name, symbols or [], max_workers, _progress)
            elif symbols:
                rows = self._sync_per_symbol(
                    ds_name, symbols, start, end, max_workers, _progress
                )
            else:
                _progress("skipped — no symbols provided and no bulk endpoint")
                rows = 0

            results[ds_name] = rows

        return results

    def sync_all(
        self,
        *,
        years: list[int] | None = None,
        period: str = "annual",
        on_progress: Callable[[str, str], None] | None = None,
    ) -> dict[str, int]:
        """Bulk-load ALL financial statement data for the given years.

        Uses bulk endpoints exclusively — one API call per dataset per year.
        Does NOT sync per-symbol datasets (daily_price, etc.).
        """
        import datetime
        if years is None:
            current_year = datetime.date.today().year
            years = list(range(current_year - 4, current_year + 1))

        results: dict[str, int] = {}
        for ds_name, (endpoint, needs_year, needs_period) in BULK_MAP.items():
            total = 0
            for year in years:
                if self._store.has_bulk_data(ds_name, year):
                    if on_progress:
                        on_progress(ds_name, f"year {year} already loaded, skipping")
                    continue

                if on_progress:
                    on_progress(ds_name, f"fetching year {year}...")

                params: dict = {"year": year}
                if needs_period:
                    params["period"] = period

                try:
                    rows = self._http.get(endpoint, params=params)
                    if rows:
                        count = self._store.write(ds_name, rows)
                        total += count
                        if on_progress:
                            on_progress(ds_name, f"year {year}: {count} rows")
                except Exception as exc:
                    if on_progress:
                        on_progress(ds_name, f"year {year} failed: {exc}")

            results[ds_name] = total
        return results

    # ------------------------------------------------------------------
    # Internal sync strategies
    # ------------------------------------------------------------------

    def _sync_bulk(
        self, ds_name: str, start: str | None, end: str | None,
        period: str, progress: Callable,
    ) -> int:
        """Sync using bulk endpoint (one call per year, all symbols)."""
        endpoint, needs_year, needs_period = BULK_MAP[ds_name]
        start_year = int(start[:4]) if start else 2020
        end_year = int(end[:4]) if end else 2025

        total = 0
        for year in range(start_year, end_year + 1):
            if self._store.has_bulk_data(ds_name, year):
                progress(f"year {year} already loaded")
                continue

            progress(f"bulk fetching year {year}...")
            params: dict = {"year": year}
            if needs_period:
                params["period"] = period
            try:
                rows = self._http.get(endpoint, params=params)
                if rows:
                    count = self._store.write(ds_name, rows)
                    total += count
                    progress(f"year {year}: {count} rows")
            except Exception as exc:
                progress(f"year {year} failed: {exc}")

        return total

    def _sync_batch(self, ds_name: str, progress: Callable) -> int:
        """Sync using batch endpoint (one call, all symbols snapshot)."""
        endpoint = BATCH_MAP[ds_name]
        progress("fetching batch snapshot...")
        try:
            rows = self._http.get(endpoint)
            if rows:
                count = self._store.write(ds_name, rows)
                progress(f"{count} rows loaded")
                return count
        except Exception as exc:
            progress(f"failed: {exc}")
        return 0

    def _sync_date_only(
        self, ds_name: str, start: str | None, end: str | None,
        progress: Callable,
    ) -> int:
        """Sync a date-only dataset (e.g., treasury_rates)."""
        ds = DATASETS[ds_name]
        if self._store.has_data(ds_name, None):
            progress("already loaded")
            return 0

        progress("fetching...")
        params: dict = {}
        if start:
            params["from"] = start
        if end:
            params["to"] = end
        try:
            rows = self._http.get(ds.endpoint, params=params)
            if rows:
                count = self._store.write(ds_name, rows)
                progress(f"{count} rows loaded")
                return count
        except Exception as exc:
            progress(f"failed: {exc}")
        return 0

    def _sync_snapshot(
        self, ds_name: str, symbols: list[str], max_workers: int,
        progress: Callable,
    ) -> int:
        """Sync snapshot datasets per symbol."""
        ds = DATASETS[ds_name]
        to_fetch = [
            s for s in symbols
            if not self._store.has_data(ds_name, s)
        ]
        if not to_fetch:
            progress(f"all {len(symbols)} symbols already loaded")
            return 0

        progress(f"fetching {len(to_fetch)} symbols...")
        return self._fetch_symbols(ds_name, ds.endpoint, to_fetch, None, None, max_workers)

    def _sync_per_symbol(
        self, ds_name: str, symbols: list[str],
        start: str | None, end: str | None, max_workers: int,
        progress: Callable,
    ) -> int:
        """Sync per-symbol datasets (daily_price, etc.)."""
        to_fetch = [
            s for s in symbols
            if not self._store.has_data(ds_name, s, start, end)
        ]
        if not to_fetch:
            progress(f"all {len(symbols)} symbols already loaded")
            return 0

        ds = DATASETS[ds_name]
        progress(f"fetching {len(to_fetch)} symbols...")
        return self._fetch_symbols(ds_name, ds.endpoint, to_fetch, start, end, max_workers)

    def _fetch_symbols(
        self, ds_name: str, endpoint: str, symbols: list[str],
        start: str | None, end: str | None, max_workers: int,
    ) -> int:
        """Fetch data for multiple symbols concurrently."""
        ds = DATASETS[ds_name]
        total = 0

        def _fetch_one(sym: str) -> int:
            params: dict[str, str] = {"symbol": sym}
            if "date" in ds.keys and start:
                params["from"] = start
            if "date" in ds.keys and end:
                params["to"] = end
            rows = self._http.get(endpoint, params=params)
            if rows:
                for row in rows:
                    row.setdefault("symbol", sym)
                return self._store.write(ds_name, rows)
            return 0

        with ThreadPoolExecutor(max_workers=min(max_workers, len(symbols))) as pool:
            futures = {pool.submit(_fetch_one, s): s for s in symbols}
            for future in as_completed(futures):
                try:
                    total += future.result()
                except Exception:
                    pass

        return total
