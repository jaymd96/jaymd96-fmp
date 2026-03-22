"""Base dataclass for derived features."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DerivedFieldDef:
    """A derived feature computed as a SQL expression over base ontology fields.

    Attributes:
        name: Unique snake_case identifier (e.g., ``"gross_profit_margin"``).
        expression: DuckDB SQL expression. References base field names directly.
            Use ``OVER w`` as a placeholder for window functions — the query
            builder replaces it with ``OVER (PARTITION BY symbol ORDER BY date)``.
        dependencies: Base field names this feature requires from the ontology.
        dtype: DuckDB result type (default ``DOUBLE``).
        category: Grouping label (e.g., ``"profitability"``).
        requires_lag: If ``True``, the expression uses ``LAG``/``LEAD`` window
            functions and requires the ``WINDOW w`` clause.
    """

    name: str
    expression: str
    dependencies: tuple[str, ...]
    dtype: str = "DOUBLE"
    category: str = ""
    requires_lag: bool = False


def _d(
    name: str,
    expr: str,
    deps: tuple[str, ...],
    *,
    category: str = "",
    dtype: str = "DOUBLE",
    lag: bool = False,
) -> DerivedFieldDef:
    """Shorthand constructor."""
    return DerivedFieldDef(
        name=name,
        expression=expr,
        dependencies=deps,
        dtype=dtype,
        category=category,
        requires_lag=lag,
    )
