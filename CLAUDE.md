# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
# Install in dev mode (creates .venv if needed)
uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_query.py

# Run a single test
pytest tests/test_query.py::test_single_dataset_daily

# Lint
ruff check src/ tests/

# Build
uv build

# Publish (requires PyPI token)
hatch publish
```

## Architecture

### Ontology-Driven Design

The entire system is driven by declarative schema definitions in `_ontology.py`. Every data flow — HTTP fetching, DuckDB storage, query generation, feature computation — follows these definitions. **Before changing anything, understand the `DatasetDef` it touches.**

Key types:
- `DatasetDef(name, endpoint, grain, keys, ttl_category, fields)` — maps an FMP endpoint to a typed DuckDB table
- `FieldDef(name, api_name, dtype, agg)` — maps a snake_case column to a camelCase API field with a default rollup aggregation
- `Grain` enum — `DAILY > QUARTERLY > SNAPSHOT` hierarchy controls how datasets join

There are 24 datasets and ~280 base fields in `FIELD_REGISTRY`. Field name collisions across datasets are handled by registration order (first wins) plus an alias system.

### Data Flow

```
sync() → HTTPClient.get() → BitemporalStore.write() → DuckDB typed tables
query() → resolve fields → fetch if needed → generate SQL → DuckDB → polars DataFrame
```

### Layer Responsibilities

| Layer | File | Role |
|---|---|---|
| Client | `client.py` | 27-mixin composition, exposes sync/query/endpoint methods |
| HTTP | `_http.py` | httpx wrapper, retry on 429, TokenBucket rate limiter, CSV auto-detection for bulk endpoints |
| Cache | `_cache.py` | `_raw_cache` table for v0.1 endpoint methods |
| Store | `_store.py` | Bitemporal typed tables (append-only, `_fetched_at` column, QUALIFY dedup) |
| Sync | `_sync.py` | Bulk loading strategies: BULK_YEARLY, BULK_PAGINATED, PER_SYMBOL_SNAPSHOT, etc. |
| Query | `_query.py` | Fluent builder → CTE-based SQL with grain alignment (ASOF JOIN, DATE_TRUNC rollup) |
| Ontology | `_ontology.py` | DatasetDef/FieldDef definitions, FIELD_REGISTRY, aliases |
| Features | `_features/*.py` | ~290 SQL-derived features + ~30 polars post-compute features |

### Endpoint Mixins (`_endpoints/`)

28 files, one per API category. Each is a class mixed into `FMPClient`. Pattern:
```python
def quote(self, symbol, *, force_refresh=False) -> list[dict]:
    return self._request("quote", params={"symbol": symbol},
                         ttl_category="realtime_quotes", force_refresh=force_refresh)
```
All delegate to `_request()` on the client. Adding a new endpoint = new mixin file + add to client's inheritance list.

### Feature System (`_features/`)

Three types of features, all accessible via `.select("feature_name")`:

1. **Base fields** — directly from API, stored in DuckDB (e.g., `close`, `revenue`)
2. **SQL-derived** (`DerivedFieldDef`) — SQL expressions over base fields, computed in DuckDB (e.g., `gross_profit_margin = gross_profit / NULLIF(revenue, 0)`)
3. **Post-compute** (`PostComputeFieldDef`) — computed in polars after SQL query returns, for recursive/cross-asset features (e.g., EMA, MACD, beta)

Derived features declare `dependencies` (base field names) so the query planner knows which datasets to fetch. Features using `LAG() OVER w` set `requires_lag=True` — the `w` placeholder is replaced with a WINDOW clause during SQL generation.

### Query Builder SQL Generation

`_generate_sql()` builds CTEs for each dataset with QUALIFY dedup, then joins them:
- Same grain → equi-join on `(symbol, date)`
- Daily + quarterly → ASOF JOIN (carry forward)
- Snapshot → LEFT JOIN on symbol only
- Date-only (treasury_rates) → LEFT JOIN on date only

Derived expressions get field names replaced with table aliases (`revenue` → `t1.revenue`) via regex substitution.

### Sync Strategies

`_sync.py` maps each dataset to its optimal fetch strategy:
- **BULK_YEARLY**: 1 API call per year for ALL symbols (income_statement, balance_sheet, cash_flow, key_metrics, ratios) — returns CSV
- **BULK_PAGINATED**: profile-bulk, ~4 pages for all symbols
- **PER_SYMBOL_TIMESERIES**: daily_price, earnings, dividends (no bulk available)
- **PER_SYMBOL_SNAPSHOT**: quote, dcf, ratings, etc.
- **EXTRA_PARAMS**: some endpoints need additional params (institutional needs year+quarter, analyst needs period)

FMP bulk endpoints return CSV (not JSON). The HTTP client auto-detects this via Content-Type header or leading quote character.

### Bitemporal Storage

`BitemporalStore` uses append-only writes (`_fetched_at = now()`). Reads use:
```sql
QUALIFY ROW_NUMBER() OVER (PARTITION BY keys ORDER BY _fetched_at DESC) = 1
```
This enables `revisions()` to see how data changed across fetches.

## Testing Patterns

- Tests use `httpx_mock` fixture (from pytest-httpx) to mock HTTP responses
- The `client` fixture in `conftest.py` creates `FMPClient(api_key="test", cache_path=None)` (in-memory DuckDB)
- For multi-dataset tests, use URL-based matching (`httpx_mock.add_response(url=re.compile(r".*endpoint.*"))`) to avoid FIFO ordering issues with ThreadPoolExecutor
- Mock data must use the actual FMP camelCase field names (e.g., `grossProfit`, `epsDiluted`, `filingDate`)
- Live validation script: `python playground/test_all_columns.py`

## Key Conventions

- `api_name` in `FieldDef` must match the exact field name from the FMP API (case-sensitive). Verify against the live API, not the spec doc — they differ.
- `from`/`to` date params in Python use `from_date`/`to_date` (since `from` is reserved), mapped to `from`/`to` in the params dict.
- Field aliases (e.g., `pe_ratio` → `price_earnings_ratio`) are defined in `_ALIASES` at the bottom of `_ontology.py`.
- The `DERIVED_REGISTRY` takes priority over `FIELD_REGISTRY` in the query builder — if a name exists as both a base field and a derived feature, the derived version is used.
- Rate limit defaults to 10 req/s. Changeable at runtime via `client.rate_limit = 30`.
