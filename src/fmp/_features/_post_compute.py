"""Post-compute features: computed in polars after the SQL query returns.

These handle cases that can't be expressed as single-pass DuckDB SQL:
recursive calculations (EMA), nested window functions (return autocorrelation),
cumulative conditional logic (dividend streaks), and cross-asset joins (beta).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass(frozen=True)
class PostComputeFieldDef:
    """A feature computed in polars after the SQL query returns.

    Attributes:
        name: Unique identifier (e.g., ``"ema_20"``).
        compute_fn: Function ``(df: polars.DataFrame, ctx: dict) -> polars.Series``.
        dependencies: Base/derived fields that must be in the DataFrame.
        category: Grouping label.
        reference_symbols: Additional symbols to fetch (e.g., ``["^GSPC"]`` for beta).
    """

    name: str
    compute_fn: Callable
    dependencies: tuple[str, ...]
    category: str = ""
    reference_symbols: tuple[str, ...] = ()


# ──────────────────────────────────────────────────────────────────────
# EMA features
# ──────────────────────────────────────────────────────────────────────

def _ema(span: int):
    """Factory for EMA compute functions."""
    def compute(df, ctx):
        import polars as pl
        return (
            df.sort("symbol", "date")
            .group_by("symbol", maintain_order=True)
            .agg(pl.col("close").ewm_mean(span=span, min_samples=1).alias("_ema"))
            .explode("_ema")["_ema"]
        )
    return compute


def _macd_line(df, ctx):
    import polars as pl
    sorted_df = df.sort("symbol", "date")
    ema12 = (
        sorted_df.group_by("symbol", maintain_order=True)
        .agg(pl.col("close").ewm_mean(span=12, min_samples=1))
        .explode("close")["close"]
    )
    ema26 = (
        sorted_df.group_by("symbol", maintain_order=True)
        .agg(pl.col("close").ewm_mean(span=26, min_samples=1))
        .explode("close")["close"]
    )
    return ema12 - ema26


def _macd_signal(df, ctx):
    import polars as pl
    sorted_df = df.sort("symbol", "date")
    ema12 = (
        sorted_df.group_by("symbol", maintain_order=True)
        .agg(pl.col("close").ewm_mean(span=12, min_samples=1))
        .explode("close")["close"]
    )
    ema26 = (
        sorted_df.group_by("symbol", maintain_order=True)
        .agg(pl.col("close").ewm_mean(span=26, min_samples=1))
        .explode("close")["close"]
    )
    macd_line = ema12 - ema26
    # Signal is EMA(9) of the MACD line, computed per symbol
    temp = sorted_df.select("symbol").with_columns(macd_line.alias("_macd"))
    signal = (
        temp.group_by("symbol", maintain_order=True)
        .agg(pl.col("_macd").ewm_mean(span=9, min_samples=1))
        .explode("_macd")["_macd"]
    )
    return signal


def _macd_histogram(df, ctx):
    import polars as pl
    sorted_df = df.sort("symbol", "date")
    ema12 = (
        sorted_df.group_by("symbol", maintain_order=True)
        .agg(pl.col("close").ewm_mean(span=12, min_samples=1))
        .explode("close")["close"]
    )
    ema26 = (
        sorted_df.group_by("symbol", maintain_order=True)
        .agg(pl.col("close").ewm_mean(span=26, min_samples=1))
        .explode("close")["close"]
    )
    macd_line = ema12 - ema26
    temp = sorted_df.select("symbol").with_columns(macd_line.alias("_macd"))
    signal = (
        temp.group_by("symbol", maintain_order=True)
        .agg(pl.col("_macd").ewm_mean(span=9, min_samples=1))
        .explode("_macd")["_macd"]
    )
    return macd_line - signal


# ──────────────────────────────────────────────────────────────────────
# Return autocorrelation
# ──────────────────────────────────────────────────────────────────────

def _return_autocorrelation(df, ctx):
    """Lag-1 autocorrelation of daily returns over a 21-day rolling window."""
    import polars as pl
    sorted_df = df.sort("symbol", "date")

    def _autocorr_per_group(group_df):
        returns = group_df["close"].pct_change()
        lagged = returns.shift(1)
        # Rolling correlation between return and lagged return
        corr = returns.rolling_corr(lagged, window_size=21, min_samples=10)
        return corr

    result = (
        sorted_df.group_by("symbol", maintain_order=True)
        .agg(pl.col("close"))
        .with_columns(
            pl.col("close").map_elements(
                lambda closes: closes.pct_change().rolling_corr(
                    closes.pct_change().shift(1), window_size=21, min_samples=10
                ),
                return_dtype=pl.List(pl.Float64),
            ).alias("_autocorr")
        )
        .explode("_autocorr")["_autocorr"]
    )
    return result


# ──────────────────────────────────────────────────────────────────────
# Consecutive dividend streak
# ──────────────────────────────────────────────────────────────────────

def _consecutive_dividend_increases(df, ctx):
    """Count of consecutive periods where dividend increased."""
    import polars as pl
    sorted_df = df.sort("symbol", "date")

    def _streak_per_group(group_df):
        divs = group_df["adj_dividend"]
        increased = divs > divs.shift(1)
        # Count consecutive True values ending at current row
        streak = pl.Series([0] * len(divs))
        vals = increased.to_list()
        counts = []
        count = 0
        for v in vals:
            if v is True:
                count += 1
            else:
                count = 0
            counts.append(count)
        return pl.Series(counts, dtype=pl.Int64)

    result = (
        sorted_df.group_by("symbol", maintain_order=True)
        .agg(pl.col("adj_dividend"))
        .with_columns(
            pl.col("adj_dividend").map_elements(
                lambda divs: _streak_helper(divs),
                return_dtype=pl.List(pl.Int64),
            ).alias("_streak")
        )
        .explode("_streak")["_streak"]
    )
    return result


def _streak_helper(divs):
    """Compute consecutive increase streak from a series of dividend values."""
    import polars as pl
    vals = divs.to_list()
    counts = []
    count = 0
    for i, v in enumerate(vals):
        if i == 0 or v is None or vals[i - 1] is None:
            count = 0
        elif v > vals[i - 1]:
            count += 1
        else:
            count = 0
        counts.append(count)
    return pl.Series(counts, dtype=pl.Int64)


# ──────────────────────────────────────────────────────────────────────
# Cross-asset beta
# ──────────────────────────────────────────────────────────────────────

def _beta_sp500(df, ctx):
    """Rolling 252-day beta vs S&P 500 (^GSPC).

    The query builder fetches ^GSPC automatically via reference_symbols.
    ctx["reference_data"]["^GSPC"] contains the market DataFrame.
    """
    import polars as pl

    market_df = ctx.get("reference_data", {}).get("^GSPC")
    if market_df is None or market_df.is_empty():
        return pl.Series([None] * len(df), dtype=pl.Float64)

    sorted_df = df.sort("symbol", "date")

    # Market returns
    market = (
        market_df.sort("date")
        .with_columns(
            (pl.col("close") / pl.col("close").shift(1) - 1).alias("market_return")
        )
        .select("date", "market_return")
    )

    # Per symbol: join with market, compute rolling covariance / variance
    results = []
    for symbol in sorted_df["symbol"].unique().sort().to_list():
        stock = sorted_df.filter(pl.col("symbol") == symbol).sort("date")
        stock = stock.with_columns(
            (pl.col("close") / pl.col("close").shift(1) - 1).alias("stock_return")
        )
        joined = stock.join(market, on="date", how="left")

        beta_vals = joined.select(
            pl.col("stock_return").rolling_corr(
                pl.col("market_return"), window_size=252, min_samples=60
            )
            * pl.col("stock_return").rolling_std(window_size=252, min_samples=60)
            / pl.col("market_return").rolling_std(window_size=252, min_samples=60)
        ).to_series()

        results.append(beta_vals)

    return pl.concat(results)


def _alpha_jensen(df, ctx):
    """Jensen's alpha: actual return - expected return (CAPM), annualised.

    Simplified: uses 252-day return - beta * market_252d_return.
    """
    import polars as pl

    market_df = ctx.get("reference_data", {}).get("^GSPC")
    if market_df is None or market_df.is_empty():
        return pl.Series([None] * len(df), dtype=pl.Float64)

    sorted_df = df.sort("symbol", "date")
    market = (
        market_df.sort("date")
        .with_columns([
            (pl.col("close") / pl.col("close").shift(1) - 1).alias("market_return"),
            (pl.col("close") / pl.col("close").shift(252) - 1).alias("market_return_252d"),
        ])
        .select("date", "market_return", "market_return_252d")
    )

    results = []
    for symbol in sorted_df["symbol"].unique().sort().to_list():
        stock = sorted_df.filter(pl.col("symbol") == symbol).sort("date")
        stock = stock.with_columns([
            (pl.col("close") / pl.col("close").shift(1) - 1).alias("stock_return"),
            (pl.col("close") / pl.col("close").shift(252) - 1).alias("stock_return_252d"),
        ])
        joined = stock.join(market, on="date", how="left")

        beta = (
            joined["stock_return"].rolling_corr(
                joined["market_return"], window_size=252, min_samples=60
            )
            * joined["stock_return"].rolling_std(window_size=252, min_samples=60)
            / joined["market_return"].rolling_std(window_size=252, min_samples=60)
        )

        alpha = joined["stock_return_252d"] - beta * joined["market_return_252d"]
        results.append(alpha)

    return pl.concat(results)


# ──────────────────────────────────────────────────────────────────────
# Index membership
# ──────────────────────────────────────────────────────────────────────

def _in_index(index_endpoint):
    """Factory for index membership check."""
    def compute(df, ctx):
        import polars as pl
        http = ctx.get("http")
        if not http:
            return pl.Series([None] * len(df), dtype=pl.Int32)
        try:
            constituents = http.get(index_endpoint)
            member_symbols = {c.get("symbol", "") for c in constituents}
            return df["symbol"].is_in(member_symbols).cast(pl.Int32)
        except Exception:
            return pl.Series([None] * len(df), dtype=pl.Int32)
    return compute


# ──────────────────────────────────────────────────────────────────────
# Insider trade aggregations
# ──────────────────────────────────────────────────────────────────────

def _fetch_insider_trades(http, symbols):
    """Fetch insider trades for symbols."""
    import polars as pl

    all_trades = []
    for sym in symbols:
        try:
            trades = http.get("insider-trading/search", params={"symbol": sym, "limit": 100})
            for t in trades:
                t.setdefault("symbol", sym)
            all_trades.extend(trades)
        except Exception:
            pass
    if not all_trades:
        return pl.DataFrame()
    return pl.DataFrame(all_trades, strict=False)


def _get_insider_trades(ctx, http, symbols):
    """Fetch once, cache in ctx."""
    if "_insider_trades" not in ctx:
        ctx["_insider_trades"] = _fetch_insider_trades(http, symbols)
    return ctx["_insider_trades"]


def _insider_net_buying_90d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Float64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_insider_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0.0] * len(df), dtype=pl.Float64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    trades_df = trades_df.filter(pl.col("transactionDate") >= cutoff)

    buys = trades_df.filter(pl.col("acquistionOrDisposition") == "A")
    sells = trades_df.filter(pl.col("acquistionOrDisposition") == "D")

    buy_val = buys.group_by("symbol").agg(
        (pl.col("securitiesTransacted").cast(pl.Float64) * pl.col("price").cast(pl.Float64)).sum().alias("buy_value")
    )
    sell_val = sells.group_by("symbol").agg(
        (pl.col("securitiesTransacted").cast(pl.Float64) * pl.col("price").cast(pl.Float64)).sum().alias("sell_value")
    )

    result = df.select("symbol").join(buy_val, on="symbol", how="left").join(sell_val, on="symbol", how="left")
    return result["buy_value"].fill_null(0) - result["sell_value"].fill_null(0)


def _insider_buy_count_30d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_insider_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int64)

    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    buys = trades_df.filter(
        (pl.col("transactionDate") >= cutoff) & (pl.col("acquistionOrDisposition") == "A")
    )
    counts = buys.group_by("symbol").agg(pl.len().alias("buy_count"))
    result = df.select("symbol").join(counts, on="symbol", how="left")
    return result["buy_count"].fill_null(0)


def _insider_sell_count_30d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_insider_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int64)

    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    sells = trades_df.filter(
        (pl.col("transactionDate") >= cutoff) & (pl.col("acquistionOrDisposition") == "D")
    )
    counts = sells.group_by("symbol").agg(pl.len().alias("sell_count"))
    result = df.select("symbol").join(counts, on="symbol", how="left")
    return result["sell_count"].fill_null(0)


def _insider_buy_sell_ratio_90d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Float64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_insider_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([None] * len(df), dtype=pl.Float64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    recent = trades_df.filter(pl.col("transactionDate") >= cutoff)

    buy_counts = recent.filter(pl.col("acquistionOrDisposition") == "A").group_by("symbol").agg(
        pl.len().alias("buy_count")
    )
    sell_counts = recent.filter(pl.col("acquistionOrDisposition") == "D").group_by("symbol").agg(
        pl.len().alias("sell_count")
    )
    result = (
        df.select("symbol")
        .join(buy_counts, on="symbol", how="left")
        .join(sell_counts, on="symbol", how="left")
    )
    buy_c = result["buy_count"].fill_null(0).cast(pl.Float64)
    sell_c = result["sell_count"].fill_null(0).cast(pl.Float64)
    return pl.when(sell_c > 0).then(buy_c / sell_c).otherwise(None)


def _insider_buying_cluster(df, ctx):
    """3+ unique insiders buying in 30 days."""
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int32)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_insider_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int32)

    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    buys = trades_df.filter(
        (pl.col("transactionDate") >= cutoff) & (pl.col("acquistionOrDisposition") == "A")
    )
    if buys.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int32)

    # Count unique insiders per symbol
    unique_buyers = buys.group_by("symbol").agg(
        pl.col("reportingName").n_unique().alias("unique_buyers")
    )
    result = df.select("symbol").join(unique_buyers, on="symbol", how="left")
    return (result["unique_buyers"].fill_null(0) >= 3).cast(pl.Int32)


def _insider_total_bought_90d(df, ctx):
    """Total $ value of insider buys in 90 days."""
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Float64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_insider_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0.0] * len(df), dtype=pl.Float64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    buys = trades_df.filter(
        (pl.col("transactionDate") >= cutoff) & (pl.col("acquistionOrDisposition") == "A")
    )
    buy_val = buys.group_by("symbol").agg(
        (pl.col("securitiesTransacted").cast(pl.Float64) * pl.col("price").cast(pl.Float64)).sum().alias("total_bought")
    )
    result = df.select("symbol").join(buy_val, on="symbol", how="left")
    return result["total_bought"].fill_null(0)


def _insider_total_sold_90d(df, ctx):
    """Total $ value of insider sells in 90 days."""
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Float64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_insider_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0.0] * len(df), dtype=pl.Float64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    sells = trades_df.filter(
        (pl.col("transactionDate") >= cutoff) & (pl.col("acquistionOrDisposition") == "D")
    )
    sell_val = sells.group_by("symbol").agg(
        (pl.col("securitiesTransacted").cast(pl.Float64) * pl.col("price").cast(pl.Float64)).sum().alias("total_sold")
    )
    result = df.select("symbol").join(sell_val, on="symbol", how="left")
    return result["total_sold"].fill_null(0)


def _insider_officer_buying(df, ctx):
    """Any officer/director buying in 90 days (boolean as Int32)."""
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int32)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_insider_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int32)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    officer_buys = trades_df.filter(
        (pl.col("transactionDate") >= cutoff)
        & (pl.col("acquistionOrDisposition") == "A")
        & (pl.col("typeOfOwner").str.to_lowercase().str.contains("officer|director"))
    )
    officers = officer_buys.group_by("symbol").agg(pl.len().alias("officer_buys"))
    result = df.select("symbol").join(officers, on="symbol", how="left")
    return (result["officer_buys"].fill_null(0) > 0).cast(pl.Int32)


# ──────────────────────────────────────────────────────────────────────
# Senate trade aggregations
# ──────────────────────────────────────────────────────────────────────

def _fetch_senate_trades(http, symbols):
    """Fetch senate trades for symbols."""
    import polars as pl

    all_trades = []
    for sym in symbols:
        try:
            trades = http.get("senate-trading", params={"symbol": sym})
            for t in trades:
                t.setdefault("symbol", sym)
            all_trades.extend(trades)
        except Exception:
            pass
    if not all_trades:
        return pl.DataFrame()
    return pl.DataFrame(all_trades, strict=False)


def _get_senate_trades(ctx, http, symbols):
    """Fetch once, cache in ctx."""
    if "_senate_trades" not in ctx:
        ctx["_senate_trades"] = _fetch_senate_trades(http, symbols)
    return ctx["_senate_trades"]


def _senate_buy_count_90d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_senate_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    buys = trades_df.filter(
        (pl.col("transactionDate") >= cutoff)
        & (pl.col("type").str.to_lowercase().str.contains("purchase"))
    )
    counts = buys.group_by("symbol").agg(pl.len().alias("buy_count"))
    result = df.select("symbol").join(counts, on="symbol", how="left")
    return result["buy_count"].fill_null(0)


def _senate_sell_count_90d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_senate_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    sells = trades_df.filter(
        (pl.col("transactionDate") >= cutoff)
        & (pl.col("type").str.to_lowercase().str.contains("sale"))
    )
    counts = sells.group_by("symbol").agg(pl.len().alias("sell_count"))
    result = df.select("symbol").join(counts, on="symbol", how="left")
    return result["sell_count"].fill_null(0)


def _senate_net_flow_90d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int64)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_senate_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    recent = trades_df.filter(pl.col("transactionDate") >= cutoff)

    buy_counts = recent.filter(
        pl.col("type").str.to_lowercase().str.contains("purchase")
    ).group_by("symbol").agg(pl.len().alias("buy_count"))

    sell_counts = recent.filter(
        pl.col("type").str.to_lowercase().str.contains("sale")
    ).group_by("symbol").agg(pl.len().alias("sell_count"))

    result = (
        df.select("symbol")
        .join(buy_counts, on="symbol", how="left")
        .join(sell_counts, on="symbol", how="left")
    )
    return result["buy_count"].fill_null(0) - result["sell_count"].fill_null(0)


def _senate_activity_flag(df, ctx):
    """Any senate trade in 30 days (boolean as Int32)."""
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int32)

    symbols = df["symbol"].unique().to_list()
    trades_df = _get_senate_trades(ctx, http, symbols)
    if trades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int32)

    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    recent = trades_df.filter(pl.col("transactionDate") >= cutoff)
    active = recent.group_by("symbol").agg(pl.len().alias("trade_count"))
    result = df.select("symbol").join(active, on="symbol", how="left")
    return (result["trade_count"].fill_null(0) > 0).cast(pl.Int32)


# ──────────────────────────────────────────────────────────────────────
# Analyst grade aggregations
# ──────────────────────────────────────────────────────────────────────

def _fetch_grades(http, symbols):
    """Fetch analyst grades for symbols."""
    import polars as pl

    all_grades = []
    for sym in symbols:
        try:
            grades = http.get("grades", params={"symbol": sym, "limit": 100})
            for g in grades:
                g.setdefault("symbol", sym)
            all_grades.extend(grades)
        except Exception:
            pass
    if not all_grades:
        return pl.DataFrame()
    return pl.DataFrame(all_grades, strict=False)


def _get_grades(ctx, http, symbols):
    """Fetch once, cache in ctx."""
    if "_grades" not in ctx:
        ctx["_grades"] = _fetch_grades(http, symbols)
    return ctx["_grades"]


def _upgrades_90d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int64)

    symbols = df["symbol"].unique().to_list()
    grades_df = _get_grades(ctx, http, symbols)
    if grades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    upgrades = grades_df.filter(
        (pl.col("date") >= cutoff)
        & (pl.col("action").str.to_lowercase() == "upgrade")
    )
    counts = upgrades.group_by("symbol").agg(pl.len().alias("upgrade_count"))
    result = df.select("symbol").join(counts, on="symbol", how="left")
    return result["upgrade_count"].fill_null(0)


def _downgrades_90d(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Int64)

    symbols = df["symbol"].unique().to_list()
    grades_df = _get_grades(ctx, http, symbols)
    if grades_df.is_empty():
        return pl.Series([0] * len(df), dtype=pl.Int64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    downgrades = grades_df.filter(
        (pl.col("date") >= cutoff)
        & (pl.col("action").str.to_lowercase() == "downgrade")
    )
    counts = downgrades.group_by("symbol").agg(pl.len().alias("downgrade_count"))
    result = df.select("symbol").join(counts, on="symbol", how="left")
    return result["downgrade_count"].fill_null(0)


def _upgrade_downgrade_ratio(df, ctx):
    import polars as pl
    from datetime import datetime, timedelta

    http = ctx.get("http")
    if not http:
        return pl.Series([None] * len(df), dtype=pl.Float64)

    symbols = df["symbol"].unique().to_list()
    grades_df = _get_grades(ctx, http, symbols)
    if grades_df.is_empty():
        return pl.Series([None] * len(df), dtype=pl.Float64)

    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    recent = grades_df.filter(pl.col("date") >= cutoff)

    up_counts = recent.filter(
        pl.col("action").str.to_lowercase() == "upgrade"
    ).group_by("symbol").agg(pl.len().alias("up_count"))

    down_counts = recent.filter(
        pl.col("action").str.to_lowercase() == "downgrade"
    ).group_by("symbol").agg(pl.len().alias("down_count"))

    result = (
        df.select("symbol")
        .join(up_counts, on="symbol", how="left")
        .join(down_counts, on="symbol", how="left")
    )
    up_c = result["up_count"].fill_null(0).cast(pl.Float64)
    down_c = result["down_count"].fill_null(0).cast(pl.Float64)
    return pl.when(down_c > 0).then(up_c / down_c).otherwise(None)


# ──────────────────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────────────────

POST_COMPUTE_FEATURES: list[PostComputeFieldDef] = [
    # EMA
    PostComputeFieldDef("ema_12", _ema(12), ("close",), category="technical"),
    PostComputeFieldDef("ema_20", _ema(20), ("close",), category="technical"),
    PostComputeFieldDef("ema_26", _ema(26), ("close",), category="technical"),
    PostComputeFieldDef("ema_50", _ema(50), ("close",), category="technical"),
    PostComputeFieldDef("ema_200", _ema(200), ("close",), category="technical"),
    # MACD
    PostComputeFieldDef("macd_line", _macd_line, ("close",), category="technical"),
    PostComputeFieldDef("macd_signal", _macd_signal, ("close",), category="technical"),
    PostComputeFieldDef("macd_histogram", _macd_histogram, ("close",), category="technical"),
    # Autocorrelation
    PostComputeFieldDef(
        "return_autocorrelation_21d", _return_autocorrelation, ("close",),
        category="momentum",
    ),
    # Dividend streak
    PostComputeFieldDef(
        "consecutive_dividend_increases", _consecutive_dividend_increases,
        ("adj_dividend",), category="dividend",
    ),
    # Cross-asset
    PostComputeFieldDef(
        "beta_sp500", _beta_sp500, ("close",), category="risk",
        reference_symbols=("^GSPC",),
    ),
    PostComputeFieldDef(
        "alpha_jensen", _alpha_jensen, ("close",), category="risk",
        reference_symbols=("^GSPC",),
    ),
    # Index membership
    PostComputeFieldDef("in_sp500", _in_index("sp500-constituent"), ("close",), category="index_membership"),
    PostComputeFieldDef("in_nasdaq", _in_index("nasdaq-constituent"), ("close",), category="index_membership"),
    PostComputeFieldDef("in_dowjones", _in_index("dowjones-constituent"), ("close",), category="index_membership"),
    # Insider trades
    PostComputeFieldDef("insider_net_buying_90d", _insider_net_buying_90d, ("close",), category="insider"),
    PostComputeFieldDef("insider_buy_count_30d", _insider_buy_count_30d, ("close",), category="insider"),
    PostComputeFieldDef("insider_sell_count_30d", _insider_sell_count_30d, ("close",), category="insider"),
    PostComputeFieldDef("insider_buy_sell_ratio_90d", _insider_buy_sell_ratio_90d, ("close",), category="insider"),
    PostComputeFieldDef("insider_buying_cluster", _insider_buying_cluster, ("close",), category="insider"),
    PostComputeFieldDef("insider_total_bought_90d", _insider_total_bought_90d, ("close",), category="insider"),
    PostComputeFieldDef("insider_total_sold_90d", _insider_total_sold_90d, ("close",), category="insider"),
    PostComputeFieldDef("insider_officer_buying", _insider_officer_buying, ("close",), category="insider"),
    # Senate trades
    PostComputeFieldDef("senate_buy_count_90d", _senate_buy_count_90d, ("close",), category="senate"),
    PostComputeFieldDef("senate_sell_count_90d", _senate_sell_count_90d, ("close",), category="senate"),
    PostComputeFieldDef("senate_net_flow_90d", _senate_net_flow_90d, ("close",), category="senate"),
    PostComputeFieldDef("senate_activity_flag", _senate_activity_flag, ("close",), category="senate"),
    # Analyst grades
    PostComputeFieldDef("upgrades_90d", _upgrades_90d, ("close",), category="analyst"),
    PostComputeFieldDef("downgrades_90d", _downgrades_90d, ("close",), category="analyst"),
    PostComputeFieldDef("upgrade_downgrade_ratio", _upgrade_downgrade_ratio, ("close",), category="analyst"),
]

POST_COMPUTE_REGISTRY: dict[str, PostComputeFieldDef] = {
    f.name: f for f in POST_COMPUTE_FEATURES
}
