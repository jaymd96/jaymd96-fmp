# Point-in-Time Data Guide

## Why point-in-time matters

Standard financial datasets use **snapshot** valuation multiples: the PE ratio from the most recent quarterly filing. When backtesting a strategy, this creates **look-ahead bias** -- the snapshot PE on 2024-01-15 uses a market cap calculated at filing time (e.g., 2024-02-10), not the actual market cap on January 15th.

The difference is material. A company trading at $150 on January 15th might have been at $180 when the quarterly metrics were filed a month later. Using the filing-date market cap inflates the PE ratio by 20% for every trading day before the filing.

Point-in-time data solves this by using the actual daily market cap to compute valuation metrics, giving you the PE ratio an investor would have actually seen on any given day.

## Historical datasets

The ontology includes four historical datasets with daily or monthly granularity:

### historical_market_cap

Daily market capitalisation for each symbol. The foundation for all point-in-time valuation metrics.

- Endpoint: `historical-market-capitalization`
- Grain: `DAILY`
- Keys: `(symbol, date)`
- Fields: `hist_market_cap` (BIGINT)

### historical_grades

Monthly analyst consensus breakdown (strong buy / buy / hold / sell / strong sell counts).

- Endpoint: `grades-historical`
- Grain: `MONTHLY`
- Keys: `(symbol, date)`
- Fields: `hist_strong_buy`, `hist_buy`, `hist_hold`, `hist_sell`, `hist_strong_sell` (all INTEGER)

### historical_ratings

Monthly FMP proprietary rating scores.

- Endpoint: `ratings-historical`
- Grain: `MONTHLY`
- Keys: `(symbol, date)`
- Fields: `hist_rating` (VARCHAR), `hist_overall_score`, `hist_dcf_score`, `hist_roe_score`, `hist_roa_score`, `hist_de_score`, `hist_pe_score`, `hist_pb_score` (all INTEGER)

### historical_institutional

Quarterly institutional ownership summary from 13F filings.

- Endpoint: `institutional-ownership/symbol-positions-summary`
- Grain: `QUARTERLY`
- Keys: `(symbol, date)`
- Fields: `hist_inst_holders`, `hist_inst_holders_change`, `hist_inst_invested`, `hist_inst_invested_change`, `hist_inst_ownership_pct`, `hist_inst_new_positions`, `hist_inst_closed_positions`, `hist_inst_put_call_ratio`

## Historical derived features

These 19 features use `hist_market_cap` and other historical base fields to compute point-in-time metrics:

### Daily valuation multiples

| Feature | Formula | Category |
|---------|---------|----------|
| `hist_pe_daily` | `hist_market_cap / net_income` | historical |
| `hist_ps_daily` | `hist_market_cap / revenue` | historical |
| `hist_pb_daily` | `hist_market_cap / total_stockholders_equity` | historical |
| `hist_ev_daily` | `hist_market_cap + total_debt - cash_and_equivalents` | historical |
| `hist_ev_to_ebitda_daily` | `hist_ev / ebitda` | historical |
| `hist_ev_to_revenue_daily` | `hist_ev / revenue` | historical |
| `hist_ev_to_fcf_daily` | `hist_ev / free_cash_flow` | historical |
| `hist_earnings_yield_daily` | `net_income / hist_market_cap` | historical |
| `hist_fcf_yield_daily` | `free_cash_flow / hist_market_cap` | historical |
| `hist_dividend_yield_daily` | `abs(dividends_paid) / hist_market_cap` | historical |
| `hist_shares_outstanding` | `hist_market_cap / close` | historical |
| `hist_market_cap_growth` | YoY growth of `hist_market_cap` | historical |

### Daily Altman Z-Score

`hist_altman_z_daily` uses the standard Altman Z-Score formula but substitutes `hist_market_cap` for the snapshot market cap in the equity/liabilities ratio component. This gives a true point-in-time bankruptcy risk score.

### Historical analyst consensus

| Feature | Description |
|---------|-------------|
| `hist_consensus_score` | Weighted average (strong buy=5 ... strong sell=1) |
| `hist_buy_pct` | Fraction of analysts rating buy or strong buy |
| `hist_sell_pct` | Fraction of analysts rating sell or strong sell |
| `hist_analyst_count` | Total number of analyst ratings |

### Historical institutional ownership

| Feature | Description |
|---------|-------------|
| `hist_inst_ownership_growth` | Period-over-period change in institutional holder count |
| `hist_inst_investment_growth` | Period-over-period change in total institutional investment |

## Example: snapshot PE vs point-in-time PE

```python
from fmp import FMPClient

client = FMPClient()

# Sync the required data
client.sync(
    symbols=["AAPL"],
    datasets=["daily_price", "income_statement", "key_metrics", "historical_market_cap"],
    start="2023-01-01", end="2024-12-31",
)

# Query both snapshot and point-in-time PE
df = (client.query()
    .symbols("AAPL")
    .select(
        "close",
        "pe_ratio",       # snapshot: uses market_cap from key_metrics (quarterly)
        "hist_pe_daily",  # point-in-time: uses hist_market_cap (daily)
    )
    .date_range("2023-01-01", "2024-12-31")
    .auto_fetch(False)
    .execute()
)

print(df.select("date", "close", "pe_ratio", "hist_pe_daily").head(10))
```

The snapshot `pe_ratio` stays constant between quarterly filings (it was calculated using a fixed market cap), while `hist_pe_daily` changes every day as the market cap fluctuates with the stock price. For backtesting, `hist_pe_daily` is the correct value to use -- it reflects what an investor would have actually calculated on that date.

## Syncing historical data

Historical datasets are per-symbol timeseries. Sync them like any other dataset:

```python
# Sync daily market cap history for specific symbols
client.sync(
    symbols=["AAPL", "MSFT", "GOOG"],
    datasets=["historical_market_cap"],
    start="2015-01-01", end="2024-12-31",
)

# Sync monthly analyst grades history
client.sync(
    symbols=["AAPL", "MSFT", "GOOG"],
    datasets=["historical_grades"],
    start="2015-01-01", end="2024-12-31",
)

# Sync quarterly institutional ownership history
# This one uses multi-period sync (iterates year/quarter combos)
client.sync(
    symbols=["AAPL"],
    datasets=["historical_institutional"],
    start="2020-01-01", end="2024-12-31",
)

# Estimate API calls before syncing
est = client.estimate_sync_calls(
    symbols=["AAPL", "MSFT", "GOOG"],
    datasets=["historical_market_cap", "historical_grades"],
    start="2015-01-01", end="2024-12-31",
)
print(est)  # {'historical_market_cap': 3, 'historical_grades': 3, '_total': 6}
```

For a full universe backtest, sync the entire S&P 500:

```python
client.sync_universe(
    "sp500",
    datasets=["daily_price", "income_statement", "balance_sheet",
              "cash_flow", "historical_market_cap"],
    start="2015-01-01", end="2024-12-31",
    on_progress=lambda ds, msg: print(f"  [{ds}] {msg}"),
)
```

## How ASOF joins align quarterly data to daily frequency

The key insight: financial statements are filed quarterly, but stock prices move daily. When you query `hist_pe_daily`, the expression `hist_market_cap / net_income` needs both:
- `hist_market_cap` -- available daily from `historical_market_cap`
- `net_income` -- available quarterly from `income_statement`

The query builder handles this with **ASOF JOIN**:

```sql
-- hist_market_cap is daily (anchor)
-- net_income is quarterly (coarser)
FROM historical_market_cap_dedup t0
ASOF JOIN income_statement_dedup t1
  ON t0.symbol = t1.symbol AND t0.date >= t1.date
```

The ASOF JOIN matches each daily row with the most recent quarterly row on or before that date. So on 2024-02-15, it uses:
- `hist_market_cap` from 2024-02-15 (daily, exact match)
- `net_income` from Q4 2023 filing (the most recent quarterly data available)

This is the correct behaviour for point-in-time analysis: on February 15th, an investor would only have access to the Q4 financials, not the Q1 numbers that won't be filed until April.

The ASOF JOIN is applied automatically by the query builder whenever a coarser-grained dataset (quarterly, annual) is combined with a finer-grained dataset (daily). The coarser dataset's start-date filter is intentionally omitted so that preceding data is available for the carry-forward.

### Grain alignment summary

| Source grain | Target grain | Strategy |
|-------------|-------------|----------|
| Daily -> Daily | Exact join on date |
| Quarterly -> Daily | ASOF JOIN (carry forward latest) |
| Daily -> Monthly | Roll up with aggregation (DATE_TRUNC + agg function) |
| Snapshot -> Daily | LEFT JOIN on symbol only |
| Date-only -> Daily | LEFT JOIN on date only |
