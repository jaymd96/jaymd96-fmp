# Architecture Guide

## High-level overview

```
                     User Code
                        |
                  FMPClient (client.py)
                  /     |     \
                 /      |      \
    Endpoint     Query    Sync
    Mixins      Builder  Manager
     (27)         |        |
       \          |        |
        v         v        v
      HTTPClient -----> BitemporalStore
        |                   |
        |                   v
        |              DuckDB (typed tables)
        |                   |
        v                   v
     FMP API           DuckDBCache
   (stable/)          (_raw_cache table)

                  Feature System
                  /            \
         DerivedFieldDef    PostComputeFieldDef
         (SQL expressions)   (polars transforms)
                  \            /
                   v          v
                 QueryBuilder.execute()
                       |
                       v
                 polars / pandas DataFrame
```

## Layer-by-layer

### HTTP layer (`_http.py`)

**`HTTPClient`** wraps `httpx.Client` with authentication, retry logic, and rate limiting.

- Base URL: `https://financialmodelingprep.com/stable/`
- Auth: API key passed as `apikey` header
- Retry: exponential backoff on HTTP 429 (rate limit), up to `max_retries` attempts (default 3)
- Rate limiting: `TokenBucket` token-bucket algorithm, default 10 req/sec
- CSV auto-detection: bulk endpoints return CSV; the client detects this via `Content-Type` header or leading `"` character and parses automatically
- Error mapping: HTTP status codes map to typed exceptions (`AuthenticationError`, `ForbiddenError`, `RateLimitError`, `NotFoundError`, `ServerError`)

```python
class TokenBucket:
    """Thread-safe token-bucket rate limiter."""
    def acquire(self) -> None:
        """Block until a token is available."""
```

### Cache layer (`_cache.py`)

**`DuckDBCache`** provides a simple key-value cache for raw API responses using a `_raw_cache` table in DuckDB.

```sql
CREATE TABLE IF NOT EXISTS _raw_cache (
    cache_key   VARCHAR PRIMARY KEY,
    endpoint    VARCHAR NOT NULL,
    params_json VARCHAR,
    response    JSON NOT NULL,
    fetched_at  TIMESTAMP NOT NULL DEFAULT now(),
    ttl_seconds INTEGER NOT NULL
);
```

Every endpoint mixin method calls `_request()`, which checks this cache first. Cache keys are derived from `endpoint:param1=val1:param2=val2`. TTLs are configurable per category (see `_config.py` for defaults).

This is the **v0.1 cache** -- it caches raw API responses for the endpoint mixin methods (`.quote()`, `.income_statement()`, etc.). The bitemporal store is a separate, more sophisticated system for the query builder.

### Bitemporal Store (`_store.py`)

**`BitemporalStore`** is an append-only typed DuckDB storage layer generated from the ontology. Every row gets a `_fetched_at` timestamp on write.

**Append-only writes:**
```python
def write(self, dataset: str, rows: list[dict]) -> int:
    """Translate camelCase API fields to snake_case columns. Append rows."""
```

**Bitemporal reads with QUALIFY dedup:**
```python
def read(self, dataset: str, symbols: list[str], ...) -> list[dict]:
    """Read latest version of each row using QUALIFY ROW_NUMBER()."""
```

The deduplication query:
```sql
SELECT columns
FROM dataset
WHERE symbol IN (?) AND date >= ? AND date <= ?
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY symbol, date, period
    ORDER BY _fetched_at DESC
) = 1
ORDER BY symbol, date
```

**Key operations:**
- `write()` -- append rows with `_fetched_at = now()`
- `read()` -- deduplicated latest-version read
- `is_fresh()` -- TTL-based freshness check
- `has_data()` -- existence check (no TTL, used by sync)
- `revisions()` -- return all historical versions of a row
- `compact()` -- delete old versions, keeping latest N

**Thread safety:** All writes are protected by a `threading.Lock()`.

### Ontology (`_ontology.py`)

The ontology is the declarative schema that drives everything else. It defines:

**`Grain`** -- temporal granularity hierarchy:
```python
class Grain(IntEnum):
    INTRADAY  = 0
    DAILY     = 1
    WEEKLY    = 2
    MONTHLY   = 3
    QUARTERLY = 4
    ANNUAL    = 5
    SNAPSHOT  = 99  # outside the hierarchy
```

**`FieldDef`** -- a single column in a dataset:
```python
@dataclass(frozen=True, slots=True)
class FieldDef:
    name: str       # snake_case column name in DuckDB
    api_name: str   # camelCase field name in API response
    dtype: str      # DuckDB type: DOUBLE, BIGINT, VARCHAR, DATE
    agg: str        # default rollup: first, last, sum, mean, max, min
```

**`DatasetDef`** -- a logical dataset backed by one FMP endpoint:
```python
@dataclass(frozen=True, slots=True)
class DatasetDef:
    name: str                      # table name in DuckDB
    endpoint: str                  # FMP API path
    grain: Grain                   # temporal granularity
    keys: tuple[str, ...]          # primary key columns
    ttl_category: str              # maps to DEFAULT_TTLS
    fields: dict[str, FieldDef]    # columns
```

**27 datasets** are registered, including:
- `daily_price` (daily) -- OHLCV
- `income_statement`, `balance_sheet`, `cash_flow` (quarterly) -- financial statements
- `key_metrics`, `ratios` (quarterly) -- FMP-computed ratios
- `quote`, `profile` (snapshot) -- real-time and static company data
- `treasury_rates` (daily, no symbol key) -- macro data
- `historical_market_cap` (daily) -- point-in-time market cap
- `historical_grades`, `historical_ratings` (monthly) -- point-in-time analyst data
- `historical_institutional` (quarterly) -- point-in-time 13F data

**`FIELD_REGISTRY`** -- global index from field name to `(dataset_name, FieldDef)`. First dataset to register a name wins.

**`_ALIASES`** -- convenient short names (`pe_ratio` -> `price_earnings_ratio`, `dividend_yield` -> `dividend_yield_r`, etc.)

**`resolve_fields()`** -- given a list of field names, returns a dict of `{dataset_name: [FieldDef, ...]}`.

### Sync Manager (`_sync.py`)

**`SyncManager`** handles bulk data loading from the FMP API into the bitemporal store, choosing the most efficient strategy for each dataset:

| Strategy | Datasets | API calls |
|----------|----------|-----------|
| Bulk yearly | `income_statement`, `balance_sheet`, `cash_flow`, `key_metrics`, `ratios` | 1 per year for ALL symbols |
| Bulk paginated | `profile` | ~10 pages for ALL symbols |
| Date-only | `treasury_rates` | 1 call total |
| Per-symbol timeseries | `daily_price`, `enterprise_values`, `earnings_data`, `dividends_data`, `analyst_estimates`, `historical_market_cap`, `historical_grades`, `historical_ratings` | 1 per symbol |
| Per-symbol snapshot | `quote`, `dcf_data`, `esg_data`, `price_change`, `institutional_summary`, `price_target`, `grades_consensus`, `ratings`, `shares_float_data`, `financial_scores` | 1 per symbol |
| Multi-period | `historical_institutional` | symbols x quarters |

**Key methods:**
- `sync()` -- sync specific symbols/datasets
- `sync_all()` -- bulk-load entire market via bulk endpoints
- `sync_universe()` -- fetch constituents of an index, then sync all their data
- `estimate_calls()` -- estimate API calls without making any

Per-symbol fetches run concurrently with `ThreadPoolExecutor` (default 10 workers).

### Query Builder (`_query.py`)

**`QueryBuilder`** is a fluent builder that generates cross-dataset SQL queries with automatic grain alignment.

**Builder methods:**
```python
(client.query()
    .symbols("AAPL", "MSFT")           # which symbols
    .select("close", "revenue", "pe")   # which fields
    .date_range("2023-01-01", "2024-12-31")  # date filter
    .grain("monthly")                   # output granularity
    .agg(close="last", volume="sum")    # override aggregations
    .force_refresh()                    # bypass cache
    .auto_fetch(False)                  # query-only, no API calls
    .execute(backend="polars")          # run it
)
```

**Execution pipeline:**

1. **Field classification** -- split requested fields into base, SQL-derived, and post-compute
2. **Dependency resolution** -- derived features declare base field dependencies; those are added to the query
3. **Dataset grouping** -- base fields are grouped by dataset via `resolve_fields()`
4. **Grain resolution** -- pick the finest non-snapshot grain, or use explicit `.grain()`
5. **Data fetch** -- fetch missing data into the bitemporal store (concurrent, with bulk optimisation)
6. **SQL generation** -- build CTE-based query with dedup, alignment, and derived expressions
7. **Execution** -- run SQL against DuckDB
8. **Post-compute** -- apply polars-based transforms (EMA, MACD, beta, etc.)

### Feature System (`_features/`)

Two feature types:

**`DerivedFieldDef`** -- SQL expression computed inline in the generated query:
```python
@dataclass(frozen=True, slots=True)
class DerivedFieldDef:
    name: str              # "gross_profit_margin"
    expression: str        # "gross_profit / NULLIF(revenue, 0)"
    dependencies: tuple[str, ...]  # ("gross_profit", "revenue")
    dtype: str             # "DOUBLE"
    category: str          # "profitability"
    requires_lag: bool     # True if uses LAG/LEAD window functions
```

**`PostComputeFieldDef`** -- polars function applied after SQL:
```python
@dataclass(frozen=True)
class PostComputeFieldDef:
    name: str                          # "ema_20"
    compute_fn: Callable               # (df, ctx) -> polars.Series
    dependencies: tuple[str, ...]      # ("close",)
    category: str                      # "technical"
    reference_symbols: tuple[str, ...] # ("^GSPC",) for beta
```

Features are organised in category modules (`profitability.py`, `growth.py`, etc.), each exporting a `FEATURES` list. The `__init__.py` aggregates them into `DERIVED_REGISTRY` and `_ALL_FEATURES`.

## The ontology-driven design

Everything flows from `DatasetDef`. A single dataset definition:
- Creates the DuckDB table schema (`BitemporalStore._ddl()`)
- Maps API field names to column names (camelCase -> snake_case)
- Determines fetch strategy (grain, endpoint, TTL category)
- Controls grain alignment in queries (ASOF JOIN for coarse -> fine)
- Provides default aggregation functions for roll-up (fine -> coarse)

Adding a new FMP endpoint to the system requires only adding a `DatasetDef` to the ontology. The store, sync, and query layers adapt automatically.

## Mixin composition pattern

`FMPClient` inherits from 27 endpoint mixins:

```python
class FMPClient(
    SearchMixin, DirectoryMixin, CompanyMixin, QuotesMixin,
    FinancialsMixin, ChartsMixin, EconomicsMixin, EarningsMixin,
    TranscriptsMixin, NewsMixin, InstitutionalMixin, AnalystMixin,
    MarketPerformanceMixin, TechnicalMixin, ETFFundsMixin,
    SECFilingsMixin, InsiderMixin, IndexesMixin, MarketHoursMixin,
    CommoditiesMixin, DCFMixin, ForexMixin, CryptoMixin,
    SenateMixin, ESGMixin, COTMixin, FundraisersMixin, BulkMixin,
):
```

Each mixin provides methods for a group of related API endpoints. They all delegate to `self._request()` on `FMPClient`, which handles caching and HTTP.

This pattern keeps each endpoint group in its own file while presenting a single unified client API.

## Bitemporal storage explained

The store maintains two time dimensions:

1. **Valid time** (`date` column) -- when the data point is effective (e.g., 2024-03-31 for Q1 financials)
2. **Transaction time** (`_fetched_at` column) -- when the data was fetched from the API

This enables:

**Deduplication:** Multiple fetches of the same data point produce multiple rows. `QUALIFY ROW_NUMBER() ... ORDER BY _fetched_at DESC` always returns the latest version.

**Revision history:** `store.revisions("AAPL", "income_statement", date="2024-03-31")` returns all versions of that row, showing how restated financials evolved.

**Compaction:** `store.compact("income_statement", keep_latest_n=1)` deletes old versions to reclaim space.

**Example:** If AAPL restates Q1 2024 revenue, fetching the income statement again creates a new row with a later `_fetched_at`. Queries automatically see the restated value; `revisions()` shows both versions.

## SQL generation pipeline

The query builder generates CTE-based SQL. Here is a simplified trace for a query that selects `close` (daily) and `revenue` (quarterly):

```sql
-- Step 1: Dedup CTEs (one per dataset)
WITH daily_price_dedup AS (
    SELECT symbol, date, close
    FROM daily_price
    WHERE symbol IN ('AAPL') AND date >= '2024-01-01' AND date <= '2024-12-31'
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY symbol, date
        ORDER BY _fetched_at DESC
    ) = 1
),
income_statement_dedup AS (
    SELECT symbol, date, period, revenue
    FROM income_statement
    WHERE symbol IN ('AAPL') AND date <= '2024-12-31'
    -- Note: no start-date filter -- ASOF JOIN needs preceding data
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY symbol, date, period
        ORDER BY _fetched_at DESC
    ) = 1
)

-- Step 2: ASOF JOIN aligns quarterly to daily
SELECT t0.symbol, t0.date, t0.close, t1.revenue
FROM daily_price_dedup t0
ASOF JOIN income_statement_dedup t1
  ON t0.symbol = t1.symbol AND t0.date >= t1.date
ORDER BY t0.symbol, t0.date
```

**Key decisions in SQL generation:**

- **Anchor dataset:** the dataset matching the target grain becomes the driving table
- **ASOF JOIN:** coarser datasets (quarterly -> daily) are joined with `ASOF JOIN ... AND anchor.date >= other.date`, carrying forward the most recent value
- **Roll-up aggregation:** finer datasets (daily -> monthly) are aggregated with `DATE_TRUNC` and each field's default `agg` function (configurable via `.agg()`)
- **Snapshot datasets:** joined on symbol only (no date)
- **Date-only datasets:** (e.g., `treasury_rates`) joined on date only
- **Derived expressions:** added to the SELECT as `(expression) AS name`
- **Window clause:** added when any derived feature uses `LAG`/`LEAD` (`WINDOW w AS (PARTITION BY symbol ORDER BY date)`)

## Field alias system

Aliases let users reference fields by intuitive names:

```python
_ALIASES = {
    "pe_ratio":          "price_earnings_ratio",
    "dividend_yield":    "dividend_yield_r",
    "debt_to_equity":    "debt_equity_ratio",
    "book_value_per_share": "book_value_per_share_r",
    ...
}
```

Aliases are registered in `FIELD_REGISTRY` pointing to the same `(dataset, FieldDef)` as their target. This means `.select("pe_ratio")` works identically to `.select("price_earnings_ratio")`.

## Thread safety

- **`TokenBucket`** (`_http.py`) -- thread-safe rate limiter with `threading.Lock()`
- **`BitemporalStore`** (`_store.py`) -- all writes protected by `threading.Lock()`
- **`SyncManager`** and **`QueryBuilder`** -- use `ThreadPoolExecutor` for concurrent API calls, with thread-safe write operations

The DuckDB connection itself is single-threaded (one connection per client instance). Concurrent reads/writes are serialised by the store lock.
