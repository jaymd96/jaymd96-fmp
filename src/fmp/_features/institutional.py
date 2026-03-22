"""§16 — Institutional ownership derived features."""

from __future__ import annotations

from fmp._features._base import _d  # noqa: F401

FEATURES = [
    _d("inst_holders", "inst_holders_count", ("inst_holders_count",), category="institutional", dtype="INTEGER"),
    _d("inst_holders_delta", "inst_holders_change", ("inst_holders_change",), category="institutional", dtype="INTEGER"),
    _d("inst_invested", "inst_total_invested", ("inst_total_invested",), category="institutional", dtype="BIGINT"),
    _d("inst_invested_delta", "inst_invested_change", ("inst_invested_change",), category="institutional", dtype="BIGINT"),
    _d("inst_put_call", "inst_put_call_ratio", ("inst_put_call_ratio",), category="institutional"),
    _d("inst_holders_growth", "inst_holders_change / NULLIF(ABS(inst_holders_prev), 0)", ("inst_holders_change", "inst_holders_prev"), category="institutional"),
    _d("inst_invested_growth", "inst_invested_change / NULLIF(ABS(inst_invested_prev), 0)", ("inst_invested_change", "inst_invested_prev"), category="institutional"),
]
