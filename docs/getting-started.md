# Getting Started

## Installation

```bash
pip install jaymd96-fmp
```

The package requires Python 3.10+ and depends on `duckdb` and `httpx` (installed automatically).

### Optional Dependencies

The query builder's `.execute()` method returns DataFrames. Install at least one backend:

```bash
# Polars (recommended) -- zero-copy Arrow transfer from DuckDB
pip install polars

# Pandas -- uses DuckDB's native .fetchdf()
pip install pandas
```

If both are installed, polars is the default. You can choose at query time with `execute(backend="pandas")`.

## API Key Configuration

You need an API key from [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs/). There are two ways to provide it:

### Constructor Argument

```python
from fmp import FMPClient

client = FMPClient(api_key="your-api-key")
```

### Environment Variable

```bash
export FMP_API_KEY="your-api-key"
```

```python
from fmp import FMPClient

# Reads from FMP_API_KEY automatically
client = FMPClient()
```

The constructor checks `api_key` first, then falls back to the `FMP_API_KEY` environment variable. If neither is set, an `FMPError` is raised immediately.

## Cache Path Configuration

All API responses and synced data are stored in a DuckDB database. The default path is `~/.fmp/cache.db`.

```python
# Default: persistent file cache
client = FMPClient(api_key="...")
# Stores data at ~/.fmp/cache.db

# Custom path
client = FMPClient(api_key="...", cache_path="/data/fmp/markets.db")

# In-memory (no persistence -- data lost when the process exits)
client = FMPClient(api_key="...", cache_path=None)
```

The DuckDB file contains two kinds of tables:

1. **`_raw_cache`** -- raw API response cache with TTL-based expiration (used by direct endpoint methods like `client.quote()`)
2. **Typed ontology tables** -- one table per dataset (`daily_price`, `income_statement`, etc.), auto-created from the ontology schema, used by the sync system and query builder

## Rate Limiting

The client includes a thread-safe token-bucket rate limiter. The default is 10 requests per second.

```python
# Free-tier plan (5 req/s)
client = FMPClient(api_key="...", rate_limit=5)

# Premium plan (30 req/s)
client = FMPClient(api_key="...", rate_limit=30)

# Unlimited (not recommended -- may trigger API-side throttling)
client = FMPClient(api_key="...", rate_limit=None)
```

### Adjusting at Runtime

The rate limit can be changed on a live client without restarting:

```python
client = FMPClient(api_key="...")

# Check current rate limit
print(client.rate_limit)  # 10.0

# Slow down mid-session
client.rate_limit = 5

# Speed up after upgrading plans
client.rate_limit = 30
```

## TTL Overrides

Each endpoint category has a default TTL (time-to-live) controlling how long cached responses remain valid before re-fetching. You can override any category at construction time:

```python
client = FMPClient(
    api_key="...",
    ttl_overrides={
        "realtime_quotes": 30,          # 30 seconds (default: 60)
        "financial_statements": 86_400, # 1 day (default: 7 days)
        "news": 300,                    # 5 minutes (default: 15 min)
    },
)
```

### Default TTL Categories

| Category | Default TTL | Description |
|---|---|---|
| `realtime_quotes` | 60s | Real-time and after-market quotes |
| `aftermarket` | 60s | Pre/post-market data |
| `intraday_charts` | 5 min | Intraday candle data |
| `daily_historical` | 24 h | Historical daily prices |
| `financial_statements` | 7 days | Income statement, balance sheet, cash flow |
| `company_profiles` | 24 h | Company profiles and metadata |
| `key_metrics` | 7 days | Key financial metrics and ratios |
| `news` | 15 min | Stock and market news |
| `earnings_calendar` | 6 h | Earnings dates and estimates |
| `sec_filings` | 24 h | SEC filing data |
| `insider_trades` | 1 h | Insider trading activity |
| `economic_indicators` | 24 h | Treasury rates, GDP, etc. |
| `analyst` | 24 h | Analyst estimates and ratings |
| `market_performance` | 10 min | Sector/market performance |
| `technical_indicators` | 5 min | SMA, EMA, RSI, etc. |
| `senate` | 1 h | Senate trading disclosures |
| `esg` | 7 days | ESG scores |
| `dcf` | 24 h | DCF valuations |
| `screener` | 10 min | Stock screener results |
| `default` | 1 h | Fallback for uncategorized endpoints |

## HTTP Configuration

```python
client = FMPClient(
    api_key="...",
    timeout=30.0,    # HTTP request timeout in seconds (default: 30)
    max_retries=3,   # Retry count on HTTP 429 responses (default: 3)
)
```

Retries use exponential backoff and only trigger on rate-limit (429) responses.

## Context Manager

Use `FMPClient` as a context manager to ensure HTTP and DuckDB connections are closed properly:

```python
with FMPClient(api_key="...") as client:
    data = client.quote("AAPL")
    # ... do work ...
# Connections closed automatically
```

Or close manually:

```python
client = FMPClient(api_key="...")
try:
    data = client.quote("AAPL")
finally:
    client.close()
```

## Full Constructor Signature

```python
FMPClient(
    api_key: str | None = None,          # FMP API key (or set FMP_API_KEY env var)
    *,
    cache_path: str | None = "~/.fmp/cache.db",  # DuckDB file path, None for in-memory
    ttl_overrides: dict[str, int] | None = None,  # Override TTLs by category
    timeout: float = 30.0,               # HTTP timeout in seconds
    max_retries: int = 3,                # Max retries on 429 responses
    rate_limit: float | None = 10.0,     # Max requests/second, None for unlimited
)
```

## Exception Hierarchy

All exceptions inherit from `FMPError`:

| Exception | HTTP Status | Meaning |
|---|---|---|
| `AuthenticationError` | 401 | Invalid API key |
| `ForbiddenError` | 403 | Plan limit exceeded or endpoint not available |
| `NotFoundError` | 404 | Endpoint or resource not found |
| `RateLimitError` | 429 | Rate limit exceeded (after all retries) |
| `ServerError` | 5xx | FMP server-side error |

```python
from fmp import FMPClient, RateLimitError, AuthenticationError

try:
    client = FMPClient(api_key="bad-key")
    client.quote("AAPL")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limited -- slow down or upgrade plan")
```

## Direct SQL Access

You can run arbitrary SQL against the DuckDB database:

```python
# Query the raw response cache
client.sql("SELECT endpoint, COUNT(*) FROM _raw_cache GROUP BY endpoint")

# Query typed ontology tables (populated by sync)
client.sql("SELECT symbol, date, close FROM daily_price WHERE symbol = 'AAPL' LIMIT 5")

# Clear all cached data
client.clear_cache()

# Clear cache for a specific endpoint
client.clear_cache(endpoint="quote")
```
