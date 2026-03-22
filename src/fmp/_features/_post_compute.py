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
]

POST_COMPUTE_REGISTRY: dict[str, PostComputeFieldDef] = {
    f.name: f for f in POST_COMPUTE_FEATURES
}
