# Feature Catalogue

`jaymd96-fmp` ships 362 computed features across 24 categories. Every feature is available through the query builder -- you just `.select()` it by name, and the library resolves dependencies, generates SQL, and applies post-compute transforms automatically.

## How features work

Features are built in three layers:

1. **Base fields** -- raw data from FMP API endpoints, stored in DuckDB tables. These are defined in the ontology (`_ontology.py`) and include things like `revenue`, `close`, `total_assets`.

2. **SQL-derived features (DerivedFieldDef)** -- computed as DuckDB SQL expressions over base fields. These run inside the generated CTE query. Examples: `gross_profit_margin`, `altman_z_score`, `revenue_growth_yoy`. There are 332 of these.

3. **Post-compute features (PostComputeFieldDef)** -- computed in polars after the SQL query returns. These handle calculations that cannot be expressed as single-pass SQL: recursive EMA, cross-asset beta, cumulative streak logic, and live API lookups (insider trades, senate trades, analyst grades). There are 30 of these.

```
FMP API  -->  DuckDB tables (base fields)
                    |
                    v
              SQL query (CTEs + QUALIFY dedup + ASOF JOIN)
                    |
                    +---> DerivedFieldDef expressions (inline SQL)
                    |
                    v
              polars DataFrame
                    |
                    +---> PostComputeFieldDef transforms (EMA, MACD, beta, streaks)
                    |
                    v
              Final DataFrame
```

## Feature categories

### profitability (20)

Margins, return ratios, and NOPAT. Measures how effectively a company converts revenue into profit.

Examples: `gross_profit_margin`, `operating_profit_margin`, `net_profit_margin`, `roe_computed`, `roa_computed`, `roic_computed`, `nopat`, `ebitda_margin`, `rd_to_revenue`, `sga_to_revenue`, `effective_tax_rate`.

### liquidity (13)

Current, quick, and cash ratios plus working capital metrics. Measures a company's ability to meet short-term obligations.

Examples: `current_ratio_computed`, `quick_ratio_computed`, `cash_ratio_computed`, `working_capital`, `working_capital_to_revenue`, `cash_to_assets`, `cash_to_debt`, `defensive_interval`.

### leverage (17)

Debt ratios, coverage ratios, and capital structure metrics. Measures financial risk from debt.

Examples: `debt_to_equity_computed`, `debt_to_assets_computed`, `net_debt_to_ebitda`, `interest_coverage_computed`, `debt_to_capital`, `long_term_debt_to_equity`, `equity_multiplier`, `fixed_charge_coverage`.

### efficiency (20)

Asset turnover, expense ratios, and operational efficiency metrics.

Examples: `asset_turnover_computed`, `inventory_turnover_computed`, `receivables_turnover_computed`, `payables_turnover`, `cash_conversion_cycle`, `fixed_asset_turnover`, `working_capital_turnover`, `capex_to_revenue`.

### valuation (22)

PE, PB, EV multiples, yields, and relative valuation metrics.

Examples: `pe_ratio_computed`, `pb_ratio_computed`, `price_to_sales`, `ev_to_ebitda_computed`, `ev_to_revenue`, `ev_to_fcf_computed`, `earnings_yield_computed`, `fcf_yield_computed`, `peg_ratio`, `price_to_tangible_book`.

### cash_flow (14)

Free cash flow quality, accrual metrics, and reinvestment ratios.

Examples: `fcf_margin`, `fcf_to_net_income`, `operating_cash_flow_margin`, `accrual_ratio`, `capex_to_operating_cf`, `reinvestment_rate`, `cash_return_on_capital`, `fcf_to_debt`.

### growth (30)

Year-over-year growth rates, multi-year CAGRs, and growth consistency metrics. Most use `LAG` window functions.

Examples: `revenue_growth_yoy`, `net_income_growth`, `eps_growth_yoy`, `fcf_growth`, `asset_growth`, `book_value_growth`, `revenue_cagr_3y`, `revenue_cagr_5y`, `revenue_cagr_10y`, `eps_cagr_3y`, `eps_cagr_5y`, `eps_cagr_10y`, `dividend_growth_3y`, `dividend_growth_5y`, `revenue_growth_consistency`, `sustainable_growth_rate`, `share_count_change`.

### dupont (7)

Three-factor and five-factor DuPont decomposition of ROE.

Examples: `dupont_roe`, `dupont_profit_margin`, `dupont_asset_turnover`, `dupont_equity_multiplier`, `dupont_tax_burden`, `dupont_interest_burden`, `dupont_operating_margin`.

### earnings_quality (17)

Sloan accrual ratio, Beneish M-Score components, and earnings persistence indicators.

Examples: `sloan_accrual_ratio`, `beneish_dsri`, `beneish_gmi`, `beneish_aqi`, `beneish_sgi`, `beneish_depi`, `beneish_sgai`, `beneish_lvgi`, `beneish_tata`, `earnings_persistence`, `cash_earnings_ratio`, `earnings_smoothness`.

### per_share (11)

Per-share financial metrics.

Examples: `book_value_per_share`, `tangible_bvps`, `revenue_per_share`, `net_income_per_share`, `fcf_per_share_computed`, `operating_cf_per_share`, `cash_per_share_computed`, `ebitda_per_share`, `debt_per_share`.

### dividend (12)

Dividend yields, payout ratios, and dividend coverage metrics. Includes the post-compute `consecutive_dividend_increases` streak counter.

Examples: `dividend_yield_computed`, `dividend_payout_ratio`, `dividend_coverage`, `fcf_payout_ratio`, `dividend_to_fcf`, `dividend_per_share_growth`, `consecutive_dividend_increases` (post-compute).

### risk (22)

Volatility, drawdown, Value-at-Risk, beta, and ATR. Includes post-compute cross-asset beta and Jensen's alpha.

Examples: `volatility_21d`, `volatility_63d`, `volatility_252d`, `max_drawdown_63d`, `max_drawdown_252d`, `var_95_21d`, `var_99_21d`, `atr_14`, `atr_21`, `sharpe_ratio_252d`, `sortino_ratio_252d`, `downside_volatility_252d`, `beta_sp500` (post-compute), `alpha_jensen` (post-compute).

### technical (38)

Moving averages (SMA/EMA), Bollinger Bands, MACD, RSI, and other technical indicators. EMAs and MACD are post-compute (polars); SMAs and Bollinger Bands are SQL-derived.

Examples: `sma_10`, `sma_20`, `sma_50`, `sma_200`, `ema_12` (post-compute), `ema_20` (post-compute), `ema_50` (post-compute), `ema_200` (post-compute), `bollinger_upper_20`, `bollinger_lower_20`, `bollinger_width_20`, `macd_line` (post-compute), `macd_signal` (post-compute), `macd_histogram` (post-compute), `rsi_14`, `price_to_sma_50`, `price_to_sma_200`, `golden_cross`, `death_cross`, `volume_sma_20`.

### momentum (15)

Multi-period returns, mean reversion signals, and return autocorrelation. Includes the post-compute `return_autocorrelation_21d`.

Examples: `return_5d`, `return_21d`, `return_63d`, `return_126d`, `return_252d`, `momentum_12_1`, `mean_reversion_21d`, `return_autocorrelation_21d` (post-compute), `return_skew_63d`, `return_kurtosis_63d`.

### composite (20)

Multi-factor scoring models computed from underlying fundamentals.

Examples: `altman_z_score`, `altman_z_prime`, `altman_z_double_prime`, `piotroski_f_score`, `beneish_m_score`, `graham_number`, `graham_value_flag`, `magic_formula_rank_proxy`, `quality_score`, `value_momentum_composite`, `defensive_quality_score`, `earnings_power_value`.

### analyst (15)

Analyst consensus, estimates, target price upside, and grade change counts. Includes post-compute `upgrades_90d`, `downgrades_90d`, and `upgrade_downgrade_ratio`.

Examples: `consensus_score`, `buy_pct`, `sell_pct`, `analyst_count`, `eps_surprise`, `revenue_surprise`, `target_upside`, `estimate_dispersion`, `upgrades_90d` (post-compute), `downgrades_90d` (post-compute), `upgrade_downgrade_ratio` (post-compute).

### macro (9)

Yield curve metrics and risk-free rate. Uses the `treasury_rates` dataset which has no symbol key -- joins on date only.

Examples: `yield_curve_slope`, `yield_curve_10y_3m`, `yield_curve_10y_2y`, `risk_free_rate`, `term_premium_10y`, `real_rate_proxy`, `credit_spread_proxy`.

### historical (19)

Point-in-time valuation multiples and scores using daily market cap instead of quarterly snapshots. Critical for avoiding look-ahead bias in backtesting.

Examples: `hist_pe_daily`, `hist_ps_daily`, `hist_pb_daily`, `hist_ev_daily`, `hist_ev_to_ebitda_daily`, `hist_earnings_yield_daily`, `hist_fcf_yield_daily`, `hist_altman_z_daily`, `hist_consensus_score`, `hist_buy_pct`, `hist_inst_ownership_growth`.

### institutional (7)

Institutional holder counts and investment flow metrics from 13F filings.

Examples: `inst_holders_growth`, `inst_investment_growth`, `inst_concentration`, `inst_new_positions_pct`, `inst_put_call_signal`.

### event_driven (15)

IPO age, pre-computed multi-period returns, and index membership checks. Includes post-compute index membership flags.

Examples: `ipo_age_days`, `ipo_age_years`, `fmp_return_1m_annualised`, `fmp_return_12m_excess`, `in_sp500` (post-compute), `in_nasdaq` (post-compute), `in_dowjones` (post-compute).

### esg (4)

ESG composite and pillar scores.

Examples: `esg_total_score`, `esg_env_score`, `esg_social_score`, `esg_gov_score`.

### insider (8)

Insider trading aggregations over rolling windows. All are post-compute features that fetch live insider trade data.

Examples: `insider_net_buying_90d`, `insider_buy_count_30d`, `insider_sell_count_30d`, `insider_buy_sell_ratio_90d`, `insider_buying_cluster`, `insider_total_bought_90d`, `insider_total_sold_90d`, `insider_officer_buying`.

### senate (4)

Congressional trading signal features. All are post-compute features that fetch live senate trade data.

Examples: `senate_buy_count_90d`, `senate_sell_count_90d`, `senate_net_flow_90d`, `senate_activity_flag`.

### index_membership (3)

Boolean flags for major index membership. All are post-compute features that query constituent lists.

Examples: `in_sp500`, `in_nasdaq`, `in_dowjones`.

## Discovering features

### List all features

```python
from fmp import list_features

# All 362 feature names
all_features = list_features()
print(len(all_features))  # 362
```

### Filter by category

```python
# Just profitability features
profitability = list_features("profitability")
# ['gross_profit_margin', 'operating_profit_margin', 'net_profit_margin', ...]
```

### List all categories

```python
from fmp import feature_categories

cats = feature_categories()
# ['analyst', 'cash_flow', 'composite', 'dividend', 'dupont', ...]
```

### List all fields (base + derived + post-compute)

```python
from fmp import list_fields

# All queryable field names (base ontology fields + derived features + post-compute)
all_fields = list_fields()

# Fields for a specific dataset
daily_fields = list_fields("daily_price")
# ['open', 'high', 'low', 'close', 'adj_close', 'volume', 'vwap', 'change', 'change_pct']
```

## Using features in queries

Features are used through the query builder's `.select()` method. You can mix base fields, SQL-derived features, and post-compute features freely:

```python
from fmp import FMPClient

client = FMPClient()

# Mix base fields with derived and post-compute features
df = (client.query()
    .symbols("AAPL", "MSFT")
    .select(
        "close",                   # base field (daily_price)
        "revenue",                 # base field (income_statement)
        "gross_profit_margin",     # SQL-derived (profitability)
        "altman_z_score",          # SQL-derived (composite)
        "revenue_growth_yoy",      # SQL-derived with LAG (growth)
        "ema_20",                  # post-compute (technical)
        "beta_sp500",              # post-compute with reference data (risk)
    )
    .date_range("2023-01-01", "2024-12-31")
    .execute()
)
```

The query builder handles everything automatically:
- Resolves which datasets each field needs (daily_price, income_statement, balance_sheet, etc.)
- Fetches data from the API if not already cached
- Generates CTE-based SQL with QUALIFY dedup
- Uses ASOF JOIN to align quarterly data to daily frequency
- Computes SQL-derived expressions inline
- Applies post-compute transforms in polars
- Fetches reference data for cross-asset features (e.g., S&P 500 for beta)

## Post-compute features explained

Post-compute features run in polars after the SQL query returns. They exist because some calculations cannot be expressed as single-pass DuckDB SQL:

### EMA (Exponential Moving Averages)
EMAs are recursive: each value depends on the previous EMA value. Polars' `ewm_mean` handles this natively.

Features: `ema_12`, `ema_20`, `ema_26`, `ema_50`, `ema_200`

### MACD (Moving Average Convergence Divergence)
MACD requires two EMAs plus an EMA of their difference (the signal line). Three nested recursive computations.

Features: `macd_line` (EMA12 - EMA26), `macd_signal` (EMA9 of MACD line), `macd_histogram` (MACD line - signal)

### Beta and Alpha
Rolling 252-day beta vs S&P 500 requires fetching market return data (`^GSPC`) and computing rolling covariance/variance. The `reference_symbols` attribute on the `PostComputeFieldDef` tells the query builder to automatically fetch the benchmark data.

Features: `beta_sp500`, `alpha_jensen`

### Consecutive dividend streaks
Cumulative conditional logic: count how many consecutive periods the dividend increased. Requires iterative state tracking.

Feature: `consecutive_dividend_increases`

### Return autocorrelation
Lag-1 autocorrelation of daily returns over a 21-day rolling window. Requires nested rolling window computations.

Feature: `return_autocorrelation_21d`

### Live API features (insider, senate, analyst grades)
These fetch data from FMP API endpoints at query time, aggregate it, and merge it with the main DataFrame. Results are cached within the query execution context.

Features: `insider_net_buying_90d`, `senate_buy_count_90d`, `upgrades_90d`, etc.

**Important:** Post-compute features require `backend='polars'` (the default). Using `backend='pandas'` with post-compute features will raise an error.

## Adding new features (for developers)

### Adding a SQL-derived feature

1. Choose the appropriate category module in `src/fmp/_features/` (e.g., `profitability.py`).
2. Add a `DerivedFieldDef` using the `_d()` shorthand:

```python
from fmp._features._base import _d

# In the FEATURES list:
_d(
    "my_new_ratio",                           # unique snake_case name
    "net_income / NULLIF(total_assets, 0)",    # DuckDB SQL expression
    ("net_income", "total_assets"),            # base field dependencies
    category="profitability",                  # category label
)
```

If your expression uses `LAG()` or `LEAD()`, set `lag=True`. The query builder will add `WINDOW w AS (PARTITION BY symbol ORDER BY date)` and you can reference `OVER w` in your expression.

3. The feature is automatically registered via the module's `FEATURES` list and the `__init__.py` aggregation.

### Adding a post-compute feature

1. Add the compute function and `PostComputeFieldDef` in `_post_compute.py`:

```python
def _my_compute(df, ctx):
    import polars as pl
    # df has all dependency columns; ctx has reference_data, http, etc.
    return df.sort("symbol", "date").group_by("symbol", maintain_order=True).agg(
        pl.col("close").rolling_mean(window_size=42).alias("_result")
    ).explode("_result")["_result"]

# In POST_COMPUTE_FEATURES list:
PostComputeFieldDef(
    "my_post_compute_feature",   # unique name
    _my_compute,                  # compute function
    ("close",),                   # base field dependencies
    category="technical",
    reference_symbols=(),         # add ("^GSPC",) if you need market data
)
```

2. The feature is automatically registered via `POST_COMPUTE_REGISTRY`.

### Dependencies

The `dependencies` tuple must contain only base ontology field names (not other derived features). The query builder uses these to determine which datasets to fetch and which columns to include in the SQL query.
