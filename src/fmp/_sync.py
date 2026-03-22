"""Bulk data sync: load data from FMP API into the bitemporal DuckDB store.

Optimizes API calls by using bulk endpoints wherever possible:
- Financial statements: 1 call per year for ALL symbols
- Profiles/scores: paginated bulk (1 call per page for ALL symbols)
- Quotes: 1 batch call for ALL symbols
- Per-symbol: only when no bulk/batch exists (daily_price, etc.)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Callable

from fmp._ontology import DATASETS

if TYPE_CHECKING:
    from fmp._http import HTTPClient
    from fmp._store import BitemporalStore


# ──────────────────────────────────────────────────────────────────────
# Endpoint strategy mapping
# ──────────────────────────────────────────────────────────────────────

# dataset → (bulk_endpoint, requires_year, requires_period)
# One call per year returns ALL symbols
BULK_YEARLY: dict[str, tuple[str, bool, bool]] = {
    "income_statement": ("income-statement-bulk", True, True),
    "balance_sheet": ("balance-sheet-statement-bulk", True, True),
    "cash_flow": ("cash-flow-statement-bulk", True, True),
    "key_metrics": ("key-metrics-bulk", True, True),
    "ratios": ("ratios-bulk", True, True),
}

# dataset → (bulk_endpoint, param_name)
# Paginated bulk: 1 call per page returns ALL symbols
BULK_PAGINATED: dict[str, tuple[str, str]] = {
    "profile": ("profile-bulk", "part"),
}

# dataset → (bulk_endpoint, requires_year)
# Year-based bulk, no period param
BULK_YEARLY_NO_PERIOD: dict[str, tuple[str, bool]] = {
    # financial_scores removed — bulk endpoint doesn't exist (404)
}

# dataset → batch_endpoint
# One call returns all symbols (snapshot)
BATCH_ALL: dict[str, str] = {
    # Note: batch-request-end-of-day-prices returns 404 on some plans.
    # quote is handled as PER_SYMBOL_SNAPSHOT as fallback.
}

# Datasets with no bulk — must fetch per-symbol, but have date range
PER_SYMBOL_TIMESERIES = {
    "daily_price", "enterprise_values", "earnings_data", "dividends_data",
    "analyst_estimates", "splits_data", "employee_count",
}

# Datasets that are date-only (no symbol key) — fetch once
DATE_ONLY = {"treasury_rates"}

# Snapshot datasets without bulk — fetch per symbol, no date range
PER_SYMBOL_SNAPSHOT = {
    "quote", "dcf_data", "esg_data", "price_change",
    "institutional_summary", "price_target", "grades_consensus", "ratings",
    "shares_float_data", "financial_scores",
}

# Extra query params required by specific endpoints beyond symbol/date range.
EXTRA_PARAMS: dict[str, dict[str, object]] = {
    "institutional_summary": {"year": 2024, "quarter": 4},
    "analyst_estimates": {"period": "annual"},
}


def _api_calls_estimate(
    symbols: list[str] | None,
    datasets: list[str] | None,
    start: str | None,
    end: str | None,
) -> dict[str, int]:
    """Estimate API calls needed for a sync operation."""
    target_ds = datasets or list(DATASETS.keys())
    n_sym = len(symbols) if symbols else 6000
    start_year = int(start[:4]) if start else 1995
    end_year = int(end[:4]) if end else 2025
    n_years = end_year - start_year + 1

    est: dict[str, int] = {}
    for ds in target_ds:
        if ds in BULK_YEARLY:
            est[ds] = n_years
        elif ds in BULK_YEARLY_NO_PERIOD:
            est[ds] = n_years
        elif ds in BULK_PAGINATED:
            est[ds] = 10  # ~10 pages for all profiles
        elif ds in BATCH_ALL:
            est[ds] = 1
        elif ds in DATE_ONLY:
            est[ds] = 1
        elif ds in PER_SYMBOL_TIMESERIES:
            est[ds] = n_sym
        elif ds in PER_SYMBOL_SNAPSHOT:
            est[ds] = n_sym
    return est


class SyncManager:
    """Manages bulk data loading from FMP into the bitemporal store."""

    def __init__(self, http: HTTPClient, store: BitemporalStore) -> None:
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

        Uses the most efficient fetch strategy for each dataset:
        bulk > batch > per-symbol.

        Args:
            symbols: Symbols to sync. Required for per-symbol datasets.
            datasets: Dataset names to sync. ``None`` = all datasets.
            start: Start date (YYYY-MM-DD).
            end: End date (YYYY-MM-DD).
            period: ``"annual"`` or ``"quarter"`` for financial statements.
            use_bulk: Use bulk endpoints when available.
            max_workers: Max concurrent API requests for per-symbol fetches.
            on_progress: Callback ``(dataset, message)``.

        Returns:
            Dict of ``{dataset_name: rows_written}``.
        """
        target_datasets = datasets or list(DATASETS.keys())
        results: dict[str, int] = {}

        for ds_name in target_datasets:
            if ds_name not in DATASETS:
                continue

            def _prog(msg: str, _ds=ds_name) -> None:
                if on_progress:
                    on_progress(_ds, msg)

            rows = 0
            if ds_name in BULK_YEARLY and use_bulk:
                rows = self._sync_bulk_yearly(ds_name, start, end, period, _prog)
            elif ds_name in BULK_YEARLY_NO_PERIOD and use_bulk:
                rows = self._sync_bulk_yearly_no_period(ds_name, start, end, _prog)
            elif ds_name in BULK_PAGINATED and use_bulk:
                rows = self._sync_bulk_paginated(ds_name, _prog)
            elif ds_name in BATCH_ALL:
                rows = self._sync_batch(ds_name, _prog)
            elif ds_name in DATE_ONLY:
                rows = self._sync_date_only(ds_name, start, end, _prog)
            elif ds_name in PER_SYMBOL_SNAPSHOT:
                rows = self._sync_per_symbol_snapshot(
                    ds_name, symbols or [], max_workers, _prog
                )
            elif ds_name in PER_SYMBOL_TIMESERIES and symbols:
                rows = self._sync_per_symbol_ts(
                    ds_name, symbols, start, end, max_workers, _prog
                )
            elif symbols:
                # Fallback — treat as per-symbol timeseries
                rows = self._sync_per_symbol_ts(
                    ds_name, symbols, start, end, max_workers, _prog
                )
            else:
                _prog("skipped — no symbols and no bulk endpoint")

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

        Uses bulk endpoints exclusively. One API call per dataset per year.
        Also loads profiles (paginated bulk) and financial scores.
        """
        import datetime
        if years is None:
            current_year = datetime.date.today().year
            years = list(range(current_year - 4, current_year + 1))

        results: dict[str, int] = {}

        def _prog(ds: str, msg: str) -> None:
            if on_progress:
                on_progress(ds, msg)

        # Yearly bulk (financial statements, metrics, ratios)
        for ds_name, (endpoint, _, needs_period) in BULK_YEARLY.items():
            total = 0
            for year in years:
                if self._store.has_bulk_data(ds_name, year):
                    _prog(ds_name, f"year {year} already loaded")
                    continue
                _prog(ds_name, f"fetching year {year}...")
                params: dict = {"year": year}
                if needs_period:
                    params["period"] = period
                try:
                    rows = self._http.get(endpoint, params=params)
                    if rows:
                        total += self._store.write(ds_name, rows)
                        _prog(ds_name, f"year {year}: {len(rows)} rows")
                except Exception as exc:
                    _prog(ds_name, f"year {year} failed: {exc}")
            results[ds_name] = total

        # Yearly bulk without period (financial scores)
        for ds_name, (endpoint, _) in BULK_YEARLY_NO_PERIOD.items():
            total = 0
            for year in years:
                if self._store.has_bulk_data(ds_name, year):
                    _prog(ds_name, f"year {year} already loaded")
                    continue
                _prog(ds_name, f"fetching year {year}...")
                try:
                    rows = self._http.get(endpoint, params={"year": year})
                    if rows:
                        total += self._store.write(ds_name, rows)
                except Exception as exc:
                    _prog(ds_name, f"year {year} failed: {exc}")
            results[ds_name] = total

        # Paginated bulk (profiles)
        for ds_name in BULK_PAGINATED:
            _prog(ds_name, "fetching paginated bulk...")
            results[ds_name] = self._sync_bulk_paginated(
                ds_name, lambda msg, _ds=ds_name: _prog(_ds, msg)
            )

        # Batch (quotes)
        for ds_name in BATCH_ALL:
            results[ds_name] = self._sync_batch(
                ds_name, lambda msg, _ds=ds_name: _prog(_ds, msg)
            )

        # Treasury rates
        for ds_name in DATE_ONLY:
            start_y = str(min(years))
            end_y = str(max(years))
            results[ds_name] = self._sync_date_only(
                ds_name, f"{start_y}-01-01", f"{end_y}-12-31",
                lambda msg, _ds=ds_name: _prog(_ds, msg),
            )

        return results

    def sync_universe(
        self,
        universe: str = "sp500",
        *,
        datasets: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        period: str = "annual",
        max_workers: int = 10,
        on_progress: Callable[[str, str], None] | None = None,
    ) -> dict[str, int]:
        """Sync all data for a stock universe (S&P 500, Nasdaq, Dow Jones).

        Automatically fetches the constituent list, then syncs all datasets
        for those symbols.

        Args:
            universe: ``"sp500"``, ``"nasdaq"``, or ``"dowjones"``.
            datasets: Datasets to sync. ``None`` = all.
            start: Start date.
            end: End date.
        """
        endpoint_map = {
            "sp500": "sp500-constituent",
            "nasdaq": "nasdaq-constituent",
            "dowjones": "dowjones-constituent",
        }
        endpoint = endpoint_map.get(universe)
        if not endpoint:
            raise ValueError(f"Unknown universe: {universe!r}. Use 'sp500', 'nasdaq', or 'dowjones'.")

        if on_progress:
            on_progress("universe", f"Fetching {universe} constituents...")

        constituents = self._http.get(endpoint)
        symbols = [c["symbol"] for c in constituents if "symbol" in c]

        if on_progress:
            on_progress("universe", f"Found {len(symbols)} symbols in {universe}")

        return self.sync(
            symbols=symbols,
            datasets=datasets,
            start=start, end=end,
            period=period, use_bulk=True,
            max_workers=max_workers,
            on_progress=on_progress,
        )

    def estimate_calls(
        self,
        *,
        symbols: list[str] | None = None,
        datasets: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, int]:
        """Estimate API calls needed without making any.

        Returns ``{dataset: estimated_calls}`` and a ``_total`` key.
        """
        est = _api_calls_estimate(symbols, datasets, start, end)
        est["_total"] = sum(est.values())
        return est

    # ------------------------------------------------------------------
    # Internal sync strategies
    # ------------------------------------------------------------------

    def _sync_bulk_yearly(
        self, ds_name: str, start: str | None, end: str | None,
        period: str, progress: Callable,
    ) -> int:
        endpoint, _, needs_period = BULK_YEARLY[ds_name]
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
                    total += self._store.write(ds_name, rows)
                    progress(f"year {year}: {len(rows)} rows")
            except Exception as exc:
                progress(f"year {year} failed: {exc}")
        return total

    def _sync_bulk_yearly_no_period(
        self, ds_name: str, start: str | None, end: str | None,
        progress: Callable,
    ) -> int:
        endpoint, _ = BULK_YEARLY_NO_PERIOD[ds_name]
        start_year = int(start[:4]) if start else 2020
        end_year = int(end[:4]) if end else 2025
        total = 0
        for year in range(start_year, end_year + 1):
            if self._store.has_bulk_data(ds_name, year):
                progress(f"year {year} already loaded")
                continue
            progress(f"bulk fetching year {year}...")
            try:
                rows = self._http.get(endpoint, params={"year": year})
                if rows:
                    total += self._store.write(ds_name, rows)
                    progress(f"year {year}: {len(rows)} rows")
            except Exception as exc:
                progress(f"year {year} failed: {exc}")
        return total

    def _sync_bulk_paginated(self, ds_name: str, progress: Callable) -> int:
        """Sync via paginated bulk endpoint (e.g., profile-bulk)."""
        endpoint, param_name = BULK_PAGINATED[ds_name]
        if self._store.row_count(ds_name) > 0:
            progress("already loaded")
            return 0

        total = 0
        part = 0
        while True:
            progress(f"fetching page {part}...")
            try:
                rows = self._http.get(endpoint, params={param_name: str(part)})
                if not rows:
                    break
                total += self._store.write(ds_name, rows)
                progress(f"page {part}: {len(rows)} rows")
                if len(rows) < 1000:
                    break
                part += 1
            except Exception as exc:
                progress(f"page {part} failed: {exc}")
                break
        return total

    def _sync_batch(self, ds_name: str, progress: Callable) -> int:
        endpoint = BATCH_ALL[ds_name]
        if self._store.row_count(ds_name) > 0:
            progress("already loaded")
            return 0
        progress("fetching batch...")
        try:
            rows = self._http.get(endpoint)
            if rows:
                count = self._store.write(ds_name, rows)
                progress(f"{count} rows loaded")
                return count
            else:
                progress("empty response — endpoint may not be available on this plan")
        except Exception as exc:
            progress(f"failed: {exc} — skipping")

    def _sync_date_only(
        self, ds_name: str, start: str | None, end: str | None,
        progress: Callable,
    ) -> int:
        ds = DATASETS[ds_name]
        if self._store.has_data(ds_name, None, start, end):
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

    def _sync_per_symbol_snapshot(
        self, ds_name: str, symbols: list[str], max_workers: int,
        progress: Callable,
    ) -> int:
        ds = DATASETS[ds_name]
        to_fetch = [s for s in symbols if not self._store.has_data(ds_name, s)]
        if not to_fetch:
            progress(f"all {len(symbols)} symbols already loaded")
            return 0
        progress(f"fetching {len(to_fetch)} symbols...")
        return self._fetch_symbols(ds_name, ds.endpoint, to_fetch, None, None, max_workers)

    def _sync_per_symbol_ts(
        self, ds_name: str, symbols: list[str],
        start: str | None, end: str | None, max_workers: int,
        progress: Callable,
    ) -> int:
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
        ds = DATASETS[ds_name]
        extra = EXTRA_PARAMS.get(ds_name, {})
        total = 0

        def _fetch_one(sym: str) -> int:
            params: dict[str, str] = {"symbol": sym}
            if "date" in ds.keys and start:
                params["from"] = start
            if "date" in ds.keys and end:
                params["to"] = end
            params.update(extra)
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
