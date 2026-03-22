# jaymd96-fmp

Python client for the [Financial Modeling Prep](https://financialmodelingprep.com/) API with automatic DuckDB caching.

## Features

- **150+ endpoints** covering quotes, financials, charts, news, SEC filings, insider trades, and more
- **DuckDB cache** with configurable TTLs per endpoint category — avoid redundant API calls
- **Concurrent fetching** — `fetch_many()` pulls data for hundreds of symbols in parallel
- **Auto-pagination** — `paginate_all()` walks through paginated endpoints automatically
- **Rate limiting** — built-in token-bucket rate limiter, thread-safe for concurrent use
- **Context manager** support for clean resource cleanup

## Installation

```bash
pip install jaymd96-fmp
```

## Quick Start

```python
from fmp import FMPClient

# API key from argument or FMP_API_KEY env var
client = FMPClient(api_key="your-api-key")

# Real-time quote
client.quote("AAPL")

# Financial statements
client.income_statement("AAPL", period="quarter", limit=4)

# Historical prices
client.historical_price_eod_full("AAPL", from_date="2024-01-01", to_date="2024-12-31")

# Stock screener
client.screener(sector="Technology", market_cap_more_than=1_000_000_000)

# Technical indicators
client.sma("AAPL", period_length=20, timeframe="1day")
```

## Concurrent Fetching

```python
# Fetch quotes for many symbols in parallel
results = client.fetch_many(client.quote, ["AAPL", "MSFT", "GOOG", "AMZN"], max_workers=10)
# Returns: {"AAPL": [...], "MSFT": [...], ...}
```

## Auto-Pagination

```python
# Fetch all pages of stock news
all_news = client.paginate_all(client.stock_news_latest, limit=100, max_pages=50)
```

## Cache

All responses are cached in a local DuckDB database (`~/.fmp/cache.db` by default). TTLs are set per endpoint category (e.g., 60s for quotes, 7 days for financial statements).

```python
# In-memory cache (no persistence)
client = FMPClient(api_key="...", cache_path=None)

# Custom TTLs
client = FMPClient(api_key="...", ttl_overrides={"realtime_quotes": 30})

# Force refresh (bypass cache)
client.quote("AAPL", force_refresh=True)

# Run SQL queries on cached data
client.sql("SELECT * FROM _raw_cache WHERE endpoint = 'quote'")

# Clear cache
client.clear_cache()
client.clear_cache(endpoint="quote")
```

## Rate Limiting

```python
# Limit to 5 requests per second (for free-tier plans)
client = FMPClient(api_key="...", rate_limit=5)
```

## Context Manager

```python
with FMPClient(api_key="...") as client:
    data = client.quote("AAPL")
# Connections closed automatically
```

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `api_key` | `FMP_API_KEY` env var | Your FMP API key |
| `cache_path` | `~/.fmp/cache.db` | DuckDB file path, `None` for in-memory |
| `ttl_overrides` | `{}` | Override TTLs by category name |
| `timeout` | `30.0` | HTTP timeout in seconds |
| `max_retries` | `3` | Retry count on 429 responses |
| `rate_limit` | `None` | Max requests/second |

## License

MIT
