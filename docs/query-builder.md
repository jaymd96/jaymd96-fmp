# Query Builder

The query builder is a fluent API for cross-dataset queries with automatic grain alignment, 315 SQL-derived features, and 30 post-compute features. It resolves field names to the correct API endpoints and DuckDB tables automatically.

## Basic Usage

```python
from fmp import FMPClient

client = FMPClient(api_key="...")

df = (
    client.query()
    .symbols("AAPL", "MSFT")
    .select("close", "volume", "revenue", "net_income")
    .date_range("2023-01-01", "2024-12-31")
    .execute()
)
```

This query:
1. Resolves `close` and `volume` to the `daily_price` dataset, and `revenue` and `net_income` to `income_statement`.
2. Fetches both datasets from the API (or reads from the local store if already synced).
3. Joins them with an ASOF JOIN -- quarterly income statement data is forward-filled to daily rows.
4. Returns a polars DataFrame.

## The Fluent API

All builder methods return `self`, so calls can be chained.

### `.symbols(*syms)` -- Set Symbols

Accepts individual strings or lists:

```python
# Individual symbols
.symbols("AAPL", "MSFT", "GOOG")

# From a list
sp500 = ["AAPL", "MSFT", ...]
.symbols(sp500)

# Mixed
.symbols("AAPL", other_symbols)
```

### `.select(*fields)` -- Choose Fields

Accepts any combination of base fields, SQL-derived features, and post-compute features:

```python
# Base fields (from API endpoints)
.select("close", "volume", "revenue", "total_assets")

# SQL-derived features (computed in DuckDB)
.select("gross_profit_margin", "return_on_equity", "debt_to_equity_ratio")

# Post-compute features (computed in polars after the SQL query)
.select("ema_20", "macd_line", "beta_sp500")

# Mix all three types freely
.select("close", "revenue", "gross_profit_margin", "ema_20", "beta_sp500")
```

Unknown field names raise `FMPError`.

### `.date_range(start, end)` -- Filter Dates

```python
.date_range("2020-01-01", "2024-12-31")
```

Both dates are inclusive. Format: `YYYY-MM-DD`.

### `.grain(grain)` -- Set Output Granularity

```python
.grain("daily")      # default -- finest grain
.grain("weekly")     # roll up daily data to weekly
.grain("monthly")    # roll up to monthly
.grain("quarterly")  # roll up to quarterly
.grain("annual")     # roll up to annual
```

When not set, the query builder picks the finest non-snapshot grain across all requested datasets (usually `daily`).

See [Grain Alignment](#grain-alignment) below for details on how data at different granularities is joined and rolled up.

### `.agg(**overrides)` -- Override Aggregations

When rolling up finer-grained data (e.g., daily to monthly), each field has a default aggregation function defined in the ontology. Override them per-field:

```python
.grain("monthly")
.agg(close="mean", volume="max", revenue="sum")
```

Supported aggregation functions:

| Function | SQL |
|---|---|
| `"first"` | `FIRST(col ORDER BY date)` |
| `"last"` | `LAST(col ORDER BY date)` |
| `"sum"` | `SUM(col)` |
| `"mean"` / `"avg"` | `AVG(col)` |
| `"max"` | `MAX(col)` |
| `"min"` | `MIN(col)` |
| `"median"` | `MEDIAN(col)` |
| `"count"` | `COUNT(col)` |

### `.auto_fetch(enabled)` -- Control API Access

```python
# Default: auto-fetch missing data from the API
.auto_fetch(True)

# Query from local store only (no API calls)
.auto_fetch(False)
```

Use `.auto_fetch(False)` after syncing data with `client.sync()` to ensure queries are pure-local.

### `.force_refresh()` -- Bypass Cache

```python
# Re-fetch all data from the API, ignoring what's already in the store
.force_refresh()
```

### `.execute(backend="polars")` -- Run the Query

```python
# Returns a polars DataFrame (default, recommended)
df = query.execute()
df = query.execute(backend="polars")

# Returns a pandas DataFrame
df = query.execute(backend="pandas")
```

**Note:** Post-compute features (EMA, MACD, beta, insider trade aggregations, etc.) require `backend="polars"`. Using `backend="pandas"` with post-compute features raises `FMPError`.

## Field Types

The query builder handles three types of fields:

### 1. Base Fields

Raw data columns from FMP API endpoints, stored in typed DuckDB tables. Examples:

- From `daily_price`: `open`, `high`, `low`, `close`, `volume`, `adj_close`, `vwap`
- From `income_statement`: `revenue`, `gross_profit`, `operating_income`, `net_income`, `ebitda`, `eps`
- From `balance_sheet`: `total_assets`, `total_liabilities`, `total_equity`, `cash_and_equivalents`
- From `cash_flow`: `operating_cash_flow`, `capital_expenditure`, `free_cash_flow`
- From `quote`: `price`, `market_cap`, `year_high`, `year_low`
- From `key_metrics`: `revenue_per_share`, `pe_ratio`, `book_value_per_share`
- From `treasury_rates`: `month_1`, `month_3`, `year_1`, `year_10`, `year_30`

Use `list_fields(dataset="daily_price")` to see all fields for a specific dataset, or `list_fields()` for all available fields.

### 2. SQL-Derived Features (315 features)

Computed as SQL expressions over base fields, executed inside DuckDB. These are defined declaratively with their dependencies -- the query builder automatically includes whatever base fields are needed.

Example: selecting `gross_profit_margin` automatically pulls `gross_profit` and `revenue` from the `income_statement` dataset and computes `gross_profit / NULLIF(revenue, 0)` in SQL.

**Categories (22):**

| Category | Examples |
|---|---|
| `profitability` | `gross_profit_margin`, `operating_profit_margin`, `net_profit_margin`, `ebitda_margin`, `roa`, `roe` |
| `liquidity` | `current_ratio`, `quick_ratio`, `cash_ratio`, `operating_cf_ratio` |
| `leverage` | `debt_to_equity_ratio`, `debt_to_assets_ratio`, `interest_coverage`, `equity_multiplier` |
| `efficiency` | `asset_turnover`, `inventory_turnover`, `receivables_turnover`, `payables_turnover` |
| `valuation` | `earnings_yield`, `fcf_yield`, `ev_to_ebitda`, `ev_to_revenue` |
| `cash_flow` | `fcf_margin`, `operating_cf_margin`, `capex_to_revenue`, `fcf_conversion` |
| `growth` | `revenue_growth_yoy`, `net_income_growth_yoy`, `eps_growth_yoy`, `asset_growth` |
| `dupont` | `dupont_roe`, `dupont_tax_burden`, `dupont_interest_burden`, `dupont_margin`, `dupont_turnover`, `dupont_leverage` |
| `earnings_quality` | `accruals_ratio`, `earnings_persistence`, `cash_flow_quality`, `operating_accruals` |
| `per_share` | `revenue_per_share_calc`, `ebitda_per_share`, `operating_cf_per_share_calc`, `tangible_book_per_share` |
| `dividend` | `dividend_coverage`, `retention_ratio`, `sustainable_growth_rate` |
| `risk` | `financial_leverage_ratio`, `operating_leverage`, `total_leverage`, `altman_z_score` |
| `technical` | `distance_52w_high`, `distance_52w_low`, `candlestick_range`, `intraday_return` |
| `momentum` | `return_1d`, `return_5d`, `return_21d`, `return_63d`, `return_252d`, `momentum_12_1` |
| `composite` | `piotroski_f_score`, `quality_score`, `value_score`, `growth_quality_score` |
| `analyst` | `analyst_upside`, `estimate_dispersion`, `estimate_revision_direction` |
| `macro` | `equity_risk_premium`, `real_yield_10y`, `yield_curve_slope`, `credit_spread_proxy` |
| `sector_relative` | `sector_relative_pe`, `sector_relative_margin`, `sector_relative_growth` |
| `event_driven` | `earnings_surprise_pct`, `post_earnings_drift_5d`, `split_adjusted_return` |
| `esg` | `esg_total`, `esg_momentum`, `governance_gap` |
| `institutional` | `institutional_ownership_change`, `ownership_concentration`, `top10_holder_pct` |
| `historical` | `grade_trend_score`, `rating_percentile`, `market_cap_rank_pct` |

### 3. Post-Compute Features (30 features)

Computed in polars after the SQL query returns. These handle cases that cannot be expressed as single-pass SQL: recursive calculations (EMA), nested window functions (autocorrelation), cumulative conditional logic (dividend streaks), and cross-asset joins (beta).

| Feature | Category | Description |
|---|---|---|
| `ema_12`, `ema_20`, `ema_26`, `ema_50`, `ema_200` | `technical` | Exponential moving averages |
| `macd_line`, `macd_signal`, `macd_histogram` | `technical` | MACD indicator components |
| `return_autocorrelation_21d` | `momentum` | 21-day rolling return autocorrelation |
| `consecutive_dividend_increases` | `dividend` | Streak of consecutive dividend increases |
| `beta_sp500` | `risk` | 252-day rolling beta vs S&P 500 |
| `alpha_jensen` | `risk` | Jensen's alpha (CAPM-based) |
| `in_sp500`, `in_nasdaq`, `in_dowjones` | `index_membership` | Index membership flags |
| `insider_net_buying_90d` | `insider` | Net insider buying ($) over 90 days |
| `insider_buy_count_30d`, `insider_sell_count_30d` | `insider` | Insider buy/sell transaction counts |
| `insider_buy_sell_ratio_90d` | `insider` | Buy/sell ratio over 90 days |
| `insider_buying_cluster` | `insider` | 3+ unique insiders buying in 30 days |
| `insider_total_bought_90d`, `insider_total_sold_90d` | `insider` | Total insider $ bought/sold |
| `insider_officer_buying` | `insider` | Officer/director buying flag |
| `senate_buy_count_90d`, `senate_sell_count_90d` | `senate` | Senate buy/sell counts |
| `senate_net_flow_90d` | `senate` | Net senate trade flow |
| `senate_activity_flag` | `senate` | Any senate trade in 30 days |
| `upgrades_90d`, `downgrades_90d` | `analyst` | Analyst upgrade/downgrade counts |
| `upgrade_downgrade_ratio` | `analyst` | Upgrade-to-downgrade ratio |

Post-compute features that reference external data (like `beta_sp500`) automatically fetch the required reference symbols (e.g., `^GSPC`) during query execution.

**Important:** Post-compute features require `backend="polars"`. Using them with `backend="pandas"` raises an error.

## Grain Alignment

Datasets have different temporal granularities (grains). The query builder handles alignment automatically.

### Grains in the Ontology

| Grain | Value | Examples |
|---|---|---|
| `DAILY` | 1 | `daily_price`, `dividends_data`, `treasury_rates` |
| `QUARTERLY` | 4 | `income_statement`, `balance_sheet`, `cash_flow`, `key_metrics` |
| `ANNUAL` | 5 | `analyst_estimates`, `employee_count` |
| `SNAPSHOT` | 99 | `quote`, `profile`, `dcf_data` |

### How Alignment Works

**Coarser to finer (ASOF JOIN):** When quarterly data is joined to daily data, the query builder uses an ASOF JOIN. Each daily row picks up the most recent quarterly value at or before that date. This effectively forward-fills quarterly data across daily rows.

```python
# Daily close with quarterly revenue -- revenue is forward-filled
df = (
    client.query()
    .symbols("AAPL")
    .select("close", "revenue")
    .date_range("2023-01-01", "2024-12-31")
    .execute()
)
# Result: daily rows. 'close' changes every day.
# 'revenue' changes quarterly and is carried forward.
```

**Finer to coarser (rollup aggregation):** When the output grain is coarser than the data grain, the query builder rolls up using each field's default aggregation function (defined in the ontology). For example, `close` defaults to `"last"`, `volume` defaults to `"sum"`.

```python
# Monthly rollup of daily data
df = (
    client.query()
    .symbols("AAPL")
    .select("close", "volume")
    .date_range("2023-01-01", "2024-12-31")
    .grain("monthly")
    .execute()
)
# Result: monthly rows.
# 'close' = last close of each month. 'volume' = sum of daily volume.
```

**Same grain (equi-join):** Datasets at the same grain are joined on `(symbol, date)`.

**Snapshot data (symbol-only join):** Snapshot datasets (like `quote`) have no date key and are joined on `symbol` only. Every row gets the same snapshot values.

### Overriding Default Aggregations

Each base field has a default aggregation function (`last`, `sum`, `mean`, etc.) defined in the ontology. Override them with `.agg()`:

```python
# Default: close uses "last", volume uses "sum"
# Override: get average close and max volume per month
df = (
    client.query()
    .symbols("AAPL")
    .select("close", "volume")
    .date_range("2023-01-01", "2024-12-31")
    .grain("monthly")
    .agg(close="mean", volume="max")
    .execute()
)
```

## Field Discovery

### `list_fields()` -- All Available Fields

```python
from fmp import list_fields

# All fields (base + derived + post-compute)
all_fields = list_fields()
print(f"{len(all_fields)} fields available")

# Fields for a specific dataset
daily_fields = list_fields(dataset="daily_price")
income_fields = list_fields(dataset="income_statement")
```

### `list_features()` -- Derived Features Only

```python
from fmp import list_features, feature_categories

# All feature categories
categories = feature_categories()
# ['analyst', 'cash_flow', 'composite', 'dividend', 'dupont', ...]

# All features
all_features = list_features()

# Features in a specific category
momentum = list_features(category="momentum")
# ['return_1d', 'return_5d', 'return_21d', 'return_63d', ...]
```

## Example Queries

### Price and Fundamentals Panel

```python
df = (
    client.query()
    .symbols("AAPL", "MSFT", "GOOG", "AMZN", "META")
    .select(
        "close", "volume",
        "revenue", "net_income", "free_cash_flow",
        "gross_profit_margin", "net_profit_margin", "roe",
    )
    .date_range("2020-01-01", "2024-12-31")
    .execute()
)
```

### Monthly Momentum Screen

```python
df = (
    client.query()
    .symbols("AAPL", "MSFT", "GOOG")
    .select("close", "return_21d", "return_63d", "return_252d", "ema_50")
    .date_range("2023-01-01", "2024-12-31")
    .grain("monthly")
    .agg(close="last")
    .execute()
)
```

### Quality + Value Composite

```python
df = (
    client.query()
    .symbols("AAPL", "MSFT")
    .select(
        "piotroski_f_score", "quality_score", "value_score",
        "altman_z_score", "earnings_yield", "fcf_yield",
    )
    .date_range("2020-01-01", "2024-12-31")
    .grain("quarterly")
    .execute()
)
```

### Risk and Beta Analysis

```python
df = (
    client.query()
    .symbols("AAPL", "TSLA", "JPM")
    .select("close", "beta_sp500", "alpha_jensen", "return_252d")
    .date_range("2022-01-01", "2024-12-31")
    .execute()
)
# beta_sp500 automatically fetches ^GSPC as a reference symbol
```

### Insider Activity Screen

```python
df = (
    client.query()
    .symbols("AAPL", "MSFT", "GOOG")
    .select(
        "close",
        "insider_net_buying_90d",
        "insider_buying_cluster",
        "insider_officer_buying",
        "senate_activity_flag",
    )
    .date_range("2024-01-01", "2024-12-31")
    .execute()
)
```

### Offline Query After Sync

```python
# Sync once
client.sync(
    symbols=["AAPL", "MSFT"],
    datasets=["daily_price", "income_statement", "balance_sheet", "ratios"],
    start="2015-01-01",
    end="2024-12-31",
)

# Query repeatedly without API calls
for year in range(2015, 2025):
    df = (
        client.query()
        .symbols("AAPL", "MSFT")
        .select("close", "revenue", "gross_profit_margin", "current_ratio")
        .date_range(f"{year}-01-01", f"{year}-12-31")
        .auto_fetch(False)
        .execute()
    )
    print(f"{year}: {df.shape[0]} rows")
```

### Macro Overlay (Treasury Rates)

```python
df = (
    client.query()
    .symbols("AAPL")
    .select("close", "year_10", "yield_curve_slope", "equity_risk_premium")
    .date_range("2023-01-01", "2024-12-31")
    .execute()
)
# treasury_rates (date-only dataset) is joined on date without a symbol key
```

### Pandas Backend

```python
# Note: post-compute features (EMA, MACD, beta) are NOT available with pandas
df = (
    client.query()
    .symbols("AAPL")
    .select("close", "revenue", "gross_profit_margin")
    .date_range("2023-01-01", "2024-12-31")
    .execute(backend="pandas")
)
# Returns a pandas DataFrame
```
