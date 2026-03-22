"""Ontology: declarative schema mapping fields → datasets → FMP endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Grain(IntEnum):
    """Temporal granularity of a dataset. Lower = finer."""

    INTRADAY = 0
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3
    QUARTERLY = 4
    ANNUAL = 5
    SNAPSHOT = 99  # outside the hierarchy

    @classmethod
    def parse(cls, value: str) -> Grain:
        return cls[value.upper()]

    @property
    def trunc_unit(self) -> str:
        """DuckDB DATE_TRUNC unit for this grain."""
        return {
            Grain.DAILY: "day",
            Grain.WEEKLY: "week",
            Grain.MONTHLY: "month",
            Grain.QUARTERLY: "quarter",
            Grain.ANNUAL: "year",
        }.get(self, "day")


@dataclass(frozen=True, slots=True)
class FieldDef:
    """A single field within a dataset."""

    name: str       # snake_case column name in DuckDB
    api_name: str   # camelCase field name in the API response
    dtype: str      # DuckDB column type: DOUBLE, BIGINT, VARCHAR, DATE, etc.
    agg: str        # default rollup aggregation: first, last, sum, mean, max, min


@dataclass(frozen=True, slots=True)
class DatasetDef:
    """A logical dataset backed by one FMP endpoint."""

    name: str
    endpoint: str
    grain: Grain
    keys: tuple[str, ...]
    ttl_category: str
    fields: dict[str, FieldDef]


# ──────────────────────────────────────────────────────────────────────
# Helper to build fields concisely
# ──────────────────────────────────────────────────────────────────────

def _f(name: str, api: str, dtype: str = "DOUBLE", agg: str = "last") -> FieldDef:
    return FieldDef(name=name, api_name=api, dtype=dtype, agg=agg)


# ──────────────────────────────────────────────────────────────────────
# Dataset definitions
# ──────────────────────────────────────────────────────────────────────

_DAILY_PRICE = DatasetDef(
    name="daily_price",
    endpoint="historical-price-eod/full",
    grain=Grain.DAILY,
    keys=("symbol", "date"),
    ttl_category="daily_historical",
    fields={
        "open":       _f("open",      "open",            agg="first"),
        "high":       _f("high",      "high",            agg="max"),
        "low":        _f("low",       "low",             agg="min"),
        # Note: the stable API's close IS already split-adjusted.
        # adjClose is not returned by the stable API; kept for v3 compat.
        "close":      _f("close",     "close",           agg="last"),
        "adj_close":  _f("adj_close", "adjClose",          agg="last"),
        "volume":     _f("volume",    "volume", "BIGINT", agg="sum"),
        "vwap":       _f("vwap",      "vwap",            agg="mean"),
        "change":     _f("change",    "change",          agg="sum"),
        "change_pct": _f("change_pct","changePercent",   agg="sum"),
    },
)

_INCOME_STATEMENT = DatasetDef(
    name="income_statement",
    endpoint="income-statement",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date", "period"),
    ttl_category="financial_statements",
    fields={
        "reported_currency":   _f("reported_currency",   "reportedCurrency", "VARCHAR"),
        "cik":                 _f("cik",                 "cik",              "VARCHAR"),
        "filling_date":        _f("filling_date",        "filingDate",       "DATE"),
        "accepted_date":       _f("accepted_date",       "acceptedDate",     "VARCHAR"),
        "calendar_year":       _f("calendar_year",       "fiscalYear",       "VARCHAR"),
        "revenue":             _f("revenue",             "revenue",          "BIGINT", agg="sum"),
        "cost_of_revenue":     _f("cost_of_revenue",     "costOfRevenue",    "BIGINT", agg="sum"),
        "gross_profit":        _f("gross_profit",        "grossProfit",      "BIGINT", agg="sum"),
        "rd_expenses":         _f("rd_expenses",         "researchAndDevelopmentExpenses", "BIGINT", agg="sum"),
        "sga_expenses":        _f("sga_expenses",        "sellingGeneralAndAdministrativeExpenses", "BIGINT", agg="sum"),
        "operating_expenses":  _f("operating_expenses",  "operatingExpenses","BIGINT", agg="sum"),
        "operating_income":    _f("operating_income",    "operatingIncome",  "BIGINT", agg="sum"),
        "interest_income":     _f("interest_income",     "interestIncome",   "BIGINT", agg="sum"),
        "interest_expense":    _f("interest_expense",    "interestExpense",  "BIGINT", agg="sum"),
        "ebitda":              _f("ebitda",              "ebitda",           "BIGINT", agg="sum"),
        "net_income":          _f("net_income",          "netIncome",        "BIGINT", agg="sum"),
        "eps":                 _f("eps",                 "eps",              agg="sum"),
        "eps_diluted":         _f("eps_diluted",         "epsDiluted",       agg="sum"),
        "weighted_avg_shares": _f("weighted_avg_shares", "weightedAverageShsOut", "BIGINT", agg="last"),
        "weighted_avg_shares_diluted": _f("weighted_avg_shares_diluted", "weightedAverageShsOutDil", "BIGINT", agg="last"),
        "income_before_tax":   _f("income_before_tax",   "incomeBeforeTax",  "BIGINT", agg="sum"),
        "income_tax_expense":  _f("income_tax_expense",  "incomeTaxExpense", "BIGINT", agg="sum"),
        "depreciation_and_amortization": _f("depreciation_and_amortization", "depreciationAndAmortization", "BIGINT", agg="sum"),
        "cost_and_expenses":   _f("cost_and_expenses",   "costAndExpenses",  "BIGINT", agg="sum"),
        "other_expenses":      _f("other_expenses",      "otherExpenses",    "BIGINT", agg="sum"),
        "total_other_income":  _f("total_other_income",  "totalOtherIncomeExpensesNet", "BIGINT", agg="sum"),
    },
)

_BALANCE_SHEET = DatasetDef(
    name="balance_sheet",
    endpoint="balance-sheet-statement",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date", "period"),
    ttl_category="financial_statements",
    fields={
        "reported_currency":         _f("reported_currency",         "reportedCurrency",         "VARCHAR"),
        "cik":                       _f("cik",                       "cik",                      "VARCHAR"),
        "filling_date":              _f("filling_date",              "filingDate",               "DATE"),
        "calendar_year":             _f("calendar_year",             "fiscalYear",               "VARCHAR"),
        "cash_and_equivalents":      _f("cash_and_equivalents",      "cashAndCashEquivalents",   "BIGINT"),
        "short_term_investments":    _f("short_term_investments",    "shortTermInvestments",     "BIGINT"),
        "net_receivables":           _f("net_receivables",           "netReceivables",           "BIGINT"),
        "inventory":                 _f("inventory",                 "inventory",                "BIGINT"),
        "total_current_assets":      _f("total_current_assets",      "totalCurrentAssets",       "BIGINT"),
        "property_plant_equipment":  _f("property_plant_equipment",  "propertyPlantEquipmentNet","BIGINT"),
        "goodwill":                  _f("goodwill",                  "goodwill",                 "BIGINT"),
        "intangible_assets":         _f("intangible_assets",         "intangibleAssets",         "BIGINT"),
        "total_non_current_assets":  _f("total_non_current_assets",  "totalNonCurrentAssets",    "BIGINT"),
        "total_assets":              _f("total_assets",              "totalAssets",              "BIGINT"),
        "accounts_payable":          _f("accounts_payable",          "accountPayables",          "BIGINT"),
        "short_term_debt":           _f("short_term_debt",           "shortTermDebt",            "BIGINT"),
        "total_current_liabilities": _f("total_current_liabilities", "totalCurrentLiabilities",  "BIGINT"),
        "long_term_debt":            _f("long_term_debt",            "longTermDebt",             "BIGINT"),
        "total_non_current_liabilities": _f("total_non_current_liabilities", "totalNonCurrentLiabilities", "BIGINT"),
        "total_liabilities":         _f("total_liabilities",         "totalLiabilities",         "BIGINT"),
        "total_stockholders_equity": _f("total_stockholders_equity", "totalStockholdersEquity",  "BIGINT"),
        "total_equity":              _f("total_equity",              "totalEquity",              "BIGINT"),
        "total_liabilities_and_equity": _f("total_liabilities_and_equity", "totalLiabilitiesAndTotalEquity", "BIGINT"),
        "total_debt":                _f("total_debt",                "totalDebt",                "BIGINT"),
        "net_debt":                  _f("net_debt",                  "netDebt",                  "BIGINT"),
        "retained_earnings":         _f("retained_earnings",         "retainedEarnings",         "BIGINT"),
        "common_stock":              _f("common_stock",              "commonStock",              "BIGINT"),
        "other_current_assets":      _f("other_current_assets",      "otherCurrentAssets",       "BIGINT"),
        "other_non_current_assets":  _f("other_non_current_assets",  "otherNonCurrentAssets",    "BIGINT"),
        "deferred_revenue":          _f("deferred_revenue",          "deferredRevenue",          "BIGINT"),
        "tax_payables":              _f("tax_payables",              "taxPayables",              "BIGINT"),
        "minority_interest":         _f("minority_interest",         "minorityInterest",         "BIGINT"),
        "goodwill_and_intangibles":  _f("goodwill_and_intangibles",  "goodwillAndIntangibleAssets", "BIGINT"),
        "other_assets":              _f("other_assets",              "otherAssets",              "BIGINT"),
        "other_liabilities":         _f("other_liabilities",         "otherLiabilities",         "BIGINT"),
        "total_investments":         _f("total_investments",         "totalInvestments",         "BIGINT"),
        "capital_lease_obligations": _f("capital_lease_obligations", "capitalLeaseObligations",  "BIGINT"),
    },
)

_CASH_FLOW = DatasetDef(
    name="cash_flow",
    endpoint="cash-flow-statement",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date", "period"),
    ttl_category="financial_statements",
    fields={
        "reported_currency":      _f("reported_currency",      "reportedCurrency",           "VARCHAR"),
        "cik":                    _f("cik",                    "cik",                        "VARCHAR"),
        "filling_date":           _f("filling_date",           "filingDate",                 "DATE"),
        "calendar_year":          _f("calendar_year",          "fiscalYear",                 "VARCHAR"),
        "net_income_cf":          _f("net_income_cf",          "netIncome",                  "BIGINT", agg="sum"),
        "depreciation":           _f("depreciation",           "depreciationAndAmortization","BIGINT", agg="sum"),
        "stock_based_compensation": _f("stock_based_compensation", "stockBasedCompensation", "BIGINT", agg="sum"),
        "operating_cash_flow":    _f("operating_cash_flow",    "operatingCashFlow",          "BIGINT", agg="sum"),
        "capex":                  _f("capex",                  "capitalExpenditure",         "BIGINT", agg="sum"),
        "acquisitions":           _f("acquisitions",           "acquisitionsNet",            "BIGINT", agg="sum"),
        "investing_cash_flow":    _f("investing_cash_flow",    "netCashProvidedByInvestingActivities", "BIGINT", agg="sum"),
        "debt_repayment":         _f("debt_repayment",         "netDebtIssuance",            "BIGINT", agg="sum"),
        "share_repurchase":       _f("share_repurchase",       "commonStockRepurchased",     "BIGINT", agg="sum"),
        "dividends_paid":         _f("dividends_paid",         "commonDividendsPaid",              "BIGINT", agg="sum"),
        "financing_cash_flow":    _f("financing_cash_flow",    "netCashProvidedByFinancingActivities", "BIGINT", agg="sum"),
        "free_cash_flow":         _f("free_cash_flow",         "freeCashFlow",               "BIGINT", agg="sum"),
        "net_change_in_cash":     _f("net_change_in_cash",     "netChangeInCash",            "BIGINT", agg="sum"),
    },
)

_KEY_METRICS = DatasetDef(
    name="key_metrics",
    endpoint="key-metrics",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date", "period"),
    ttl_category="key_metrics",
    fields={
        "calendar_year":       _f("calendar_year",       "fiscalYear",              "VARCHAR"),
        "market_cap":          _f("market_cap",          "marketCap",               "BIGINT", agg="last"),
        "enterprise_value":    _f("enterprise_value",    "enterpriseValue",         "BIGINT", agg="last"),
        "ev_to_sales":         _f("ev_to_sales",         "evToSales",               agg="last"),
        "ev_to_ebitda":        _f("ev_to_ebitda",        "evToEBITDA",              agg="last"),
        "ev_to_fcf":           _f("ev_to_fcf",           "evToFreeCashFlow",        agg="last"),
        "earnings_yield":      _f("earnings_yield",      "earningsYield",           agg="last"),
        "fcf_yield":           _f("fcf_yield",           "freeCashFlowYield",       agg="last"),
        "current_ratio":       _f("current_ratio",       "currentRatio",            agg="last"),
        "roic":                _f("roic",                "returnOnInvestedCapital",  agg="last"),
        "roe":                 _f("roe",                 "returnOnEquity",          agg="last"),
        "roa":                 _f("roa",                 "returnOnAssets",          agg="last"),
        "tax_burden_km":       _f("tax_burden_km",       "taxBurden",               agg="last"),
        "interest_burden_km":  _f("interest_burden_km",  "interestBurden",          agg="last"),
        "operating_return_on_assets_km": _f("operating_return_on_assets_km", "operatingReturnOnAssets", agg="last"),
        "return_on_capital_employed_km": _f("return_on_capital_employed_km", "returnOnCapitalEmployed", agg="last"),
        "return_on_tangible_assets_km":  _f("return_on_tangible_assets_km", "returnOnTangibleAssets",  agg="last"),
        "net_debt_to_ebitda_km": _f("net_debt_to_ebitda_km", "netDebtToEBITDA",     agg="last"),
        "invested_capital":    _f("invested_capital",    "investedCapital",         "BIGINT", agg="last"),
        "working_capital_km":  _f("working_capital_km",  "workingCapital",          "BIGINT", agg="last"),
        "graham_number_km":    _f("graham_number_km",    "grahamNumber",            agg="last"),
        "income_quality":      _f("income_quality",      "incomeQuality",           agg="last"),
    },
)

_RATIOS = DatasetDef(
    name="ratios",
    endpoint="ratios",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date", "period"),
    ttl_category="key_metrics",
    fields={
        "gross_profit_margin":  _f("gross_profit_margin",  "grossProfitMargin",        agg="last"),
        "operating_profit_margin": _f("operating_profit_margin", "operatingProfitMargin", agg="last"),
        "net_profit_margin":    _f("net_profit_margin",    "netProfitMargin",          agg="last"),
        "debt_ratio":           _f("debt_ratio",           "debtToAssetsRatio",        agg="last"),
        "debt_equity_ratio":    _f("debt_equity_ratio",    "debtToEquityRatio",        agg="last"),
        "interest_coverage":    _f("interest_coverage",    "interestCoverageRatio",    agg="last"),
        "cash_flow_to_debt":    _f("cash_flow_to_debt",    "cashFlowToDebtRatio",      agg="last"),
        "current_ratio_r":      _f("current_ratio_r",      "currentRatio",             agg="last"),
        "quick_ratio":          _f("quick_ratio",          "quickRatio",               agg="last"),
        "cash_ratio":           _f("cash_ratio",           "cashRatio",                agg="last"),
        "asset_turnover":       _f("asset_turnover",       "assetTurnover",            agg="last"),
        "inventory_turnover":   _f("inventory_turnover",   "inventoryTurnover",        agg="last"),
        "receivables_turnover": _f("receivables_turnover", "receivablesTurnover",      agg="last"),
        "dividend_yield_r":     _f("dividend_yield_r",     "dividendYield",            agg="last"),
        "price_earnings_ratio": _f("price_earnings_ratio", "priceToEarningsRatio",     agg="last"),
        "price_to_book":        _f("price_to_book",        "priceToBookRatio",         agg="last"),
        "price_to_sales_r":     _f("price_to_sales_r",     "priceToSalesRatio",        agg="last"),
        "price_to_fcf":         _f("price_to_fcf",         "priceToFreeCashFlowRatio", agg="last"),
        "ev_to_sales_r":        _f("ev_to_sales_r",        "enterpriseValueMultiple",  agg="last"),
        "revenue_per_share_r":  _f("revenue_per_share_r",  "revenuePerShare",          agg="last"),
        "net_income_per_share_r": _f("net_income_per_share_r", "netIncomePerShare",    agg="last"),
        "book_value_per_share_r": _f("book_value_per_share_r", "bookValuePerShare",    agg="last"),
        "fcf_per_share_r":      _f("fcf_per_share_r",      "freeCashFlowPerShare",     agg="last"),
        "operating_cf_per_share_r": _f("operating_cf_per_share_r", "operatingCashFlowPerShare", agg="last"),
        "cash_per_share_r":     _f("cash_per_share_r",     "cashPerShare",             agg="last"),
        "tangible_bvps_r":      _f("tangible_bvps_r",      "tangibleBookValuePerShare", agg="last"),
        "dividend_per_share_r": _f("dividend_per_share_r", "dividendPerShare",         agg="last"),
        "ebitda_margin_r":      _f("ebitda_margin_r",      "ebitdaMargin",             agg="last"),
        "effective_tax_rate_r": _f("effective_tax_rate_r",  "effectiveTaxRate",         agg="last"),
    },
)

_QUOTE = DatasetDef(
    name="quote",
    endpoint="quote",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="realtime_quotes",
    fields={
        "quote_name":           _f("quote_name",           "name",               "VARCHAR"),
        "price":                _f("price",                "price"),
        "quote_change":         _f("quote_change",         "change"),
        "quote_change_pct":     _f("quote_change_pct",     "changePercentage"),
        "day_low":              _f("day_low",              "dayLow"),
        "day_high":             _f("day_high",             "dayHigh"),
        "year_low":             _f("year_low",             "yearLow"),
        "year_high":            _f("year_high",            "yearHigh"),
        "quote_market_cap":     _f("quote_market_cap",     "marketCap",          "BIGINT"),
        "price_avg_50":         _f("price_avg_50",         "priceAvg50"),
        "price_avg_200":        _f("price_avg_200",        "priceAvg200"),
        "quote_volume":         _f("quote_volume",         "volume",             "BIGINT"),
        "quote_open":           _f("quote_open",           "open"),
        "previous_close":       _f("previous_close",       "previousClose"),
        "exchange":             _f("exchange",             "exchange",           "VARCHAR"),
    },
)

_PROFILE = DatasetDef(
    name="profile",
    endpoint="profile",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="company_profiles",
    fields={
        "company_name":         _f("company_name",         "companyName",        "VARCHAR"),
        "currency":             _f("currency",             "currency",           "VARCHAR"),
        "cik":                  _f("cik",                  "cik",                "VARCHAR"),
        "isin":                 _f("isin",                 "isin",               "VARCHAR"),
        "exchange_short":       _f("exchange_short",       "exchange",           "VARCHAR"),
        "industry":             _f("industry",             "industry",           "VARCHAR"),
        "sector":               _f("sector",               "sector",             "VARCHAR"),
        "country":              _f("country",              "country",            "VARCHAR"),
        "employees":            _f("employees",            "fullTimeEmployees",  "VARCHAR"),
        "description":          _f("description",          "description",        "VARCHAR"),
        "ceo":                  _f("ceo",                  "ceo",                "VARCHAR"),
        "website":              _f("website",              "website",            "VARCHAR"),
        "ipo_date":             _f("ipo_date",             "ipoDate",            "DATE"),
        "beta":                 _f("beta",                 "beta"),
        "is_etf":               _f("is_etf",               "isEtf",              "BOOLEAN"),
        "is_actively_trading":  _f("is_actively_trading",  "isActivelyTrading",  "BOOLEAN"),
    },
)

_EARNINGS = DatasetDef(
    name="earnings_data",
    endpoint="earnings",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date"),
    ttl_category="earnings_calendar",
    fields={
        "earnings_eps":           _f("earnings_eps",           "epsActual"),
        "eps_estimated":          _f("eps_estimated",          "epsEstimated"),
        "earnings_revenue":       _f("earnings_revenue",       "revenueActual",     "BIGINT", agg="sum"),
        "revenue_estimated":      _f("revenue_estimated",      "revenueEstimated",  "BIGINT", agg="sum"),
        "earnings_last_updated":  _f("earnings_last_updated",  "lastUpdated",       "DATE"),
    },
)

_DIVIDENDS = DatasetDef(
    name="dividends_data",
    endpoint="dividends",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date"),
    ttl_category="earnings_calendar",
    fields={
        "dividend":         _f("dividend",         "dividend"),
        "adj_dividend":     _f("adj_dividend",     "adjDividend"),
        "record_date":      _f("record_date",      "recordDate",      "DATE"),
        "payment_date":     _f("payment_date",     "paymentDate",     "DATE"),
        "declaration_date": _f("declaration_date", "declarationDate", "DATE"),
    },
)

_ENTERPRISE_VALUES = DatasetDef(
    name="enterprise_values",
    endpoint="enterprise-values",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date"),
    ttl_category="financial_statements",
    fields={
        "stock_price_ev":         _f("stock_price_ev",         "stockPrice"),
        "shares_outstanding_ev":  _f("shares_outstanding_ev",  "numberOfShares",     "BIGINT"),
        "ev_market_cap":          _f("ev_market_cap",          "marketCapitalization","BIGINT"),
        "minus_cash":             _f("minus_cash",             "minusCashAndCashEquivalents", "BIGINT"),
        "plus_debt":              _f("plus_debt",              "addTotalDebt",       "BIGINT"),
        "enterprise_value":      _f("enterprise_value",       "enterpriseValue",    "BIGINT"),
    },
)

_TREASURY_RATES = DatasetDef(
    name="treasury_rates",
    endpoint="treasury-rates",
    grain=Grain.DAILY,
    keys=("date",),  # No symbol — market-wide data, joins on date only
    ttl_category="economic_indicators",
    fields={
        "rate_1m":  _f("rate_1m",  "month1"),
        "rate_2m":  _f("rate_2m",  "month2"),
        "rate_3m":  _f("rate_3m",  "month3"),
        "rate_6m":  _f("rate_6m",  "month6"),
        "rate_1y":  _f("rate_1y",  "year1"),
        "rate_2y":  _f("rate_2y",  "year2"),
        "rate_3y":  _f("rate_3y",  "year3"),
        "rate_5y":  _f("rate_5y",  "year5"),
        "rate_7y":  _f("rate_7y",  "year7"),
        "rate_10y": _f("rate_10y", "year10"),
        "rate_20y": _f("rate_20y", "year20"),
        "rate_30y": _f("rate_30y", "year30"),
    },
)

_ANALYST_ESTIMATES = DatasetDef(
    name="analyst_estimates",
    endpoint="analyst-estimates",  # requires period param (annual/quarter)
    grain=Grain.QUARTERLY,
    keys=("symbol", "date"),
    ttl_category="analyst",
    fields={
        "est_revenue_low":     _f("est_revenue_low",     "revenueLow",          "BIGINT"),
        "est_revenue_high":    _f("est_revenue_high",    "revenueHigh",         "BIGINT"),
        "est_revenue_avg":     _f("est_revenue_avg",     "revenueAvg",          "BIGINT"),
        "est_ebitda_low":      _f("est_ebitda_low",      "ebitdaLow",           "BIGINT"),
        "est_ebitda_high":     _f("est_ebitda_high",     "ebitdaHigh",          "BIGINT"),
        "est_ebitda_avg":      _f("est_ebitda_avg",      "ebitdaAvg",           "BIGINT"),
        "est_eps_low":         _f("est_eps_low",         "epsLow"),
        "est_eps_high":        _f("est_eps_high",        "epsHigh"),
        "est_eps_avg":         _f("est_eps_avg",         "epsAvg"),
        "est_net_income_low":  _f("est_net_income_low",  "netIncomeLow",        "BIGINT"),
        "est_net_income_high": _f("est_net_income_high", "netIncomeHigh",       "BIGINT"),
        "est_net_income_avg":  _f("est_net_income_avg",  "netIncomeAvg",        "BIGINT"),
        "est_sga_avg":         _f("est_sga_avg",         "sgaExpenseAvg",       "BIGINT"),
        "num_analysts_revenue": _f("num_analysts_revenue","numAnalystsRevenue", "INTEGER"),
        "num_analysts_eps":    _f("num_analysts_eps",    "numAnalystsEps",      "INTEGER"),
    },
)

_PRICE_TARGET = DatasetDef(
    name="price_target",
    endpoint="price-target-consensus",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="analyst",
    fields={
        "target_high":      _f("target_high",      "targetHigh"),
        "target_low":       _f("target_low",       "targetLow"),
        "target_consensus": _f("target_consensus", "targetConsensus"),
        "target_median":    _f("target_median",    "targetMedian"),
    },
)

_GRADES_CONSENSUS = DatasetDef(
    name="grades_consensus",
    endpoint="grades-consensus",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="analyst",
    fields={
        "strong_buy":  _f("strong_buy",  "strongBuy",  "INTEGER"),
        "buy":         _f("buy",         "buy",        "INTEGER"),
        "hold":        _f("hold",        "hold",       "INTEGER"),
        "sell":        _f("sell",        "sell",        "INTEGER"),
        "strong_sell": _f("strong_sell", "strongSell", "INTEGER"),
        "consensus":   _f("consensus",  "consensus",  "VARCHAR"),
    },
)

_RATINGS = DatasetDef(
    name="ratings",
    endpoint="ratings-snapshot",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="analyst",
    fields={
        "fmp_rating":        _f("fmp_rating",        "rating",                    "VARCHAR"),
        "fmp_rating_score":  _f("fmp_rating_score",  "overallScore",              "INTEGER"),
        "fmp_dcf_score":     _f("fmp_dcf_score",     "discountedCashFlowScore",   "INTEGER"),
        "fmp_roe_score":     _f("fmp_roe_score",     "returnOnEquityScore",       "INTEGER"),
        "fmp_roa_score":     _f("fmp_roa_score",     "returnOnAssetsScore",       "INTEGER"),
        "fmp_de_score":      _f("fmp_de_score",      "debtToEquityScore",         "INTEGER"),
        "fmp_pe_score":      _f("fmp_pe_score",      "priceToEarningsScore",      "INTEGER"),
        "fmp_pb_score":      _f("fmp_pb_score",      "priceToBookScore",          "INTEGER"),
    },
)

_EMPLOYEE_COUNT = DatasetDef(
    name="employee_count",
    endpoint="historical-employee-count",
    grain=Grain.ANNUAL,
    keys=("symbol", "date"),
    ttl_category="company_profiles",
    fields={
        "employee_count_val": _f("employee_count_val", "employeeCount", "INTEGER"),
        "company_name_emp":   _f("company_name_emp",   "companyName",   "VARCHAR"),
    },
)

_SHARES_FLOAT = DatasetDef(
    name="shares_float_data",
    endpoint="shares-float",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="company_profiles",
    fields={
        "free_float":           _f("free_float",           "freeFloat"),
        "float_shares":         _f("float_shares",         "floatShares",         "BIGINT"),
        "outstanding_shares":   _f("outstanding_shares",   "outstandingShares",   "BIGINT"),
    },
)

_DCF_DATA = DatasetDef(
    name="dcf_data",
    endpoint="discounted-cash-flow",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="dcf",
    fields={
        "dcf_val":        _f("dcf_val",        "dcf"),
        "dcf_stock_price": _f("dcf_stock_price", "Stock Price"),
    },
)

_ESG_DATA = DatasetDef(
    name="esg_data",
    endpoint="esg-environmental-social-governance-data",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="esg",
    fields={
        "esg_total":         _f("esg_total",         "environmentalScore"),  # composite
        "esg_environmental": _f("esg_environmental", "environmentalScore"),
        "esg_social":        _f("esg_social",        "socialScore"),
        "esg_governance":    _f("esg_governance",    "governanceScore"),
        "esg_score":         _f("esg_score",         "ESGScore"),
    },
)

_PRICE_CHANGE = DatasetDef(
    name="price_change",
    endpoint="stock-price-change",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="realtime_quotes",
    fields={
        "fmp_return_1d":  _f("fmp_return_1d",  "1D"),
        "fmp_return_5d":  _f("fmp_return_5d",  "5D"),
        "fmp_return_1m":  _f("fmp_return_1m",  "1M"),
        "fmp_return_3m":  _f("fmp_return_3m",  "3M"),
        "fmp_return_6m":  _f("fmp_return_6m",  "6M"),
        "fmp_return_ytd": _f("fmp_return_ytd", "ytd"),
        "fmp_return_1y":  _f("fmp_return_1y",  "1Y"),
        "fmp_return_3y":  _f("fmp_return_3y",  "3Y"),
        "fmp_return_5y":  _f("fmp_return_5y",  "5Y"),
    },
)

_SPLITS_DATA = DatasetDef(
    name="splits_data",
    endpoint="splits",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date"),
    ttl_category="earnings_calendar",
    fields={
        "split_label":       _f("split_label",       "label",       "VARCHAR"),
        "split_numerator":   _f("split_numerator",   "numerator",   "INTEGER"),
        "split_denominator": _f("split_denominator", "denominator", "INTEGER"),
    },
)

_INSTITUTIONAL_SUMMARY = DatasetDef(
    name="institutional_summary",
    endpoint="institutional-ownership/symbol-positions-summary",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="sec_filings",
    fields={
        "inst_holders_count":    _f("inst_holders_count",    "investorsHolding",        "INTEGER"),
        "inst_holders_prev":     _f("inst_holders_prev",     "lastInvestorsHolding",    "INTEGER"),
        "inst_holders_change":   _f("inst_holders_change",   "investorsHoldingChange",  "INTEGER"),
        "inst_total_invested":   _f("inst_total_invested",   "totalInvested",           "BIGINT"),
        "inst_invested_prev":    _f("inst_invested_prev",    "lastTotalInvested",       "BIGINT"),
        "inst_invested_change":  _f("inst_invested_change",  "totalInvestedChange",     "BIGINT"),
        "inst_put_call_ratio":   _f("inst_put_call_ratio",   "putCallRatio"),
    },
)

_FINANCIAL_SCORES = DatasetDef(
    name="financial_scores",
    endpoint="financial-scores",
    grain=Grain.SNAPSHOT,
    keys=("symbol",),
    ttl_category="key_metrics",
    fields={
        "altman_z_score_fmp":    _f("altman_z_score_fmp",    "altmanZScore"),
        "piotroski_score_fmp":   _f("piotroski_score_fmp",   "piotroskiScore"),
        "working_capital_score": _f("working_capital_score",  "workingCapital"),
        "retained_earnings_score": _f("retained_earnings_score", "retainedEarnings"),
        "operating_cash_flow_score": _f("operating_cash_flow_score", "operatingCashFlow"),
        "total_assets_score":    _f("total_assets_score",     "totalAssets"),
    },
)

# ──────────────────────────────────────────────────────────────────────
# Historical datasets (point-in-time correct for backtesting)
# ──────────────────────────────────────────────────────────────────────

_HISTORICAL_MARKET_CAP = DatasetDef(
    name="historical_market_cap",
    endpoint="historical-market-capitalization",
    grain=Grain.DAILY,
    keys=("symbol", "date"),
    ttl_category="daily_historical",
    fields={
        "hist_market_cap": _f("hist_market_cap", "marketCap", "BIGINT"),
    },
)

_HISTORICAL_GRADES = DatasetDef(
    name="historical_grades",
    endpoint="grades-historical",
    grain=Grain.MONTHLY,
    keys=("symbol", "date"),
    ttl_category="analyst",
    fields={
        "hist_strong_buy":  _f("hist_strong_buy",  "analystRatingsStrongBuy",  "INTEGER"),
        "hist_buy":         _f("hist_buy",         "analystRatingsBuy",        "INTEGER"),
        "hist_hold":        _f("hist_hold",        "analystRatingsHold",       "INTEGER"),
        "hist_sell":        _f("hist_sell",         "analystRatingsSell",       "INTEGER"),
        "hist_strong_sell": _f("hist_strong_sell",  "analystRatingsStrongSell", "INTEGER"),
    },
)

_HISTORICAL_RATINGS = DatasetDef(
    name="historical_ratings",
    endpoint="ratings-historical",
    grain=Grain.MONTHLY,
    keys=("symbol", "date"),
    ttl_category="analyst",
    fields={
        "hist_rating":         _f("hist_rating",         "rating",                    "VARCHAR"),
        "hist_overall_score":  _f("hist_overall_score",  "overallScore",              "INTEGER"),
        "hist_dcf_score":      _f("hist_dcf_score",      "discountedCashFlowScore",   "INTEGER"),
        "hist_roe_score":      _f("hist_roe_score",      "returnOnEquityScore",       "INTEGER"),
        "hist_roa_score":      _f("hist_roa_score",      "returnOnAssetsScore",       "INTEGER"),
        "hist_de_score":       _f("hist_de_score",       "debtToEquityScore",         "INTEGER"),
        "hist_pe_score":       _f("hist_pe_score",       "priceToEarningsScore",      "INTEGER"),
        "hist_pb_score":       _f("hist_pb_score",       "priceToBookScore",          "INTEGER"),
    },
)

_HISTORICAL_INSTITUTIONAL = DatasetDef(
    name="historical_institutional",
    endpoint="institutional-ownership/symbol-positions-summary",
    grain=Grain.QUARTERLY,
    keys=("symbol", "date"),
    ttl_category="sec_filings",
    fields={
        "hist_inst_holders":          _f("hist_inst_holders",          "investorsHolding",        "INTEGER"),
        "hist_inst_holders_change":   _f("hist_inst_holders_change",  "investorsHoldingChange",  "INTEGER"),
        "hist_inst_invested":         _f("hist_inst_invested",        "totalInvested",           "BIGINT"),
        "hist_inst_invested_change":  _f("hist_inst_invested_change", "totalInvestedChange",     "BIGINT"),
        "hist_inst_ownership_pct":    _f("hist_inst_ownership_pct",   "ownershipPercent"),
        "hist_inst_new_positions":    _f("hist_inst_new_positions",   "newPositions",            "INTEGER"),
        "hist_inst_closed_positions": _f("hist_inst_closed_positions","closedPositions",         "INTEGER"),
        "hist_inst_put_call_ratio":   _f("hist_inst_put_call_ratio",  "putCallRatio"),
    },
)


# ──────────────────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────────────────

DATASETS: dict[str, DatasetDef] = {
    ds.name: ds
    for ds in [
        _DAILY_PRICE,
        _INCOME_STATEMENT,
        _BALANCE_SHEET,
        _CASH_FLOW,
        _KEY_METRICS,
        _RATIOS,
        _QUOTE,
        _PROFILE,
        _EARNINGS,
        _DIVIDENDS,
        _ENTERPRISE_VALUES,
        _DCF_DATA,
        _ESG_DATA,
        _PRICE_CHANGE,
        _SPLITS_DATA,
        _INSTITUTIONAL_SUMMARY,
        _FINANCIAL_SCORES,
        _TREASURY_RATES,
        _ANALYST_ESTIMATES,
        _PRICE_TARGET,
        _GRADES_CONSENSUS,
        _RATINGS,
        _EMPLOYEE_COUNT,
        _SHARES_FLOAT,
        _HISTORICAL_MARKET_CAP,
        _HISTORICAL_GRADES,
        _HISTORICAL_RATINGS,
        _HISTORICAL_INSTITUTIONAL,
    ]
}

# Build a global field name → (dataset_name, FieldDef) index.
# First dataset to register a name wins (order above controls priority).
FIELD_REGISTRY: dict[str, tuple[str, FieldDef]] = {}
for _ds in DATASETS.values():
    for _field in _ds.fields.values():
        if _field.name not in FIELD_REGISTRY:
            FIELD_REGISTRY[_field.name] = (_ds.name, _field)

# ── Aliases: convenient short names that map to fields in their correct dataset ──
# These let users write .select("pe_ratio") instead of .select("price_earnings_ratio")
_ALIASES: dict[str, str] = {
    # key_metrics fields that moved to ratios
    "pe_ratio":          "price_earnings_ratio",
    "pb_ratio":          "price_to_book",
    "price_to_sales":    "price_to_sales_r",
    "debt_to_equity":    "debt_equity_ratio",
    "debt_to_assets":    "debt_ratio",
    "dividend_yield":    "dividend_yield_r",
    "payout_ratio":      "dividend_per_share_r",  # closest available
    "revenue_per_share": "revenue_per_share_r",
    "net_income_per_share": "net_income_per_share_r",
    "book_value_per_share": "book_value_per_share_r",
    "fcf_per_share":     "fcf_per_share_r",
    "cash_per_share":    "cash_per_share_r",
    "operating_cf_per_share": "operating_cf_per_share_r",
    # quote fields that moved elsewhere
    "shares_outstanding": "outstanding_shares",   # shares_float_data
    "avg_volume":        "quote_volume",           # quote (closest)
    "quote_pe":          "price_earnings_ratio",   # ratios
    "quote_eps":         "eps",                    # income_statement
    # income statement ratios (now in ratios endpoint or computable)
    "gross_profit_ratio":     "gross_profit_margin",  # ratios endpoint
    "operating_income_ratio": "operating_profit_margin",  # ratios
    "ebitda_ratio":           "ebitda_margin_r",
    "net_income_ratio":       "net_profit_margin",  # ratios
}

# Register aliases — point them to the same (dataset, FieldDef) as the target
for _alias, _target in _ALIASES.items():
    if _alias not in FIELD_REGISTRY and _target in FIELD_REGISTRY:
        FIELD_REGISTRY[_alias] = FIELD_REGISTRY[_target]


def resolve_fields(
    names: list[str],
) -> dict[str, list[FieldDef]]:
    """Resolve field names to datasets.

    Returns a dict keyed by dataset name, each value being the list of
    :class:`FieldDef` objects requested from that dataset.

    Raises :class:`ValueError` for unknown field names (checks both base
    and derived registries).
    """
    from fmp._features import DERIVED_REGISTRY
    from fmp._features._post_compute import POST_COMPUTE_REGISTRY

    unknown = [
        n for n in names
        if n not in FIELD_REGISTRY and n not in DERIVED_REGISTRY and n not in POST_COMPUTE_REGISTRY
    ]
    if unknown:
        raise ValueError(f"Unknown fields: {unknown}")

    # Only resolve base fields here; derived fields are handled by the
    # query builder which calls resolve_derived_dependencies separately.
    grouped: dict[str, list[FieldDef]] = {}
    for name in names:
        if name in FIELD_REGISTRY:
            ds_name, field_def = FIELD_REGISTRY[name]
            grouped.setdefault(ds_name, []).append(field_def)
    return grouped


def list_fields(dataset: str | None = None) -> list[str]:
    """List available field names (base + derived + post-compute)."""
    from fmp._features import DERIVED_REGISTRY
    from fmp._features._post_compute import POST_COMPUTE_REGISTRY

    if dataset:
        ds = DATASETS.get(dataset)
        if not ds:
            raise ValueError(f"Unknown dataset: {dataset}")
        return list(ds.fields.keys())
    return sorted(set(
        list(FIELD_REGISTRY.keys())
        + list(DERIVED_REGISTRY.keys())
        + list(POST_COMPUTE_REGISTRY.keys())
    ))
