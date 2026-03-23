"""Derived feature registry — ~350 computed metrics over base ontology fields."""

from __future__ import annotations

from fmp._features._base import DerivedFieldDef
from fmp._features._post_compute import POST_COMPUTE_REGISTRY, PostComputeFieldDef

from fmp._features.profitability import FEATURES as _profitability
from fmp._features.liquidity import FEATURES as _liquidity
from fmp._features.leverage import FEATURES as _leverage
from fmp._features.efficiency import FEATURES as _efficiency
from fmp._features.valuation import FEATURES as _valuation
from fmp._features.cash_flow_features import FEATURES as _cash_flow
from fmp._features.growth import FEATURES as _growth
from fmp._features.dupont import FEATURES as _dupont
from fmp._features.earnings_quality import FEATURES as _earnings_quality
from fmp._features.per_share import FEATURES as _per_share
from fmp._features.dividend import FEATURES as _dividend
from fmp._features.risk import FEATURES as _risk
from fmp._features.technical import FEATURES as _technical
from fmp._features.momentum import FEATURES as _momentum
from fmp._features.composite import FEATURES as _composite
from fmp._features.analyst import FEATURES as _analyst
from fmp._features.macro import FEATURES as _macro
from fmp._features.sector_relative import FEATURES as _sector_relative
from fmp._features.event_driven import FEATURES as _event_driven
from fmp._features.esg import FEATURES as _esg
from fmp._features.institutional import FEATURES as _institutional
from fmp._features.historical import FEATURES as _historical
from fmp._features.insider import FEATURES as _insider

_ALL_FEATURES: list[DerivedFieldDef] = (
    _profitability + _liquidity + _leverage + _efficiency + _valuation
    + _cash_flow + _growth + _dupont + _earnings_quality + _per_share
    + _dividend + _risk + _technical + _momentum + _composite + _analyst
    + _macro + _sector_relative + _event_driven + _esg + _institutional
    + _historical + _insider
)

DERIVED_REGISTRY: dict[str, DerivedFieldDef] = {f.name: f for f in _ALL_FEATURES}


def resolve_derived_dependencies(names: list[str]) -> tuple[list[str], list[DerivedFieldDef]]:
    """Given a list of derived field names, return the union of base field
    dependencies and the derived field definitions.

    Returns:
        (base_field_names, derived_defs)
    """
    base_deps: set[str] = set()
    derived: list[DerivedFieldDef] = []
    for name in names:
        d = DERIVED_REGISTRY[name]
        derived.append(d)
        base_deps.update(d.dependencies)
    return sorted(base_deps), derived


def list_features(category: str | None = None) -> list[str]:
    """List available feature names (SQL-derived + post-compute)."""
    from fmp._features._post_compute import POST_COMPUTE_REGISTRY

    if category:
        sql = [f.name for f in _ALL_FEATURES if f.category == category]
        post = [f.name for f in POST_COMPUTE_REGISTRY.values() if f.category == category]
        return sql + post
    return list(DERIVED_REGISTRY.keys()) + list(POST_COMPUTE_REGISTRY.keys())


def feature_categories() -> list[str]:
    """List all feature categories."""
    from fmp._features._post_compute import POST_COMPUTE_REGISTRY

    cats = {f.category for f in _ALL_FEATURES if f.category}
    cats |= {f.category for f in POST_COMPUTE_REGISTRY.values() if f.category}
    return sorted(cats)
