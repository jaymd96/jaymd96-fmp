"""Insider trading derived features — per-transaction metrics for aggregation."""

from __future__ import annotations

from fmp._features._base import _d

FEATURES = [
    # Per-transaction dollar value (price × shares transacted)
    _d(
        "insider_trade_value",
        "insider_price * securities_transacted",
        ("insider_price", "securities_transacted"),
        category="insider",
    ),
    # Buy dollar value (0 for sells) — sums to monthly inflow at coarser grain
    _d(
        "insider_buy_value",
        "CASE WHEN acquisition_or_disposition = 'A' THEN insider_price * securities_transacted ELSE 0 END",
        ("insider_price", "securities_transacted", "acquisition_or_disposition"),
        category="insider",
    ),
    # Sell dollar value (0 for buys) — sums to monthly outflow at coarser grain
    _d(
        "insider_sell_value",
        "CASE WHEN acquisition_or_disposition = 'D' THEN insider_price * securities_transacted ELSE 0 END",
        ("insider_price", "securities_transacted", "acquisition_or_disposition"),
        category="insider",
    ),
    # Net flow per transaction (positive = buy, negative = sell)
    _d(
        "insider_net_flow",
        "CASE WHEN acquisition_or_disposition = 'A' THEN insider_price * securities_transacted "
        "WHEN acquisition_or_disposition = 'D' THEN -(insider_price * securities_transacted) "
        "ELSE 0 END",
        ("insider_price", "securities_transacted", "acquisition_or_disposition"),
        category="insider",
    ),
    # Buy share count (0 for sells)
    _d(
        "insider_shares_bought",
        "CASE WHEN acquisition_or_disposition = 'A' THEN securities_transacted ELSE 0 END",
        ("securities_transacted", "acquisition_or_disposition"),
        category="insider",
        dtype="BIGINT",
    ),
    # Sell share count (0 for buys)
    _d(
        "insider_shares_sold",
        "CASE WHEN acquisition_or_disposition = 'D' THEN securities_transacted ELSE 0 END",
        ("securities_transacted", "acquisition_or_disposition"),
        category="insider",
        dtype="BIGINT",
    ),
    # Is this an officer/director trade? (boolean as integer)
    _d(
        "insider_is_officer",
        "CASE WHEN type_of_owner LIKE '%officer%' OR type_of_owner LIKE '%director%' THEN 1 ELSE 0 END",
        ("type_of_owner",),
        category="insider",
        dtype="INTEGER",
    ),
]
