from __future__ import annotations

import pytest
from fmp._ontology import (
    DATASETS,
    FIELD_REGISTRY,
    Grain,
    list_fields,
    resolve_fields,
)


def test_all_datasets_registered():
    assert len(DATASETS) == 24
    assert "daily_price" in DATASETS
    assert "income_statement" in DATASETS
    assert "quote" in DATASETS


def test_field_registry_populated():
    assert len(FIELD_REGISTRY) > 100
    # canonical owners
    assert FIELD_REGISTRY["close"][0] == "daily_price"
    assert FIELD_REGISTRY["revenue"][0] == "income_statement"
    assert FIELD_REGISTRY["price"][0] == "quote"
    assert FIELD_REGISTRY["price_earnings_ratio"][0] == "ratios"


def test_field_conflicts_resolved():
    """Canonical owner wins bare name; others are prefixed."""
    # eps → income_statement; quote gets quote_change_pct
    assert FIELD_REGISTRY["eps"][0] == "income_statement"
    assert FIELD_REGISTRY["quote_change_pct"][0] == "quote"
    # volume → daily_price; quote gets quote_volume
    assert FIELD_REGISTRY["volume"][0] == "daily_price"
    assert FIELD_REGISTRY["quote_volume"][0] == "quote"


def test_resolve_fields_groups_by_dataset():
    grouped = resolve_fields(["close", "volume", "revenue", "net_income"])
    assert set(grouped.keys()) == {"daily_price", "income_statement"}
    assert len(grouped["daily_price"]) == 2
    assert len(grouped["income_statement"]) == 2


def test_resolve_fields_unknown_raises():
    with pytest.raises(ValueError, match="Unknown fields"):
        resolve_fields(["close", "nonexistent_field"])


def test_grain_ordering():
    assert Grain.DAILY < Grain.QUARTERLY
    assert Grain.QUARTERLY < Grain.ANNUAL
    assert Grain.INTRADAY < Grain.DAILY


def test_grain_parse():
    assert Grain.parse("daily") == Grain.DAILY
    assert Grain.parse("QUARTERLY") == Grain.QUARTERLY
    assert Grain.parse("Monthly") == Grain.MONTHLY


def test_grain_trunc_unit():
    assert Grain.DAILY.trunc_unit == "day"
    assert Grain.QUARTERLY.trunc_unit == "quarter"
    assert Grain.ANNUAL.trunc_unit == "year"


def test_list_fields_all():
    fields = list_fields()
    assert "close" in fields
    assert "revenue" in fields
    assert len(fields) > 100


def test_list_fields_by_dataset():
    fields = list_fields("daily_price")
    assert "close" in fields
    assert "volume" in fields
    assert "revenue" not in fields


def test_list_fields_unknown_dataset():
    with pytest.raises(ValueError, match="Unknown dataset"):
        list_fields("nonexistent")
