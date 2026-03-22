# API Reference

## FMPClient

The main entry point. Inherits from 27 endpoint mixins and provides query building, data sync, and cache management.

### Constructor

```python
FMPClient(
    api_key: str | None = None,
    *,
    cache_path: str | None = "~/.fmp/cache.db",
    ttl_overrides: dict[str, int] | None = None,
    timeout: float = 30.0,
    max_retries: int = 3,
    rate_limit: float | None = 10.0,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | FMP API key. Falls back to `FMP_API_KEY` env var. |
| `cache_path` | `str \| None` | `"~/.fmp/cache.db"` | Path to DuckDB cache file. `None` for in-memory. |
| `ttl_overrides` | `dict[str, int] \| None` | `None` | Override default TTL (seconds) per category. |
| `timeout` | `float` | `30.0` | HTTP request timeout in seconds. |
| `max_retries` | `int` | `3` | Max retry attempts on HTTP 429. |
| `rate_limit` | `float \| None` | `10.0` | Max requests/second. `5` for free-tier, `30` for premium, `None` for unlimited. |

```python
from fmp import FMPClient

# Basic usage (uses FMP_API_KEY env var)
client = FMPClient()

# Explicit API key, custom rate limit
client = FMPClient("your_api_key", rate_limit=5)

# In-memory cache (no disk persistence)
client = FMPClient(cache_path=None)

# Override TTLs
client = FMPClient(ttl_overrides={
    "realtime_quotes": 30,        # refresh quotes every 30s
    "financial_statements": 86400, # refresh financials daily
})

# Context manager for auto-cleanup
with FMPClient() as client:
    data = client.quote("AAPL")
```

### Query builder

#### `client.query() -> QueryBuilder`

Start building a cross-dataset query. Returns a `QueryBuilder` instance.

```python
df = (client.query()
    .symbols("AAPL", "MSFT")
    .select("close", "revenue", "gross_profit_margin")
    .date_range("2023-01-01", "2024-12-31")
    .execute()
)
```

### Sync methods

#### `client.sync(**kwargs) -> dict[str, int]`

Sync data from the FMP API into the local DuckDB store.

```python
client.sync(
    symbols: list[str] | None = None,
    datasets: list[str] | None = None,
    start: str | None = None,           # "YYYY-MM-DD"
    end: str | None = None,             # "YYYY-MM-DD"
    period: str = "annual",             # "annual" or "quarter"
    use_bulk: bool = True,
    max_workers: int = 10,
    on_progress: Callable[[str, str], None] | None = None,
) -> dict[str, int]  # {dataset_name: rows_written}
```

```python
# Sync specific symbols and datasets
result = client.sync(
    symbols=["AAPL", "MSFT"],
    datasets=["daily_price", "income_statement", "balance_sheet"],
    start="2020-01-01", end="2024-12-31",
    on_progress=lambda ds, msg: print(f"[{ds}] {msg}"),
)
print(result)
# {'daily_price': 2520, 'income_statement': 40, 'balance_sheet': 40}
```

#### `client.sync_all(**kwargs) -> dict[str, int]`

Bulk-load ALL financial data via bulk endpoints. One API call per dataset per year.

```python
client.sync_all(
    years: list[int] | None = None,   # default: last 5 years
    period: str = "annual",
    on_progress: Callable[[str, str], None] | None = None,
) -> dict[str, int]
```

```python
# Load 5 years of all financial data for the entire market
result = client.sync_all(years=[2020, 2021, 2022, 2023, 2024])
```

#### `client.sync_universe(universe, **kwargs) -> dict[str, int]`

Fetch constituents of an index, then sync all their data.

```python
client.sync_universe(
    universe: str = "sp500",          # "sp500", "nasdaq", or "dowjones"
    datasets: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
    period: str = "annual",
    max_workers: int = 10,
    on_progress: Callable[[str, str], None] | None = None,
) -> dict[str, int]
```

```python
# Sync all S&P 500 data
result = client.sync_universe("sp500", start="2020-01-01", end="2024-12-31")
```

#### `client.estimate_sync_calls(**kwargs) -> dict[str, int]`

Estimate API calls needed for a sync without making any.

```python
client.estimate_sync_calls(
    symbols: list[str] | None = None,
    datasets: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, int]  # includes "_total" key
```

```python
est = client.estimate_sync_calls(
    symbols=["AAPL", "MSFT"],
    datasets=["daily_price", "income_statement"],
    start="2020-01-01", end="2024-12-31",
)
print(f"Total API calls: {est['_total']}")
```

### Bulk helpers

#### `client.fetch_many(method, symbols, **kwargs) -> dict[str, list[dict]]`

Call an endpoint method for multiple symbols concurrently.

```python
results = client.fetch_many(
    method: Callable,
    symbols: list[str],
    max_workers: int = 10,
    **kwargs,
) -> dict[str, list[dict]]  # keyed by symbol
```

```python
# Fetch quotes for 100 symbols concurrently
results = client.fetch_many(client.quote, ["AAPL", "MSFT", "GOOG", ...])
for sym, data in results.items():
    print(f"{sym}: ${data[0]['price']}")
```

#### `client.paginate_all(method, **kwargs) -> list[dict]`

Auto-paginate a paginated endpoint until exhausted.

```python
all_news = client.paginate_all(
    method: Callable,
    limit: int = 100,
    max_pages: int = 100,
    **kwargs,
) -> list[dict]
```

### Rate limit control

```python
# Get current rate limit
print(client.rate_limit)  # 10.0

# Change at runtime
client.rate_limit = 5    # slow down for free-tier
client.rate_limit = 30   # speed up for premium
client.rate_limit = None # unlimited (not recommended)
```

### Store access

#### `client.store -> BitemporalStore`

Direct access to the bitemporal store for advanced operations.

```python
# Check data freshness
is_fresh = client.store.is_fresh("daily_price", "AAPL", ttl=86400)

# Read raw data with dedup
rows = client.store.read("income_statement", ["AAPL"], start="2023-01-01")

# See all historical versions of a data point
versions = client.store.revisions("income_statement", "AAPL", date="2024-03-31")

# Compact old versions
deleted = client.store.compact("daily_price", keep_latest_n=1)

# Check row count
count = client.store.row_count("daily_price")
```

#### `client.revisions(symbol, dataset, **filters) -> list[dict]`

Convenience method to see how data changed across fetches.

```python
revisions = client.revisions("AAPL", "income_statement", date="2023-09-30", period="FY")
```

### Cache access

#### `client.cache -> DuckDBCache`

Direct access to the raw response cache.

#### `client.sql(query, params=None) -> list[dict]`

Execute arbitrary SQL against the cache database.

```python
# Query the typed tables directly
results = client.sql("SELECT symbol, date, revenue FROM income_statement LIMIT 10")

# Count cached entries
results = client.sql("SELECT COUNT(*) as n FROM _raw_cache")
```

#### `client.clear_cache(endpoint=None) -> int`

Clear cached entries. Returns the number of rows deleted.

```python
# Clear all cache
deleted = client.clear_cache()

# Clear cache for a specific endpoint
deleted = client.clear_cache("income-statement")
```

### Lifecycle

```python
client.close()  # Close HTTP and DuckDB connections

# Or use as context manager
with FMPClient() as client:
    ...
```

---

## QueryBuilder

Returned by `client.query()`. Fluent interface for building cross-dataset queries.

### Builder methods

All builder methods return `self` for chaining.

#### `.symbols(*syms: str | list[str]) -> QueryBuilder`

Set the symbols to query. Required.

```python
.symbols("AAPL", "MSFT")
.symbols(["AAPL", "MSFT", "GOOG"])
```

#### `.select(*fields: str) -> QueryBuilder`

Choose which fields to include. Required. Accepts base fields, derived features, post-compute features, and aliases.

```python
.select("close", "volume")                    # base fields
.select("gross_profit_margin", "altman_z_score")  # derived features
.select("ema_20", "beta_sp500")                # post-compute features
.select("pe_ratio")                             # alias for price_earnings_ratio
```

#### `.date_range(start: str, end: str) -> QueryBuilder`

Filter to a date range (inclusive). Format: `"YYYY-MM-DD"`.

```python
.date_range("2023-01-01", "2024-12-31")
```

#### `.grain(grain: str) -> QueryBuilder`

Set the output granularity. When omitted, the query builder picks the finest non-snapshot grain from the requested datasets.

Valid values: `"daily"`, `"weekly"`, `"monthly"`, `"quarterly"`, `"annual"`.

```python
.grain("monthly")  # roll up daily data to monthly
```

#### `.agg(**overrides: str) -> QueryBuilder`

Override default aggregation for specific fields when rolling up to a coarser grain.

Available aggregations: `"first"`, `"last"`, `"sum"`, `"mean"` / `"avg"`, `"max"`, `"min"`, `"median"`, `"count"`.

```python
.grain("monthly")
.agg(close="last", volume="sum", high="max", low="min")
```

#### `.force_refresh() -> QueryBuilder`

Bypass cache and re-fetch all data from the API.

#### `.auto_fetch(enabled: bool = True) -> QueryBuilder`

Control whether missing data is auto-fetched from the API. When `False`, queries only read from the local DuckDB store. Use `client.sync()` to populate the store first.

```python
# Offline query mode
.auto_fetch(False)
```

### Execute

#### `.execute(backend: str = "polars") -> DataFrame`

Run the query and return a DataFrame.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `str` | `"polars"` | `"polars"` (zero-copy via Arrow) or `"pandas"`. Post-compute features require polars. |

```python
# Polars DataFrame (default, recommended)
df = query.execute()

# Pandas DataFrame
df = query.execute(backend="pandas")
```

**Raises:**
- `FMPError` if no symbols specified
- `FMPError` if no fields specified
- `FMPError` for unknown field names
- `FMPError` if post-compute features used with `backend="pandas"`

### Complete example

```python
df = (client.query()
    .symbols("AAPL", "MSFT", "GOOG")
    .select(
        "close", "volume",                # daily price
        "revenue", "net_income",           # quarterly financials (ASOF joined)
        "gross_profit_margin",             # derived: profitability
        "revenue_growth_yoy",              # derived: growth (uses LAG)
        "altman_z_score",                  # derived: composite model
        "ema_20", "macd_line",             # post-compute: technical
        "beta_sp500",                      # post-compute: cross-asset risk
        "rate_10y",                        # macro: treasury rates (date-only join)
    )
    .date_range("2023-01-01", "2024-12-31")
    .execute()
)
```

---

## BitemporalStore

Append-only typed DuckDB storage. Access via `client.store`.

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `write` | `(dataset: str, rows: list[dict]) -> int` | Append rows with `_fetched_at = now()`. Returns row count. |
| `read` | `(dataset: str, symbols: list[str], start?, end?, columns?) -> list[dict]` | Read latest version of each row (QUALIFY dedup). |
| `is_fresh` | `(dataset: str, symbol: str \| None, ttl: int) -> bool` | Check if data was fetched within TTL seconds. |
| `has_data` | `(dataset: str, symbol: str \| None, start?, end?) -> bool` | Check if any data exists (no TTL). |
| `has_bulk_data` | `(dataset: str, year: int) -> bool` | Check if bulk data for a year has been loaded. |
| `symbols_with_data` | `(dataset: str) -> list[str]` | List all symbols with data in a dataset. |
| `revisions` | `(dataset: str, symbol: str, **filters) -> list[dict]` | Return all historical versions ordered by fetch time. |
| `compact` | `(dataset: str, keep_latest_n: int = 1) -> int` | Delete old versions. Returns rows deleted. |
| `row_count` | `(dataset: str) -> int` | Total rows in the table. |

---

## Configuration

### Default TTLs (`_config.py`)

TTL values control how long cached data is considered fresh. Override at client init via `ttl_overrides`.

| Category | Default TTL | Duration |
|----------|-------------|----------|
| `realtime_quotes` | 60 | 1 minute |
| `aftermarket` | 60 | 1 minute |
| `intraday_charts` | 300 | 5 minutes |
| `daily_historical` | 86,400 | 24 hours |
| `financial_statements` | 604,800 | 7 days |
| `company_profiles` | 86,400 | 24 hours |
| `key_metrics` | 604,800 | 7 days |
| `news` | 900 | 15 minutes |
| `earnings_calendar` | 21,600 | 6 hours |
| `sec_filings` | 86,400 | 24 hours |
| `insider_trades` | 3,600 | 1 hour |
| `economic_indicators` | 86,400 | 24 hours |
| `analyst` | 86,400 | 24 hours |
| `screener` | 600 | 10 minutes |
| `bulk_data` | 86,400 | 24 hours |
| `static_lists` | 2,592,000 | 30 days |
| `esg` | 604,800 | 7 days |
| `senate` | 3,600 | 1 hour |
| `dcf` | 86,400 | 24 hours |
| `transcripts` | 604,800 | 7 days |
| `default` | 3,600 | 1 hour (fallback) |

---

## Exceptions

All exceptions inherit from `FMPError`.

```
FMPError
  +-- AuthenticationError   (HTTP 401 -- invalid API key)
  +-- ForbiddenError        (HTTP 403 -- plan limit exceeded)
  +-- RateLimitError        (HTTP 429 -- after retries exhausted)
  +-- NotFoundError         (HTTP 404 -- endpoint not found)
  +-- ServerError           (HTTP 5xx -- server-side error)
```

### FMPError

```python
class FMPError(Exception):
    status_code: int | None
    response: dict | None
```

```python
from fmp import FMPError, AuthenticationError, RateLimitError

try:
    data = client.quote("AAPL")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited (status {e.status_code})")
except FMPError as e:
    print(f"FMP error: {e} (status {e.status_code})")
```

---

## Utility functions

These are importable directly from `fmp`:

### `list_fields(dataset: str | None = None) -> list[str]`

List available field names. Without an argument, returns all queryable names (base + derived + post-compute). With a dataset name, returns only that dataset's base fields.

```python
from fmp import list_fields

# All queryable fields
all_fields = list_fields()  # ~500+ names

# Fields for a specific dataset
list_fields("daily_price")
# ['open', 'high', 'low', 'close', 'adj_close', 'volume', 'vwap', 'change', 'change_pct']

list_fields("income_statement")
# ['reported_currency', 'cik', 'filling_date', 'revenue', 'cost_of_revenue', ...]
```

### `list_features(category: str | None = None) -> list[str]`

List available derived and post-compute feature names. Optionally filter by category.

```python
from fmp import list_features

# All 362 features
all_features = list_features()

# Filter by category
list_features("composite")
# ['altman_z_score', 'altman_z_prime', 'piotroski_f_score', 'beneish_m_score', ...]
```

### `feature_categories() -> list[str]`

List all feature category names.

```python
from fmp import feature_categories

categories = feature_categories()
# ['analyst', 'cash_flow', 'composite', 'dividend', 'dupont',
#  'earnings_quality', 'efficiency', 'esg', 'event_driven',
#  'growth', 'historical', 'index_membership', 'insider',
#  'institutional', 'leverage', 'liquidity', 'macro', 'momentum',
#  'per_share', 'profitability', 'risk', 'senate', 'technical',
#  'valuation']
```

### `Grain`

Enum for temporal granularity. Used with `QueryBuilder.grain()`.

```python
from fmp import Grain

Grain.DAILY      # 1
Grain.WEEKLY     # 2
Grain.MONTHLY    # 3
Grain.QUARTERLY  # 4
Grain.ANNUAL     # 5
Grain.SNAPSHOT   # 99

# Parse from string
Grain.parse("monthly")  # Grain.MONTHLY
```

---

## Available datasets

For reference, here are all 27 registered datasets:

| Dataset | Endpoint | Grain | Keys |
|---------|----------|-------|------|
| `daily_price` | `historical-price-eod/full` | daily | symbol, date |
| `income_statement` | `income-statement` | quarterly | symbol, date, period |
| `balance_sheet` | `balance-sheet-statement` | quarterly | symbol, date, period |
| `cash_flow` | `cash-flow-statement` | quarterly | symbol, date, period |
| `key_metrics` | `key-metrics` | quarterly | symbol, date, period |
| `ratios` | `ratios` | quarterly | symbol, date, period |
| `quote` | `quote` | snapshot | symbol |
| `profile` | `profile` | snapshot | symbol |
| `earnings_data` | `earnings` | quarterly | symbol, date |
| `dividends_data` | `dividends` | quarterly | symbol, date |
| `enterprise_values` | `enterprise-values` | quarterly | symbol, date |
| `treasury_rates` | `treasury-rates` | daily | date |
| `analyst_estimates` | `analyst-estimates` | quarterly | symbol, date |
| `price_target` | `price-target-consensus` | snapshot | symbol |
| `grades_consensus` | `grades-consensus` | snapshot | symbol |
| `ratings` | `ratings-snapshot` | snapshot | symbol |
| `employee_count` | `historical-employee-count` | annual | symbol, date |
| `shares_float_data` | `shares-float` | snapshot | symbol |
| `dcf_data` | `discounted-cash-flow` | snapshot | symbol |
| `esg_data` | `esg-environmental-social-governance-data` | snapshot | symbol |
| `price_change` | `stock-price-change` | snapshot | symbol |
| `splits_data` | `splits` | quarterly | symbol, date |
| `institutional_summary` | `institutional-ownership/symbol-positions-summary` | snapshot | symbol |
| `financial_scores` | `financial-scores` | snapshot | symbol |
| `historical_market_cap` | `historical-market-capitalization` | daily | symbol, date |
| `historical_grades` | `grades-historical` | monthly | symbol, date |
| `historical_ratings` | `ratings-historical` | monthly | symbol, date |
| `historical_institutional` | `institutional-ownership/symbol-positions-summary` | quarterly | symbol, date |
