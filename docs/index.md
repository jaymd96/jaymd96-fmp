# jaymd96-fmp

Python client for the [Financial Modeling Prep](https://financialmodelingprep.com/) API with DuckDB persistence, an ontology-driven query builder, and 345 derived features.

## What This Package Does

`jaymd96-fmp` provides three layers on top of the FMP REST API:

1. **Direct endpoint access** -- 150+ typed methods covering quotes, financials, charts, news, SEC filings, insider trades, senate trades, ESG, and more. Responses are cached in DuckDB with configurable TTLs per endpoint category.

2. **Bulk data sync** -- Load financial data into a local DuckDB warehouse. Bulk endpoints fetch entire markets in a single API call per year. Per-symbol endpoints are fetched concurrently with built-in rate limiting.

3. **Query builder** -- A fluent API that joins across datasets with automatic grain alignment (ASOF JOINs, rollup aggregation), 315 SQL-derived features (profitability margins, DuPont decomposition, growth rates, momentum signals, etc.), and 30 post-compute features (EMA, MACD, beta, insider trade aggregations) -- all resolved from field names to API endpoints automatically.

## Installation

```bash
pip install jaymd96-fmp
```

Optional backends for the query builder:

```bash
pip install jaymd96-fmp polars   # recommended (zero-copy Arrow)
pip install jaymd96-fmp pandas   # alternative
```

## Quick Start

### Direct Endpoint Access

Every FMP endpoint has a corresponding method on `FMPClient`. Results are cached locally.

```python
from fmp import FMPClient

client = FMPClient(api_key="your-api-key")

# Real-time quote
client.quote("AAPL")

# Financial statements
client.income_statement("AAPL", period="quarter", limit=4)

# Historical prices
client.historical_price_eod_full("AAPL", from_date="2024-01-01", to_date="2024-12-31")

# Stock screener
client.screener(sector="Technology", market_cap_more_than=1_000_000_000)

# Concurrent fetching across many symbols
results = client.fetch_many(client.quote, ["AAPL", "MSFT", "GOOG", "AMZN"])
```

### Query Builder

The query builder lets you select fields by name -- base data fields, SQL-derived ratios, and post-compute indicators -- across any combination of datasets. The ontology resolves field names to the right API endpoints and DuckDB tables automatically.

```python
df = (
    client.query()
    .symbols("AAPL", "MSFT")
    .select("close", "revenue", "gross_profit_margin", "return_5d", "ema_20")
    .date_range("2023-01-01", "2024-12-31")
    .execute()
)
# Returns a polars DataFrame with daily rows, quarterly data forward-filled via ASOF JOIN
```

### Sync-Then-Query Workflow

For research workloads, sync data once into DuckDB, then query offline without hitting the API.

```python
# Step 1: Sync data (bulk endpoints minimize API calls)
client.sync(
    symbols=["AAPL", "MSFT", "GOOG"],
    datasets=["daily_price", "income_statement", "balance_sheet"],
    start="2020-01-01",
    end="2024-12-31",
)

# Step 2: Query from local store only (no API calls)
df = (
    client.query()
    .symbols("AAPL", "MSFT", "GOOG")
    .select("close", "volume", "revenue", "net_income", "net_profit_margin")
    .date_range("2020-01-01", "2024-12-31")
    .auto_fetch(False)
    .execute()
)
```

### Sync an Entire Universe

```python
# Sync the full S&P 500 -- bulk endpoints load entire market per API call
client.sync_universe(
    "sp500",
    start="2020-01-01",
    end="2024-12-31",
    on_progress=lambda ds, msg: print(f"[{ds}] {msg}"),
)
```

## Documentation

- [Getting Started](getting-started.md) -- installation, API key setup, configuration, rate limiting
- [Syncing Data](syncing-data.md) -- bulk sync, universe sync, API call optimization, progress callbacks
- [Query Builder](query-builder.md) -- fluent API, field types, grain alignment, aggregation overrides, field discovery
