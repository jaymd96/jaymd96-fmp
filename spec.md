# Financial Modeling Prep (FMP) API — Client & Cache Specification

> **Version:** 1.0.0  
> **Base URL:** `https://financialmodelingprep.com/stable/`  
> **Auth:** All requests require `apikey` — passed as query parameter (`?apikey=KEY`) or header (`apikey: KEY`).  
> **Response format:** JSON (arrays at the top level unless otherwise noted).

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [DuckDB Cache Layer](#2-duckdb-cache-layer)
3. [Common Parameters](#3-common-parameters)
4. [API Endpoints](#4-api-endpoints)
   - 4.1 [Company Search](#41-company-search)
   - 4.2 [Stock Directory](#42-stock-directory)
   - 4.3 [Company Information](#43-company-information)
   - 4.4 [Quotes](#44-quotes)
   - 4.5 [Financial Statements](#45-financial-statements)
   - 4.6 [Charts / Historical Prices](#46-charts--historical-prices)
   - 4.7 [Economics](#47-economics)
   - 4.8 [Earnings, Dividends & Splits](#48-earnings-dividends--splits)
   - 4.9 [Earnings Transcripts](#49-earnings-transcripts)
   - 4.10 [News](#410-news)
   - 4.11 [Form 13F / Institutional Ownership](#411-form-13f--institutional-ownership)
   - 4.12 [Analyst](#412-analyst)
   - 4.13 [Market Performance](#413-market-performance)
   - 4.14 [Technical Indicators](#414-technical-indicators)
   - 4.15 [ETF & Mutual Funds](#415-etf--mutual-funds)
   - 4.16 [SEC Filings](#416-sec-filings)
   - 4.17 [Insider Trades](#417-insider-trades)
   - 4.18 [Indexes](#418-indexes)
   - 4.19 [Market Hours](#419-market-hours)
   - 4.20 [Commodities](#420-commodities)
   - 4.21 [Discounted Cash Flow](#421-discounted-cash-flow)
   - 4.22 [Forex](#422-forex)
   - 4.23 [Crypto](#423-crypto)
   - 4.24 [Senate Trading](#424-senate-trading)
   - 4.25 [ESG](#425-esg)
   - 4.26 [Commitment of Traders](#426-commitment-of-traders)
   - 4.27 [Fundraisers](#427-fundraisers)
   - 4.28 [Bulk Endpoints](#428-bulk-endpoints)
5. [Response Schemas](#5-response-schemas)
6. [Error Handling](#6-error-handling)
7. [Rate Limits & Best Practices](#7-rate-limits--best-practices)

---

## 1. Architecture Overview

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│  Application │────▶│  FMP Client   │────▶│  FMP REST API    │
│  Code        │◀────│  (Python)     │◀────│  (stable/)       │
└──────────────┘     └───────┬───────┘     └──────────────────┘
                             │
                     ┌───────▼───────┐
                     │  DuckDB Cache │
                     │  (local .db)  │
                     └───────────────┘
```

The client is a Python class that:

1. Accepts method calls mapping to each API section (e.g., `client.quote("AAPL")`).
2. Checks DuckDB for a cached response within the configured TTL.
3. On cache miss, calls the FMP API, stores the result in DuckDB, and returns it.
4. Exposes the DuckDB connection so users can run analytical SQL directly over cached data.

---

## 2. DuckDB Cache Layer

### 2.1 Schema Design

```sql
-- Master cache metadata table
CREATE TABLE IF NOT EXISTS _cache_meta (
    cache_key     VARCHAR PRIMARY KEY,   -- e.g. "quote:AAPL"
    endpoint      VARCHAR NOT NULL,       -- e.g. "/stable/quote"
    params_hash   VARCHAR NOT NULL,       -- SHA-256 of sorted query params
    fetched_at    TIMESTAMP NOT NULL DEFAULT now(),
    ttl_seconds   INTEGER NOT NULL,
    expires_at    TIMESTAMP GENERATED ALWAYS AS (fetched_at + INTERVAL (ttl_seconds) SECOND),
    row_count     INTEGER,
    http_status   INTEGER
);

-- Each endpoint category gets a typed table.  Examples:

CREATE TABLE IF NOT EXISTS quotes (
    symbol          VARCHAR,
    name            VARCHAR,
    price           DOUBLE,
    change          DOUBLE,
    change_pct      DOUBLE,
    day_low         DOUBLE,
    day_high        DOUBLE,
    year_low        DOUBLE,
    year_high       DOUBLE,
    volume          BIGINT,
    avg_volume      BIGINT,
    open            DOUBLE,
    previous_close  DOUBLE,
    market_cap      BIGINT,
    pe              DOUBLE,
    eps             DOUBLE,
    shares_outstanding BIGINT,
    earnings_date   DATE,
    exchange        VARCHAR,
    timestamp       BIGINT,
    _fetched_at     TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS income_statements (
    symbol                VARCHAR,
    date                  DATE,
    period                VARCHAR,     -- "FY" | "Q1" | "Q2" | "Q3" | "Q4"
    reported_currency     VARCHAR,
    cik                   VARCHAR,
    filling_date          DATE,
    accepted_date         TIMESTAMP,
    calendar_year         INTEGER,
    revenue               BIGINT,
    cost_of_revenue       BIGINT,
    gross_profit          BIGINT,
    operating_expenses    BIGINT,
    operating_income      BIGINT,
    net_income            BIGINT,
    eps                   DOUBLE,
    eps_diluted           DOUBLE,
    weighted_avg_shares   BIGINT,
    weighted_avg_shares_dil BIGINT,
    ebitda                BIGINT,
    link                  VARCHAR,
    final_link            VARCHAR,
    _fetched_at           TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS historical_prices (
    symbol    VARCHAR,
    date      DATE,
    open      DOUBLE,
    high      DOUBLE,
    low       DOUBLE,
    close     DOUBLE,
    adj_close DOUBLE,
    volume    BIGINT,
    vwap      DOUBLE,
    change    DOUBLE,
    change_pct DOUBLE,
    _fetched_at TIMESTAMP DEFAULT now()
);

-- Generic JSON cache for endpoints without typed tables
CREATE TABLE IF NOT EXISTS _raw_cache (
    cache_key   VARCHAR PRIMARY KEY,
    endpoint    VARCHAR NOT NULL,
    params_json VARCHAR,
    response    JSON NOT NULL,
    fetched_at  TIMESTAMP DEFAULT now(),
    ttl_seconds INTEGER NOT NULL
);
```

### 2.2 TTL Strategy

| Data Category | Default TTL | Rationale |
|---|---|---|
| Real-time quotes | 60 seconds | Prices change continuously during market hours |
| Aftermarket quotes/trades | 60 seconds | Post-market data updates frequently |
| Intraday charts (1min–4hr) | 5 minutes | Granular but semi-stale acceptable |
| Daily historical prices | 24 hours | EOD data is final after close |
| Financial statements | 7 days | Updated quarterly |
| Company profiles | 24 hours | Rarely change |
| Key metrics / ratios | 7 days | Derived from statements |
| News articles | 15 minutes | Fresh content matters |
| Earnings calendar | 6 hours | Updated periodically |
| SEC filings | 24 hours | Filed periodically |
| Insider trades | 1 hour | Filed with some delay |
| Economic indicators | 24 hours | Released on schedule |
| ETF/fund holdings | 24 hours | Quarterly with daily estimates |
| Index constituents | 24 hours | Change infrequently |
| Market hours/holidays | 7 days | Essentially static |
| Screener results | 10 minutes | Dynamic filtering |
| Bulk data | 24 hours | Large dataset refreshes |
| Static lists (exchanges, sectors) | 30 days | Rarely change |

### 2.3 Cache Key Convention

```
{endpoint_slug}:{sorted_params_hash}

Examples:
  quote:AAPL
  income-statement:AAPL:annual:limit=5
  historical-price-eod-full:AAPL:from=2024-01-01:to=2024-12-31
  news-stock-latest:page=0:limit=20
```

### 2.4 Cache Operations

```python
def cache_get(self, key: str) -> Optional[list[dict]]:
    """Return cached data if key exists and TTL has not expired."""
    row = self.db.execute("""
        SELECT response FROM _raw_cache
        WHERE cache_key = ? AND fetched_at + INTERVAL (ttl_seconds) SECOND > now()
    """, [key]).fetchone()
    return json.loads(row[0]) if row else None

def cache_set(self, key: str, endpoint: str, params: dict, data: list[dict], ttl: int):
    """Upsert cached response."""
    self.db.execute("""
        INSERT OR REPLACE INTO _raw_cache (cache_key, endpoint, params_json, response, ttl_seconds)
        VALUES (?, ?, ?, ?::JSON, ?)
    """, [key, endpoint, json.dumps(params), json.dumps(data), ttl])
```

---

## 3. Common Parameters

These parameters appear across many endpoints and behave consistently:

| Parameter | Type | Description |
|---|---|---|
| `symbol` | `string` | Stock ticker symbol, e.g. `AAPL`. Case-insensitive. |
| `symbols` | `string` | Comma-separated list of symbols for batch endpoints, e.g. `AAPL,MSFT,GOOG`. |
| `exchange` | `string` | Exchange filter. Values: `NYSE`, `NASDAQ`, `AMEX`, `EURONEXT`, `TSX`, `LSE`, `XETRA`, `NSE`, `ETF`, `MUTUAL_FUND`, `COMMODITY`, `INDEX`, `CRYPTO`, `FOREX`. |
| `period` | `string` | Financial statement period: `annual` (default) or `quarter`. |
| `limit` | `integer` | Max results to return. Default varies by endpoint (typically 10–100). |
| `page` | `integer` | Zero-indexed page number for paginated results. Default `0`. |
| `from` | `string` | Start date filter (inclusive). Format: `YYYY-MM-DD`. |
| `to` | `string` | End date filter (inclusive). Format: `YYYY-MM-DD`. Max range is typically 1–5 years depending on endpoint. |
| `apikey` | `string` | **Required.** Your FMP API key. Can also be sent as header `apikey: KEY`. |

---

## 4. API Endpoints

All paths below are relative to: `https://financialmodelingprep.com/stable/`

### 4.1 Company Search

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Symbol Search | GET | `search-symbol` | `query` (required), `limit`, `exchange` | Global |
| 2 | Name Search | GET | `search-name` | `query` (required), `limit`, `exchange` | Global |
| 3 | CIK Search | GET | `search-cik` | `cik` (required) | US |
| 4 | CUSIP Search | GET | `search-cusip` | `cusip` (required) | Global |
| 5 | ISIN Search | GET | `search-isin` | `isin` (required) | Global |
| 6 | Stock Screener | GET | `company-screener` | `marketCapMoreThan`, `marketCapLowerThan`, `priceMoreThan`, `priceLowerThan`, `volumeMoreThan`, `volumeLowerThan`, `betaMoreThan`, `betaLowerThan`, `dividendMoreThan`, `dividendLowerThan`, `sector`, `industry`, `country`, `exchange`, `isEtf`, `isActivelyTrading`, `limit`, `page` | Global |
| 7 | Exchange Variants | GET | `search-exchange-variants` | `symbol` (required) | Global |

**Symbol Search — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "currency": "USD",
    "stockExchange": "NASDAQ Global Select",
    "exchangeShortName": "NASDAQ"
  }
]
```

**Stock Screener — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "companyName": "Apple Inc.",
    "marketCap": 2890000000000,
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "beta": 1.24,
    "price": 182.52,
    "lastAnnualDividend": 0.96,
    "volume": 54000000,
    "exchange": "NASDAQ",
    "exchangeShortName": "NASDAQ",
    "country": "US",
    "isEtf": false,
    "isFund": false,
    "isActivelyTrading": true
  }
]
```

---

### 4.2 Stock Directory

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | Company Symbols List | GET | `stock-list` | — |
| 2 | Financial Statement Symbols List | GET | `financial-statement-symbol-list` | — |
| 3 | CIK List | GET | `cik-list` | `page`, `limit` |
| 4 | Symbol Changes List | GET | `symbol-change` | `page`, `limit` |
| 5 | ETF List | GET | `etf-list` | — |
| 6 | Actively Trading List | GET | `actively-trading-list` | — |
| 7 | Earnings Transcript List | GET | `earnings-transcript-list` | — |
| 8 | Available Exchanges | GET | `available-exchanges` | — |
| 9 | Available Sectors | GET | `available-sectors` | — |
| 10 | Available Industries | GET | `available-industries` | — |
| 11 | Available Countries | GET | `available-countries` | — |

**Stock List — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 182.52,
    "exchange": "NASDAQ Global Select",
    "exchangeShortName": "NASDAQ",
    "type": "stock"
  }
]
```

---

### 4.3 Company Information

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Company Profile | GET | `profile` | `symbol` | Global |
| 2 | Profile by CIK | GET | `profile-cik` | `cik` | US |
| 3 | Company Notes | GET | `company-notes` | `symbol` | US |
| 4 | Stock Peers | GET | `stock-peers` | `symbol` | Global |
| 5 | Delisted Companies | GET | `delisted-companies` | `page`, `limit` | US |
| 6 | Employee Count | GET | `employee-count` | `symbol` | US |
| 7 | Historical Employee Count | GET | `historical-employee-count` | `symbol` | US |
| 8 | Market Cap | GET | `market-capitalization` | `symbol` | Global |
| 9 | Batch Market Cap | GET | `market-capitalization-batch` | `symbols` | Global |
| 10 | Historical Market Cap | GET | `historical-market-capitalization` | `symbol`, `from`, `to`, `limit` | Global |
| 11 | Shares Float | GET | `shares-float` | `symbol` | Global |
| 12 | All Shares Float | GET | `shares-float-all` | `page`, `limit` | Global |
| 13 | Latest M&A | GET | `mergers-acquisitions-latest` | `page`, `limit` | US |
| 14 | Search M&A | GET | `mergers-acquisitions-search` | `name` | US |
| 15 | Company Executives | GET | `key-executives` | `symbol` | Global |
| 16 | Executive Compensation | GET | `governance-executive-compensation` | `symbol` | US |
| 17 | Compensation Benchmark | GET | `executive-compensation-benchmark` | `year` | US |

**Company Profile — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "companyName": "Apple Inc.",
    "currency": "USD",
    "cik": "0000320193",
    "isin": "US0378331005",
    "cusip": "037833100",
    "exchange": "NASDAQ Global Select",
    "exchangeShortName": "NASDAQ",
    "industry": "Consumer Electronics",
    "sector": "Technology",
    "country": "US",
    "fullTimeEmployees": "164000",
    "description": "Apple Inc. designs, manufactures...",
    "ceo": "Mr. Timothy D. Cook",
    "website": "https://www.apple.com",
    "phone": "408-996-1010",
    "address": "One Apple Park Way",
    "city": "Cupertino",
    "state": "CA",
    "zip": "95014",
    "image": "https://financialmodelingprep.com/image-stock/AAPL.png",
    "ipoDate": "1980-12-12",
    "price": 182.52,
    "beta": 1.24,
    "volAvg": 54000000,
    "mktCap": 2890000000000,
    "lastDiv": 0.96,
    "range": "124.17-199.62",
    "changes": 2.33,
    "dcf": 150.12,
    "dcfDiff": 32.40,
    "isEtf": false,
    "isFund": false,
    "isActivelyTrading": true,
    "defaultImage": false
  }
]
```

---

### 4.4 Quotes

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Stock Quote | GET | `quote` | `symbol` | Global |
| 2 | Stock Quote Short | GET | `quote-short` | `symbol` | Global |
| 3 | Aftermarket Trade | GET | `aftermarket-trade` | `symbol` | US |
| 4 | Aftermarket Quote | GET | `aftermarket-quote` | `symbol` | US |
| 5 | Stock Price Change | GET | `stock-price-change` | `symbol` | Global |
| 6 | Batch Quote | GET | `batch-quote` | `symbols` | Global |
| 7 | Batch Quote Short | GET | `batch-quote-short` | `symbols` | Global |
| 8 | Batch Aftermarket Trade | GET | `batch-aftermarket-trade` | `symbols` | US |
| 9 | Batch Aftermarket Quote | GET | `batch-aftermarket-quote` | `symbols` | US |
| 10 | Exchange Quotes | GET | `batch-exchange-quote` | `exchange` | Global |
| 11 | Mutual Fund Quotes | GET | `batch-mutualfund-quotes` | `exchange` | US |
| 12 | ETF Quotes | GET | `batch-etf-quotes` | `exchange` | Global |
| 13 | Commodities Quotes | GET | `batch-commodity-quotes` | `exchange` | — |
| 14 | Crypto Quotes | GET | `batch-crypto-quotes` | `exchange` | — |
| 15 | Forex Quotes | GET | `batch-forex-quotes` | `exchange` | — |
| 16 | Index Quotes | GET | `batch-index-quotes` | `exchange` | — |

**Stock Quote — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 182.52,
    "changesPercentage": 1.29,
    "change": 2.33,
    "dayLow": 179.25,
    "dayHigh": 183.07,
    "yearHigh": 199.62,
    "yearLow": 124.17,
    "marketCap": 2890000000000,
    "priceAvg50": 178.43,
    "priceAvg200": 170.12,
    "exchange": "NASDAQ",
    "volume": 54321000,
    "avgVolume": 48000000,
    "open": 180.10,
    "previousClose": 180.19,
    "eps": 6.57,
    "pe": 27.78,
    "earningsAnnouncement": "2024-10-31T16:00:00.000+0000",
    "sharesOutstanding": 15800000000,
    "timestamp": 1711100400
  }
]
```

**Stock Price Change — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "1D": 1.29,
    "5D": 3.41,
    "1M": 5.12,
    "3M": 8.45,
    "6M": 12.30,
    "ytd": 15.20,
    "1Y": 22.40,
    "3Y": 45.60,
    "5Y": 280.50,
    "10Y": 850.00,
    "max": 15000.00
  }
]
```

---

### 4.5 Financial Statements

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Income Statement | GET | `income-statement` | `symbol`, `period`, `limit` | Global |
| 2 | Balance Sheet | GET | `balance-sheet-statement` | `symbol`, `period`, `limit` | Global |
| 3 | Cash Flow Statement | GET | `cash-flow-statement` | `symbol`, `period`, `limit` | Global |
| 4 | Latest Financial Statements | GET | `latest-financial-statements` | `page`, `limit` | Global |
| 5 | Income Statement TTM | GET | `income-statement-ttm` | `symbol` | Global |
| 6 | Balance Sheet TTM | GET | `balance-sheet-statement-ttm` | `symbol` | Global |
| 7 | Cash Flow TTM | GET | `cash-flow-statement-ttm` | `symbol` | Global |
| 8 | Key Metrics | GET | `key-metrics` | `symbol`, `period`, `limit` | Global |
| 9 | Financial Ratios | GET | `ratios` | `symbol`, `period`, `limit` | Global |
| 10 | Key Metrics TTM | GET | `key-metrics-ttm` | `symbol` | Global |
| 11 | Financial Ratios TTM | GET | `ratios-ttm` | `symbol` | Global |
| 12 | Financial Scores | GET | `financial-scores` | `symbol` | Global |
| 13 | Owner Earnings | GET | `owner-earnings` | `symbol` | Global |
| 14 | Enterprise Values | GET | `enterprise-values` | `symbol`, `period`, `limit` | Global |
| 15 | Income Statement Growth | GET | `income-statement-growth` | `symbol`, `period`, `limit` | Global |
| 16 | Balance Sheet Growth | GET | `balance-sheet-statement-growth` | `symbol`, `period`, `limit` | Global |
| 17 | Cash Flow Growth | GET | `cash-flow-statement-growth` | `symbol`, `period`, `limit` | Global |
| 18 | Financial Growth | GET | `financial-growth` | `symbol`, `period`, `limit` | Global |
| 19 | Financial Reports Dates | GET | `financial-reports-dates` | `symbol` | — |
| 20 | Reports 10-K JSON | GET | `financial-reports-json` | `symbol`, `year`, `period` | — |
| 21 | Reports 10-K XLSX | GET | `financial-reports-xlsx` | `symbol`, `year`, `period` | — |
| 22 | Revenue Product Segmentation | GET | `revenue-product-segmentation` | `symbol`, `period` | — |
| 23 | Revenue Geographic Segmentation | GET | `revenue-geographic-segmentation` | `symbol`, `period` | — |
| 24 | As-Reported Income Statement | GET | `income-statement-as-reported` | `symbol`, `period`, `limit` | — |
| 25 | As-Reported Balance Sheet | GET | `balance-sheet-statement-as-reported` | `symbol`, `period`, `limit` | — |
| 26 | As-Reported Cash Flow | GET | `cash-flow-statement-as-reported` | `symbol`, `period`, `limit` | — |
| 27 | As-Reported Full | GET | `financial-statement-full-as-reported` | `symbol`, `period`, `limit` | — |

**Income Statement — Response Schema:**

```json
[
  {
    "date": "2023-09-30",
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "cik": "0000320193",
    "fillingDate": "2023-11-03",
    "acceptedDate": "2023-11-02T18:04:35.000Z",
    "calendarYear": "2023",
    "period": "FY",
    "revenue": 383285000000,
    "costOfRevenue": 214137000000,
    "grossProfit": 169148000000,
    "grossProfitRatio": 0.4413,
    "researchAndDevelopmentExpenses": 29915000000,
    "sellingGeneralAndAdministrativeExpenses": 24932000000,
    "otherExpenses": 0,
    "operatingExpenses": 54847000000,
    "costAndExpenses": 268984000000,
    "interestIncome": 3999000000,
    "interestExpense": 3933000000,
    "depreciationAndAmortization": 11519000000,
    "ebitda": 125820000000,
    "ebitdaratio": 0.3283,
    "operatingIncome": 114301000000,
    "operatingIncomeRatio": 0.2982,
    "totalOtherIncomeExpensesNet": -382000000,
    "incomeBeforeTax": 113919000000,
    "incomeBeforeTaxRatio": 0.2972,
    "incomeTaxExpense": 16741000000,
    "netIncome": 96995000000,
    "netIncomeRatio": 0.2531,
    "eps": 6.16,
    "epsdiluted": 6.13,
    "weightedAverageShsOut": 15744231000,
    "weightedAverageShsOutDil": 15812547000,
    "link": "https://www.sec.gov/...",
    "finalLink": "https://www.sec.gov/..."
  }
]
```

**Key Metrics — Response Schema (partial):**

```json
[
  {
    "symbol": "AAPL",
    "date": "2023-09-30",
    "calendarYear": "2023",
    "period": "FY",
    "revenuePerShare": 24.34,
    "netIncomePerShare": 6.16,
    "operatingCashFlowPerShare": 7.01,
    "freeCashFlowPerShare": 6.43,
    "cashPerShare": 4.03,
    "bookValuePerShare": 3.96,
    "tangibleBookValuePerShare": 3.96,
    "shareholdersEquityPerShare": 3.96,
    "interestDebtPerShare": 7.33,
    "marketCap": 2690000000000,
    "enterpriseValue": 2760000000000,
    "peRatio": 27.78,
    "priceToSalesRatio": 7.02,
    "pocfratio": 24.38,
    "pfcfRatio": 26.55,
    "pbRatio": 43.19,
    "ptbRatio": 43.19,
    "evToSales": 7.20,
    "enterpriseValueOverEBITDA": 21.94,
    "evToOperatingCashFlow": 24.99,
    "evToFreeCashFlow": 27.22,
    "earningsYield": 0.036,
    "freeCashFlowYield": 0.038,
    "debtToEquity": 1.81,
    "debtToAssets": 0.32,
    "netDebtToEBITDA": 0.56,
    "currentRatio": 0.99,
    "dividendYield": 0.0054,
    "payoutRatio": 0.156,
    "roic": 0.560,
    "roe": 1.560,
    "roa": 0.289
  }
]
```

---

### 4.6 Charts / Historical Prices

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Chart Light (EOD) | GET | `historical-price-eod/light` | `symbol`, `from`, `to` | Global |
| 2 | Chart Full (EOD) | GET | `historical-price-eod/full` | `symbol`, `from`, `to` | Global |
| 3 | Non-Split Adjusted | GET | `historical-price-eod/non-split-adjusted` | `symbol`, `from`, `to` | Global |
| 4 | Dividend Adjusted | GET | `historical-price-eod/dividend-adjusted` | `symbol`, `from`, `to` | Global |
| 5 | 1-Minute Intraday | GET | `historical-chart/1min` | `symbol`, `from`, `to` | Global |
| 6 | 5-Minute Intraday | GET | `historical-chart/5min` | `symbol`, `from`, `to` | Global |
| 7 | 15-Minute Intraday | GET | `historical-chart/15min` | `symbol`, `from`, `to` | Global |
| 8 | 30-Minute Intraday | GET | `historical-chart/30min` | `symbol`, `from`, `to` | Global |
| 9 | 1-Hour Intraday | GET | `historical-chart/1hour` | `symbol`, `from`, `to` | Global |
| 10 | 4-Hour Intraday | GET | `historical-chart/4hour` | `symbol`, `from`, `to` | Global |

**Chart Full — Response Schema:**

```json
[
  {
    "date": "2024-03-15",
    "open": 172.28,
    "high": 173.58,
    "low": 170.77,
    "close": 172.62,
    "adjClose": 172.62,
    "volume": 71200000,
    "unadjustedVolume": 71200000,
    "change": 0.34,
    "changePercent": 0.197,
    "vwap": 172.32,
    "label": "March 15, 24",
    "changeOverTime": 0.00197
  }
]
```

**Intraday — Response Schema:**

```json
[
  {
    "date": "2024-03-15 15:59:00",
    "open": 172.50,
    "low": 172.40,
    "high": 172.65,
    "close": 172.62,
    "volume": 1230000
  }
]
```

---

### 4.7 Economics

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | Treasury Rates | GET | `treasury-rates` | `from`, `to` |
| 2 | Economic Indicators | GET | `economic-indicators` | `name` (required: `GDP`, `realGDP`, `CPI`, `inflationRate`, `federalFundsRate`, `unemploymentRate`, etc.), `from`, `to` |
| 3 | Economic Calendar | GET | `economic-calendar` | `from`, `to` |
| 4 | Market Risk Premium | GET | `market-risk-premium` | — |

**Treasury Rates — Response Schema:**

```json
[
  {
    "date": "2024-03-15",
    "month1": 5.52,
    "month2": 5.48,
    "month3": 5.44,
    "month6": 5.33,
    "year1": 5.02,
    "year2": 4.72,
    "year3": 4.46,
    "year5": 4.27,
    "year7": 4.27,
    "year10": 4.31,
    "year20": 4.58,
    "year30": 4.44
  }
]
```

---

### 4.8 Earnings, Dividends & Splits

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Dividends (Company) | GET | `dividends` | `symbol`, `from`, `to`, `limit` | Global |
| 2 | Dividends Calendar | GET | `dividends-calendar` | `from`, `to` | Global |
| 3 | Earnings Report | GET | `earnings` | `symbol`, `limit` | Global |
| 4 | Earnings Calendar | GET | `earnings-calendar` | `from`, `to` | Global |
| 5 | IPOs Calendar | GET | `ipos-calendar` | `from`, `to` | Global |
| 6 | IPOs Disclosure | GET | `ipos-disclosure` | `from`, `to` | US |
| 7 | IPOs Prospectus | GET | `ipos-prospectus` | `from`, `to` | US |
| 8 | Stock Splits (Company) | GET | `splits` | `symbol`, `from`, `to` | Global |
| 9 | Splits Calendar | GET | `splits-calendar` | `from`, `to` | Global |

**Earnings — Response Schema:**

```json
[
  {
    "date": "2024-01-25",
    "symbol": "AAPL",
    "eps": 2.18,
    "epsEstimated": 2.10,
    "revenue": 119580000000,
    "revenueEstimated": 117900000000,
    "time": "amc",
    "fiscalDateEnding": "2023-12-31",
    "updatedFromDate": "2024-01-25"
  }
]
```

**Dividends — Response Schema:**

```json
[
  {
    "date": "2024-02-09",
    "label": "February 09, 24",
    "adjDividend": 0.24,
    "dividend": 0.24,
    "recordDate": "2024-02-12",
    "paymentDate": "2024-02-15",
    "declarationDate": "2024-02-01"
  }
]
```

---

### 4.9 Earnings Transcripts

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Latest Transcripts | GET | `earning-call-transcript-latest` | `page`, `limit` | Global |
| 2 | Transcript by Symbol | GET | `earning-call-transcript` | `symbol`, `year`, `quarter` | Global |
| 3 | Transcript Dates | GET | `earning-call-transcript-dates` | `symbol` | Global |
| 4 | Available Transcript Symbols | GET | `earnings-transcript-list` | — | Global |

**Transcript — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "quarter": 3,
    "year": 2020,
    "date": "2020-07-30 17:00:00",
    "content": "Operator: Good day, and welcome to the Apple Q3..."
  }
]
```

---

### 4.10 News

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | FMP Articles | GET | `fmp-articles` | `page`, `limit` | US |
| 2 | General News | GET | `news/general-latest` | `page`, `limit` | Global |
| 3 | Press Releases (Latest) | GET | `news/press-releases-latest` | `page`, `limit` | US |
| 4 | Stock News (Latest) | GET | `news/stock-latest` | `page`, `limit` | — |
| 5 | Crypto News (Latest) | GET | `news/crypto-latest` | `page`, `limit` | — |
| 6 | Forex News (Latest) | GET | `news/forex-latest` | `page`, `limit` | — |
| 7 | Search Press Releases | GET | `news/press-releases` | `symbols` | US |
| 8 | Search Stock News | GET | `news/stock` | `symbols`, `from`, `to`, `page`, `limit` | — |
| 9 | Search Crypto News | GET | `news/crypto` | `symbols`, `from`, `to`, `page`, `limit` | — |
| 10 | Search Forex News | GET | `news/forex` | `symbols`, `from`, `to`, `page`, `limit` | — |

**Stock News — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "publishedDate": "2024-03-15T14:30:00.000Z",
    "title": "Apple Announces New Product...",
    "image": "https://cdn.example.com/image.jpg",
    "site": "Reuters",
    "text": "Apple Inc. announced today...",
    "url": "https://www.reuters.com/article/..."
  }
]
```

---

### 4.11 Form 13F / Institutional Ownership

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Latest Filings | GET | `institutional-ownership/latest` | `page`, `limit` | US |
| 2 | Filings Extract | GET | `institutional-ownership/extract` | `cik`, `year`, `quarter` | US |
| 3 | Filing Dates | GET | `institutional-ownership/dates` | `cik` | US |
| 4 | Analytics by Holder | GET | `institutional-ownership/extract-analytics/holder` | `symbol`, `year`, `quarter`, `page`, `limit` | US |
| 5 | Holder Performance | GET | `institutional-ownership/holder-performance-summary` | `cik`, `page` | US |
| 6 | Industry Breakdown | GET | `institutional-ownership/holder-industry-breakdown` | `cik`, `year`, `quarter` | US |
| 7 | Positions Summary | GET | `institutional-ownership/symbol-positions-summary` | `symbol`, `year`, `quarter` | US |
| 8 | Industry Summary | GET | `institutional-ownership/industry-summary` | `year`, `quarter` | US |

---

### 4.12 Analyst

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Financial Estimates | GET | `analyst-estimates` | `symbol`, `period`, `page`, `limit` | Global |
| 2 | Ratings Snapshot | GET | `ratings-snapshot` | `symbol` | Global |
| 3 | Historical Ratings | GET | `ratings-historical` | `symbol`, `limit` | Global |
| 4 | Price Target Summary | GET | `price-target-summary` | `symbol` | US |
| 5 | Price Target Consensus | GET | `price-target-consensus` | `symbol` | US |
| 6 | Grades | GET | `grades` | `symbol`, `limit` | Global |
| 7 | Historical Grades | GET | `grades-historical` | `symbol`, `limit` | Global |
| 8 | Grades Summary | GET | `grades-consensus` | `symbol` | Global |

**Analyst Estimates — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-09-30",
    "estimatedRevenueLow": 370000000000,
    "estimatedRevenueHigh": 420000000000,
    "estimatedRevenueAvg": 395000000000,
    "estimatedEbitdaLow": 115000000000,
    "estimatedEbitdaHigh": 138000000000,
    "estimatedEbitdaAvg": 126000000000,
    "estimatedEpsAvg": 6.70,
    "estimatedEpsHigh": 7.10,
    "estimatedEpsLow": 6.20,
    "estimatedNetIncomeLow": 95000000000,
    "estimatedNetIncomeHigh": 110000000000,
    "estimatedNetIncomeAvg": 102000000000,
    "estimatedSgaExpenseAvg": 25000000000,
    "numberAnalystEstimatedRevenue": 32,
    "numberAnalystsEstimatedEps": 35
  }
]
```

**Grades — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-03-10",
    "gradingCompany": "Morgan Stanley",
    "previousGrade": "Overweight",
    "newGrade": "Overweight",
    "action": "maintain"
  }
]
```

---

### 4.13 Market Performance

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Sector Performance Snapshot | GET | `sector-performance-snapshot` | `date` | Global |
| 2 | Industry Performance Snapshot | GET | `industry-performance-snapshot` | `date` | Global |
| 3 | Historical Sector Performance | GET | `historical-sector-performance` | `sector`, `from`, `to` | Global |
| 4 | Historical Industry Performance | GET | `historical-industry-performance` | `industry`, `from`, `to` | Global |
| 5 | Sector PE Snapshot | GET | `sector-pe-snapshot` | `date` | Global |
| 6 | Industry PE Snapshot | GET | `industry-pe-snapshot` | `date` | Global |
| 7 | Historical Sector PE | GET | `historical-sector-pe` | `sector`, `from`, `to` | Global |
| 8 | Historical Industry PE | GET | `historical-industry-pe` | `industry`, `from`, `to` | Global |
| 9 | Biggest Gainers | GET | `biggest-gainers` | — | US |
| 10 | Biggest Losers | GET | `biggest-losers` | — | US |
| 11 | Most Active | GET | `most-actives` | — | US |

---

### 4.14 Technical Indicators

All technical indicator endpoints share the same parameter signature and response pattern.

**Common Parameters:** `symbol` (required), `periodLength` (required, integer), `timeframe` (required: `1min`, `5min`, `15min`, `30min`, `1hour`, `4hour`, `1day`, `1week`, `1month`)

| # | Indicator | Path |
|---|---|---|
| 1 | Simple Moving Average (SMA) | `technical-indicators/sma` |
| 2 | Exponential Moving Average (EMA) | `technical-indicators/ema` |
| 3 | Weighted Moving Average (WMA) | `technical-indicators/wma` |
| 4 | Double EMA (DEMA) | `technical-indicators/dema` |
| 5 | Triple EMA (TEMA) | `technical-indicators/tema` |
| 6 | Relative Strength Index (RSI) | `technical-indicators/rsi` |
| 7 | Standard Deviation | `technical-indicators/standarddeviation` |
| 8 | Williams %R | `technical-indicators/williams` |
| 9 | Average Directional Index (ADX) | `technical-indicators/adx` |

**Technical Indicator — Response Schema:**

```json
[
  {
    "date": "2024-03-15",
    "open": 172.28,
    "high": 173.58,
    "low": 170.77,
    "close": 172.62,
    "volume": 71200000,
    "sma": 174.35
  }
]
```

*(The indicator field name matches the endpoint: `sma`, `ema`, `wma`, `dema`, `tema`, `rsi`, `standarddeviation`, `williams`, `adx`.)*

---

### 4.15 ETF & Mutual Funds

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | ETF/Fund Holdings | GET | `etf/holdings` | `symbol`, `date` | Global |
| 2 | ETF/Fund Info | GET | `etf/info` | `symbol` | Global |
| 3 | Country Weightings | GET | `etf/country-weightings` | `symbol` | Global |
| 4 | ETF Asset Exposure | GET | `etf/asset-exposure` | `symbol` | Global |
| 5 | Sector Weightings | GET | `etf/sector-weightings` | `symbol` | Global |
| 6 | Latest Disclosures | GET | `funds/disclosure-holders-latest` | `symbol` | US |
| 7 | Mutual Fund Disclosures | GET | `funds/disclosure` | `symbol`, `year`, `quarter` | US |
| 8 | Disclosure Name Search | GET | `funds/disclosure-holders-search` | `name` | US |
| 9 | Disclosure Dates | GET | `funds/disclosure-dates` | `symbol` | US |

---

### 4.16 SEC Filings

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Latest 8-K | GET | `sec-filings-8k` | `from`, `to`, `page`, `limit` | US |
| 2 | Latest SEC Filings | GET | `sec-filings-financials` | `from`, `to`, `page`, `limit` | US |
| 3 | By Form Type | GET | `sec-filings-search/form-type` | `formType`, `from`, `to`, `page`, `limit` | US |
| 4 | By Symbol | GET | `sec-filings-search/symbol` | `symbol`, `from`, `to`, `page`, `limit` | US |
| 5 | By CIK | GET | `sec-filings-search/cik` | `cik`, `from`, `to`, `page`, `limit` | US |
| 6 | By Name | GET | `sec-filings-company-search/name` | `company` | US |
| 7 | By Symbol (Company) | GET | `sec-filings-company-search/symbol` | `symbol` | US |
| 8 | By CIK (Company) | GET | `sec-filings-company-search/cik` | `cik` | US |
| 9 | SEC Full Profile | GET | `sec-profile` | `symbol` | US |
| 10 | SIC Classification List | GET | `standard-industrial-classification-list` | — | US |
| 11 | SIC Classification Search | GET | `industry-classification-search` | `symbol`, `sicCode`, `industryTitle` | US |
| 12 | All SIC Classifications | GET | `all-industry-classification` | — | US |

---

### 4.17 Insider Trades

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Latest Insider Trading | GET | `insider-trading/latest` | `page`, `limit` | US |
| 2 | Search Insider Trades | GET | `insider-trading/search` | `symbol`, `page`, `limit` | US |
| 3 | By Reporting Name | GET | `insider-trading/reporting-name` | `name` | US |
| 4 | Transaction Types | GET | `insider-trading-transaction-type` | — | US |
| 5 | Trade Statistics | GET | `insider-trading/statistics` | `symbol` | US |
| 6 | Acquisition Ownership | GET | `acquisition-of-beneficial-ownership` | `symbol` | US |

**Insider Trade — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "filingDate": "2024-03-15",
    "transactionDate": "2024-03-13",
    "reportingCik": "0001214156",
    "reportingName": "COOK TIMOTHY D",
    "typeOfOwner": "officer",
    "acquistionOrDisposition": "D",
    "formType": "4",
    "securitiesOwned": 3280000,
    "securitiesTransacted": 400000,
    "price": 172.50,
    "securityName": "Common Stock",
    "link": "https://www.sec.gov/..."
  }
]
```

---

### 4.18 Indexes

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | Index List | GET | `index-list` | — |
| 2 | Index Quote | GET | `quote` | `symbol` (e.g. `^GSPC`) |
| 3 | Index Quote Short | GET | `quote-short` | `symbol` |
| 4 | All Index Quotes | GET | `batch-index-quotes` | `exchange` |
| 5 | Historical Light | GET | `historical-price-eod/light` | `symbol` (e.g. `^GSPC`), `from`, `to` |
| 6 | Historical Full | GET | `historical-price-eod/full` | `symbol`, `from`, `to` |
| 7 | 1-Min Intraday | GET | `historical-chart/1min` | `symbol`, `from`, `to` |
| 8 | 5-Min Intraday | GET | `historical-chart/5min` | `symbol`, `from`, `to` |
| 9 | 1-Hour Intraday | GET | `historical-chart/1hour` | `symbol`, `from`, `to` |
| 10 | S&P 500 Constituents | GET | `sp500-constituent` | — |
| 11 | Nasdaq Constituents | GET | `nasdaq-constituent` | — |
| 12 | Dow Jones Constituents | GET | `dowjones-constituent` | — |
| 13 | Historical S&P 500 | GET | `historical-sp500-constituent` | — |
| 14 | Historical Nasdaq | GET | `historical-nasdaq-constituent` | — |
| 15 | Historical Dow Jones | GET | `historical-dowjones-constituent` | — |

---

### 4.19 Market Hours

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Exchange Market Hours | GET | `exchange-market-hours` | `exchange` | Global |
| 2 | Holidays by Exchange | GET | `holidays-by-exchange` | `exchange` | Global |
| 3 | All Market Hours | GET | `all-exchange-market-hours` | — | Global |

---

### 4.20 Commodities

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | Commodities List | GET | `commodities-list` | — |
| 2 | Commodity Quote | GET | `quote` | `symbol` (e.g. `GCUSD`) |
| 3 | Commodity Quote Short | GET | `quote-short` | `symbol` |
| 4 | All Commodities Quotes | GET | `batch-commodity-quotes` | `exchange` |
| 5 | Light Chart | GET | `historical-price-eod/light` | `symbol`, `from`, `to` |
| 6 | Full Chart | GET | `historical-price-eod/full` | `symbol`, `from`, `to` |
| 7 | 1-Min Intraday | GET | `historical-chart/1min` | `symbol`, `from`, `to` |
| 8 | 5-Min Intraday | GET | `historical-chart/5min` | `symbol`, `from`, `to` |
| 9 | 1-Hour Intraday | GET | `historical-chart/1hour` | `symbol`, `from`, `to` |

---

### 4.21 Discounted Cash Flow

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | DCF Valuation | GET | `discounted-cash-flow` | `symbol` | Global |
| 2 | Levered DCF | GET | `levered-discounted-cash-flow` | `symbol` | Global |
| 3 | Custom DCF Advanced | GET | `custom-discounted-cash-flow` | `symbol` + various growth/discount rate params | Global |
| 4 | Custom DCF Levered | GET | `custom-levered-discounted-cash-flow` | `symbol` + various assumptions | Global |

**DCF — Response Schema:**

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-03-15",
    "dcf": 150.12,
    "stockPrice": 182.52
  }
]
```

---

### 4.22 Forex

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | Forex Pairs List | GET | `forex-list` | — |
| 2 | Forex Quote | GET | `quote` | `symbol` (e.g. `EURUSD`) |
| 3 | Forex Quote Short | GET | `quote-short` | `symbol` |
| 4 | All Forex Quotes | GET | `batch-forex-quotes` | `exchange` |
| 5 | Light Chart | GET | `historical-price-eod/light` | `symbol`, `from`, `to` |
| 6 | Full Chart | GET | `historical-price-eod/full` | `symbol`, `from`, `to` |
| 7 | 1-Min Intraday | GET | `historical-chart/1min` | `symbol`, `from`, `to` |
| 8 | 5-Min Intraday | GET | `historical-chart/5min` | `symbol`, `from`, `to` |
| 9 | 1-Hour Intraday | GET | `historical-chart/1hour` | `symbol`, `from`, `to` |

---

### 4.23 Crypto

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | Crypto List | GET | `crypto-list` | — |
| 2 | Crypto Quote | GET | `quote` | `symbol` (e.g. `BTCUSD`) |
| 3 | Crypto Quote Short | GET | `quote-short` | `symbol` |
| 4 | All Crypto Quotes | GET | `batch-crypto-quotes` | `exchange` |
| 5 | Light Chart | GET | `historical-price-eod/light` | `symbol`, `from`, `to` |
| 6 | Full Chart | GET | `historical-price-eod/full` | `symbol`, `from`, `to` |
| 7 | 1-Min Intraday | GET | `historical-chart/1min` | `symbol`, `from`, `to` |
| 8 | 5-Min Intraday | GET | `historical-chart/5min` | `symbol`, `from`, `to` |
| 9 | 1-Hour Intraday | GET | `historical-chart/1hour` | `symbol`, `from`, `to` |

---

### 4.24 Senate Trading

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | Latest Senate Trading | GET | `senate-trading` | `page`, `limit` | US |
| 2 | Senate Trading by Symbol | GET | `senate-trading` | `symbol` | US |
| 3 | Senate Disclosure | GET | `senate-disclosure` | `page`, `limit` | US |
| 4 | Senate Disclosure by Symbol | GET | `senate-disclosure` | `symbol` | US |

---

### 4.25 ESG

| # | Name | Method | Path | Key Params | Coverage |
|---|---|---|---|---|---|
| 1 | ESG Score | GET | `esg-environmental-social-governance-data` | `symbol` | Global |
| 2 | ESG Ratings | GET | `esg-environmental-social-governance-data-ratings` | `symbol` | Global |
| 3 | ESG Benchmark | GET | `esg-environmental-social-governance-sector-benchmark` | `year` | Global |

---

### 4.26 Commitment of Traders

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | COT List | GET | `commitment-of-traders-report-list` | — |
| 2 | COT Report | GET | `commitment-of-traders-report` | `symbol`, `from`, `to` |
| 3 | COT Analysis | GET | `commitment-of-traders-report-analysis` | `symbol`, `from`, `to` |

---

### 4.27 Fundraisers

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | Crowdfunding RSS | GET | `crowdfunding-rss` | `page`, `limit` |
| 2 | Crowdfunding Search | GET | `crowdfunding-search` | `name` |
| 3 | Crowdfunding by CIK | GET | `crowdfunding-by-cik` | `cik` |
| 4 | Equity Offering RSS | GET | `equity-offering-rss` | `page`, `limit` |
| 5 | Equity Offering Search | GET | `equity-offering-search` | `name` |
| 6 | Equity Offering by CIK | GET | `equity-offering-by-cik` | `cik` |

---

### 4.28 Bulk Endpoints

Bulk endpoints return large datasets for all symbols at once. Subject to rate limits (max 1 request per 10 seconds, profile/ETF bulk max 1 per 60 seconds).

| # | Name | Method | Path | Key Params |
|---|---|---|---|---|
| 1 | Profile Bulk | GET | `profile-bulk` | `part` (0–N) |
| 2 | Quote Bulk | GET | `batch-request-end-of-day-prices` | — |
| 3 | Income Statement Bulk | GET | `income-statement-bulk` | `year`, `period` |
| 4 | Balance Sheet Bulk | GET | `balance-sheet-statement-bulk` | `year`, `period` |
| 5 | Cash Flow Bulk | GET | `cash-flow-statement-bulk` | `year`, `period` |
| 6 | Ratios Bulk | GET | `ratios-bulk` | `year`, `period` |
| 7 | Key Metrics Bulk | GET | `key-metrics-bulk` | `year`, `period` |
| 8 | Earnings Surprise Bulk | GET | `earnings-surprises-bulk` | `year` |
| 9 | Scores Bulk | GET | `financial-scores-bulk` | `year` |
| 10 | ETF Holdings Bulk | GET | `etf-holdings-bulk` | `date` |

---

## 5. Response Schemas

### 5.1 Common Patterns

All FMP API responses share these characteristics:

- **Top-level JSON arrays** — every response is `[{...}, {...}, ...]` (even single-item results).
- **Empty arrays** `[]` for no results — never `null`.
- **Numeric fields** use JSON numbers (no strings for amounts).
- **Date strings** use `YYYY-MM-DD` format for dates, ISO-8601 for timestamps.
- **Symbol field** is always uppercase.
- **Snake_case or camelCase** — the API uses camelCase throughout (e.g., `marketCap`, `dayHigh`, `netIncome`).

### 5.2 DuckDB Table Mapping Guide

When creating typed DuckDB tables, use this mapping:

| JSON Type | DuckDB Type | Notes |
|---|---|---|
| String (symbol, name) | `VARCHAR` | |
| Date string (`YYYY-MM-DD`) | `DATE` | |
| Timestamp string | `TIMESTAMP` | |
| Integer amounts (revenue, volume) | `BIGINT` | Financials can exceed INT32 |
| Decimal amounts (price, ratio) | `DOUBLE` | |
| Boolean | `BOOLEAN` | |
| Nested object | `JSON` or flatten into columns | |

---

## 6. Error Handling

### 6.1 HTTP Status Codes

| Code | Meaning | Client Action |
|---|---|---|
| 200 | Success | Parse JSON array |
| 401 | Invalid API key | Check `apikey` parameter or header |
| 403 | Plan limit exceeded | Upgrade plan or reduce requests |
| 429 | Rate limited | Back off and retry with exponential delay |
| 404 | Endpoint not found | Check URL path |
| 500 | Server error | Retry after delay |

### 6.2 Error Response Format

```json
{
  "Error Message": "Invalid API KEY. Please retry or visit our documentation."
}
```

### 6.3 Recommended Retry Strategy

```python
import time

MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds

def fetch_with_retry(url: str, params: dict) -> list[dict]:
    for attempt in range(MAX_RETRIES):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 429:
            delay = BASE_DELAY * (2 ** attempt)
            time.sleep(delay)
            continue
        response.raise_for_status()
    raise Exception(f"Failed after {MAX_RETRIES} retries")
```

---

## 7. Rate Limits & Best Practices

### 7.1 Rate Limits

| Plan | Requests/sec | Daily Limit | Bandwidth/30 days |
|---|---|---|---|
| Free | ~5 | 250 | Limited |
| Starter | ~10 | 10,000 | Moderate |
| Premium | ~30 | 100,000+ | High |
| Enterprise | Custom | Unlimited | Custom |

**Bulk endpoint limits:** max 1 request per 10 seconds (profile/ETF bulk: 1 per 60 seconds).

### 7.2 Client Implementation Best Practices

1. **Always use the DuckDB cache** before hitting the API. Even a 60-second TTL prevents redundant calls.

2. **Batch requests where possible.** Use `batch-quote` with `symbols=AAPL,MSFT,GOOG` instead of 3 individual calls.

3. **Use bulk endpoints for initial data loads.** Populate your DuckDB database with bulk endpoints, then use individual endpoints for incremental updates.

4. **Respect rate limits.** Implement token-bucket or leaky-bucket rate limiting in your client.

5. **Use header-based auth** (`apikey: KEY`) to keep URLs clean and loggable.

6. **Date range chunking.** For endpoints with max 3-month or 5-year ranges, loop over intervals:

   ```python
   def chunked_date_ranges(start: str, end: str, max_days: int = 90):
       """Yield (from, to) date tuples covering the full range."""
       from datetime import datetime, timedelta
       s = datetime.strptime(start, "%Y-%m-%d")
       e = datetime.strptime(end, "%Y-%m-%d")
       while s < e:
           chunk_end = min(s + timedelta(days=max_days), e)
           yield s.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")
           s = chunk_end + timedelta(days=1)
   ```

7. **Store raw JSON alongside typed tables.** The `_raw_cache` table provides a safety net if the typed schema doesn't capture all fields.

8. **DuckDB analytical queries.** Leverage DuckDB's full SQL to run analytics over cached data:

   ```sql
   -- Compare P/E ratios across a sector
   SELECT symbol, pe, market_cap
   FROM quotes
   WHERE symbol IN (SELECT symbol FROM screener_results WHERE sector = 'Technology')
   ORDER BY pe ASC;

   -- Revenue growth trend
   SELECT symbol, calendar_year, revenue,
          revenue - LAG(revenue) OVER (PARTITION BY symbol ORDER BY date) AS yoy_change
   FROM income_statements
   WHERE symbol = 'AAPL' AND period = 'FY'
   ORDER BY date;

   -- Find insider buying clusters
   SELECT symbol, COUNT(*) as buy_count, SUM(securities_transacted * price) as total_value
   FROM insider_trades
   WHERE acquisition_or_disposition = 'A'
     AND transaction_date > CURRENT_DATE - INTERVAL '30 days'
   GROUP BY symbol
   HAVING buy_count >= 3
   ORDER BY total_value DESC;
   ```

9. **Timezone awareness.** NYSE/NASDAQ data uses EST. LSE uses GMT. Forex uses EST. Store timestamps in UTC in DuckDB and convert on read.

10. **Handle empty responses gracefully.** Some symbols or date ranges return `[]`. Your client should return an empty DataFrame or list without raising errors.

---

*Specification generated from FMP stable API documentation. Endpoint availability depends on subscription plan. Verify current parameters and response fields against the live [API Viewer](https://site.financialmodelingprep.com/playground).*