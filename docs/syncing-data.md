# Syncing Data

## Architecture

The sync system uses a store-first architecture:

1. **DuckDB is the warehouse.** Every dataset in the ontology (daily prices, income statements, balance sheets, etc.) has its own typed table in DuckDB, auto-generated from the schema.
2. **The API is the ingestion mechanism.** Sync methods fetch data from FMP and write it into the typed tables.
3. **The query builder reads from the store.** Once data is synced, queries run entirely against DuckDB -- no API calls needed.

This separation means you can sync once, then run unlimited queries offline.

### Bitemporal Storage

The store is append-only. Every row includes a `_fetched_at` timestamp. When data is re-fetched, new rows are appended rather than overwriting old ones. Queries use `QUALIFY ROW_NUMBER() OVER (PARTITION BY keys ORDER BY _fetched_at DESC) = 1` to always read the latest version of each row while preserving history.

This means you can:
- See how reported data changed across fetches (`client.revisions("AAPL", "income_statement", date="2023-09-30")`)
- Re-sync without worrying about data loss
- Compact old versions when no longer needed (`client.store.compact("income_statement")`)

## Sync Methods

### `client.sync()` -- Targeted Sync

Sync specific symbols and datasets with full quarterly history.

```python
results = client.sync(
    symbols=["AAPL", "MSFT", "GOOG"],
    datasets=["daily_price", "income_statement", "balance_sheet", "key_metrics"],
    start="2015-01-01",
    end="2024-12-31",
)
# results: {"daily_price": 7500, "income_statement": 120, ...}
```

**Parameters:**

| Parameter | Default | Description |
|---|---|---|
| `symbols` | `None` | List of ticker symbols to sync. Required for per-symbol datasets. |
| `datasets` | `None` (all) | Dataset names to sync. `None` syncs all datasets in the ontology. |
| `start` | `None` | Start date (`YYYY-MM-DD`). Determines the year range for bulk endpoints. |
| `end` | `None` | End date (`YYYY-MM-DD`). |
| `period` | `"annual"` | `"annual"` or `"quarter"` for financial statement bulk endpoints. |
| `use_bulk` | `True` | Use bulk endpoints when available (recommended). |
| `max_workers` | `10` | Max concurrent API requests for per-symbol fetches. |
| `on_progress` | `None` | Callback `(dataset_name: str, message: str) -> None`. |

**Returns:** A dict of `{dataset_name: rows_written}`.

When specific symbols are provided and the dataset has a per-symbol endpoint, `sync()` prefers per-symbol fetching (which gets full quarterly history) over bulk endpoints (which return the latest annual data for all symbols).

### `client.sync_all()` -- Bulk Market Load

Load entire-market data using bulk endpoints. One API call per dataset per year.

```python
results = client.sync_all(
    years=[2020, 2021, 2022, 2023, 2024],
    period="annual",
    on_progress=lambda ds, msg: print(f"[{ds}] {msg}"),
)
```

This is the most API-efficient way to build a broad market database. It loads:

- **Financial statements** (income, balance sheet, cash flow) via yearly bulk endpoints
- **Key metrics and ratios** via yearly bulk endpoints
- **Company profiles** via paginated bulk endpoint
- **Treasury rates** via date-range endpoint

**Parameters:**

| Parameter | Default | Description |
|---|---|---|
| `years` | Last 5 years | List of years to load. |
| `period` | `"annual"` | `"annual"` or `"quarter"` for financial statements. |
| `on_progress` | `None` | Callback `(dataset_name: str, message: str) -> None`. |

If `years` is not specified, it defaults to the current year minus 4 through the current year.

### `client.sync_universe()` -- Universe Sync

Automatically fetch the constituent list of a stock universe, then sync all datasets for those symbols.

```python
results = client.sync_universe(
    "sp500",
    datasets=["daily_price", "income_statement", "balance_sheet"],
    start="2020-01-01",
    end="2024-12-31",
    on_progress=lambda ds, msg: print(f"[{ds}] {msg}"),
)
```

**Supported universes:**

| Universe | Endpoint |
|---|---|
| `"sp500"` | S&P 500 constituents |
| `"nasdaq"` | Nasdaq constituents |
| `"dowjones"` | Dow Jones constituents |

The method fetches the constituent list first, then delegates to `sync()` with those symbols.

### `client.estimate_sync_calls()` -- Preview API Usage

Before syncing, preview how many API calls will be needed:

```python
est = client.estimate_sync_calls(
    symbols=["AAPL", "MSFT"],
    datasets=["daily_price", "income_statement"],
    start="2015-01-01",
    end="2024-12-31",
)
print(est)
# {"daily_price": 2, "income_statement": 10, "_total": 12}
```

The estimate accounts for the sync strategy each dataset uses:
- Bulk yearly datasets: 1 call per year (regardless of symbol count)
- Per-symbol datasets: 1 call per symbol
- Paginated bulk datasets: ~10 calls total
- Date-only datasets: 1 call total

## Sync Strategies

The sync system automatically chooses the most efficient fetch strategy for each dataset:

### Bulk Yearly (1 call per year for ALL symbols)

These datasets have dedicated bulk endpoints that return data for every symbol in a single API call per year:

| Dataset | Bulk Endpoint |
|---|---|
| `income_statement` | `income-statement-bulk` |
| `balance_sheet` | `balance-sheet-statement-bulk` |
| `cash_flow` | `cash-flow-statement-bulk` |
| `key_metrics` | `key-metrics-bulk` |
| `ratios` | `ratios-bulk` |

When syncing with specific symbols, the system prefers per-symbol fetching (for full quarterly history). When syncing via `sync_all()`, it uses the bulk endpoints.

### Bulk Paginated (1 call per page for ALL symbols)

| Dataset | Bulk Endpoint |
|---|---|
| `profile` | `profile-bulk` |

Fetches all company profiles in pages of ~1000. Typically completes in under 10 API calls.

### Per-Symbol Timeseries (1 call per symbol)

These datasets require per-symbol fetching but support date-range parameters:

- `daily_price`, `enterprise_values`, `earnings_data`, `dividends_data`
- `analyst_estimates`, `splits_data`, `employee_count`
- `historical_market_cap`, `historical_grades`, `historical_ratings`

Per-symbol fetches run concurrently (up to `max_workers` threads).

### Per-Symbol Snapshot (1 call per symbol, no date range)

Point-in-time data fetched per symbol:

- `quote`, `dcf_data`, `esg_data`, `price_change`
- `institutional_summary`, `price_target`, `grades_consensus`, `ratings`
- `shares_float_data`, `financial_scores`

### Date-Only (1 call total)

Datasets with no symbol key:

- `treasury_rates`

## Smart Deduplication

The sync system checks whether data already exists before making API calls:

- **Per-symbol datasets**: Checks if any rows exist for the symbol (and optional date range) in the store. Skips symbols that are already loaded.
- **Bulk yearly datasets**: Checks if any rows exist for the given year. Skips years that are already loaded.
- **Paginated bulk datasets**: Checks if the table has any rows. Skips if already loaded.

This means re-running `sync()` with the same parameters is safe and will not make redundant API calls. Only missing data is fetched.

## Progress Callbacks

All sync methods accept an `on_progress` callback to report progress:

```python
def progress(dataset: str, message: str):
    print(f"[{dataset}] {message}")

client.sync(
    symbols=["AAPL", "MSFT"],
    datasets=["daily_price", "income_statement"],
    start="2020-01-01",
    end="2024-12-31",
    on_progress=progress,
)
```

Example output:

```
[daily_price] fetching 2 symbols...
[daily_price] 2500 rows
[income_statement] fetching 2 symbols...
[income_statement] 80 rows
```

## Available Datasets

The ontology defines 27 datasets. Each has a defined grain (temporal granularity):

| Dataset | Grain | Keys |
|---|---|---|
| `daily_price` | Daily | symbol, date |
| `income_statement` | Quarterly | symbol, date, period |
| `balance_sheet` | Quarterly | symbol, date, period |
| `cash_flow` | Quarterly | symbol, date, period |
| `key_metrics` | Quarterly | symbol, date, period |
| `ratios` | Quarterly | symbol, date, period |
| `enterprise_values` | Quarterly | symbol, date, period |
| `earnings_data` | Quarterly | symbol, date |
| `dividends_data` | Daily | symbol, date |
| `splits_data` | Daily | symbol, date |
| `analyst_estimates` | Annual | symbol, date, period |
| `employee_count` | Annual | symbol, date |
| `historical_market_cap` | Daily | symbol, date |
| `historical_grades` | Daily | symbol, date |
| `historical_ratings` | Daily | symbol, date |
| `historical_institutional` | Quarterly | symbol, date |
| `quote` | Snapshot | symbol |
| `profile` | Snapshot | symbol |
| `dcf_data` | Snapshot | symbol |
| `esg_data` | Snapshot | symbol |
| `price_change` | Snapshot | symbol |
| `institutional_summary` | Snapshot | symbol |
| `price_target` | Snapshot | symbol |
| `grades_consensus` | Snapshot | symbol |
| `ratings` | Snapshot | symbol |
| `shares_float_data` | Snapshot | symbol |
| `financial_scores` | Snapshot | symbol |
| `treasury_rates` | Daily | date |

## Example: Full S&P 500 Research Database

```python
from fmp import FMPClient

with FMPClient(api_key="...", rate_limit=10) as client:
    # Preview API usage
    est = client.estimate_sync_calls(
        start="2015-01-01",
        end="2024-12-31",
    )
    print(f"Estimated API calls: {est['_total']}")

    # Sync S&P 500 with progress reporting
    results = client.sync_universe(
        "sp500",
        start="2015-01-01",
        end="2024-12-31",
        max_workers=10,
        on_progress=lambda ds, msg: print(f"  [{ds}] {msg}"),
    )

    # Summary
    total_rows = sum(results.values())
    print(f"\nSynced {total_rows:,} total rows across {len(results)} datasets")

    # Now query offline
    df = (
        client.query()
        .symbols("AAPL", "MSFT", "GOOG", "AMZN", "META")
        .select("close", "revenue", "net_income", "gross_profit_margin", "return_5d")
        .date_range("2020-01-01", "2024-12-31")
        .auto_fetch(False)
        .execute()
    )
    print(f"\nQuery result: {df.shape[0]} rows x {df.shape[1]} columns")
```

## Maintenance

### Viewing Revisions

See how data changed across fetches:

```python
revisions = client.revisions("AAPL", "income_statement", date="2023-09-30", period="FY")
for rev in revisions:
    print(f"Fetched at {rev['_fetched_at']}: revenue={rev['revenue']}")
```

### Compacting Old Versions

Remove old versions to save disk space, keeping only the latest:

```python
# Keep only the most recent version of each row
deleted = client.store.compact("daily_price", keep_latest_n=1)
print(f"Removed {deleted} old rows")
```

### Checking Store Contents

```python
# Count rows in a dataset
count = client.store.row_count("daily_price")

# List symbols that have data
symbols = client.store.symbols_with_data("income_statement")

# Check if data exists for a symbol
has_data = client.store.has_data("daily_price", "AAPL", "2020-01-01", "2024-12-31")
```
