"""Configuration constants for the FMP client."""

from __future__ import annotations

BASE_URL = "https://financialmodelingprep.com/stable/"

# TTL values in seconds, keyed by category name.
# Override at client init via ttl_overrides={...}.
DEFAULT_TTLS: dict[str, int] = {
    "realtime_quotes": 60,
    "aftermarket": 60,
    "intraday_charts": 300,          # 5 min
    "daily_historical": 86_400,      # 24 h
    "financial_statements": 604_800, # 7 days
    "company_profiles": 86_400,
    "key_metrics": 604_800,
    "news": 900,                     # 15 min
    "earnings_calendar": 21_600,     # 6 h
    "sec_filings": 86_400,
    "insider_trades": 3_600,         # 1 h
    "economic_indicators": 86_400,
    "etf_fund_holdings": 86_400,
    "index_constituents": 86_400,
    "market_hours": 604_800,
    "screener": 600,                 # 10 min
    "bulk_data": 86_400,
    "static_lists": 2_592_000,       # 30 days
    "analyst": 86_400,
    "market_performance": 600,
    "technical_indicators": 300,
    "senate": 3_600,
    "esg": 604_800,
    "cot": 86_400,
    "fundraisers": 86_400,
    "dcf": 86_400,
    "transcripts": 604_800,
    "default": 3_600,                # 1 h fallback
}
