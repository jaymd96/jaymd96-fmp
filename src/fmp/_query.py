"""Ontology-driven query builder with grain alignment and SQL generation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

from fmp._exceptions import FMPError
from fmp._features import DERIVED_REGISTRY, resolve_derived_dependencies
from fmp._features._base import DerivedFieldDef
from fmp._features._post_compute import POST_COMPUTE_REGISTRY, PostComputeFieldDef
from fmp._ontology import DATASETS, FIELD_REGISTRY, Grain, resolve_fields

if TYPE_CHECKING:
    from fmp._http import HTTPClient
    from fmp._store import BitemporalStore


# ──────────────────────────────────────────────────────────────────────
# Aggregation function mapping
# ──────────────────────────────────────────────────────────────────────

_AGG_SQL: dict[str, str] = {
    "first": "FIRST({col} ORDER BY date)",
    "last": "LAST({col} ORDER BY date)",
    "sum": "SUM({col})",
    "mean": "AVG({col})",
    "avg": "AVG({col})",
    "max": "MAX({col})",
    "min": "MIN({col})",
    "median": "MEDIAN({col})",
    "count": "COUNT({col})",
}


class QueryBuilder:
    """Fluent builder for cross-dataset queries with grain alignment.

    Returned by :meth:`FMPClient.query`.
    """

    def __init__(
        self,
        http: HTTPClient,
        store: BitemporalStore,
        ttls: dict[str, int],
    ) -> None:
        self._http = http
        self._store = store
        self._ttls = ttls
        self._symbols: list[str] = []
        self._fields: list[str] = []
        self._start: str | None = None
        self._end: str | None = None
        self._target_grain: Grain | None = None
        self._agg_overrides: dict[str, str] = {}
        self._force: bool = False

    # ------------------------------------------------------------------
    # Builder methods
    # ------------------------------------------------------------------

    def symbols(self, *syms: str | list[str]) -> QueryBuilder:
        """Set the symbols to query."""
        for s in syms:
            if isinstance(s, list):
                self._symbols.extend(s)
            else:
                self._symbols.append(s)
        return self

    def select(self, *fields: str) -> QueryBuilder:
        """Choose which fields to include in the result."""
        self._fields.extend(fields)
        return self

    def date_range(self, start: str, end: str) -> QueryBuilder:
        """Filter to a date range (inclusive)."""
        self._start = start
        self._end = end
        return self

    def grain(self, grain: str) -> QueryBuilder:
        """Set the output granularity: daily, weekly, monthly, quarterly, annual."""
        self._target_grain = Grain.parse(grain)
        return self

    def agg(self, **overrides: str) -> QueryBuilder:
        """Override default aggregation for specific fields."""
        self._agg_overrides.update(overrides)
        return self

    def force_refresh(self) -> QueryBuilder:
        """Bypass cache and re-fetch all data from the API."""
        self._force = True
        return self

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, backend: str = "polars") -> Any:
        """Run the query and return a DataFrame.

        Args:
            backend: ``"polars"`` (default, zero-copy via Arrow) or ``"pandas"``.
        """
        # Validate
        if not self._symbols:
            raise FMPError("No symbols specified. Call .symbols() first.")
        if not self._fields:
            raise FMPError("No fields specified. Call .select() first.")

        # 1. Split into base, derived (SQL), and post-compute fields.
        #    Check order: post-compute → derived → base.
        base_fields: list[str] = []
        derived_names: list[str] = []
        post_compute_defs: list[PostComputeFieldDef] = []
        for f in self._fields:
            if f in POST_COMPUTE_REGISTRY:
                post_compute_defs.append(POST_COMPUTE_REGISTRY[f])
            elif f in DERIVED_REGISTRY:
                derived_names.append(f)
            elif f in FIELD_REGISTRY:
                base_fields.append(f)
            else:
                raise FMPError(f"Unknown field: {f!r}")

        # 2. Resolve derived dependencies → additional base fields
        derived_defs: list[DerivedFieldDef] = []
        if derived_names:
            dep_bases, derived_defs = resolve_derived_dependencies(derived_names)
            for dep in dep_bases:
                if dep not in base_fields and dep in FIELD_REGISTRY:
                    base_fields.append(dep)

        # 2b. Resolve post-compute dependencies → additional base fields
        for pc in post_compute_defs:
            for dep in pc.dependencies:
                if dep not in base_fields and dep in FIELD_REGISTRY:
                    base_fields.append(dep)

        # 3. Resolve base fields → datasets
        grouped = resolve_fields(base_fields) if base_fields else {}

        # 4. Determine target grain
        target = self._resolve_target_grain(grouped)

        # 5. Fetch data into typed tables
        self._fetch_datasets(grouped)

        # 5b. Fetch reference symbols for post-compute features (e.g., ^GSPC for beta)
        reference_data: dict[str, Any] = {}
        if post_compute_defs:
            reference_data = self._fetch_reference_data(post_compute_defs, grouped)

        # 6. Generate SQL (with derived expressions)
        sql = self._generate_sql(grouped, target, derived_defs)

        # 7. Execute SQL
        result = self._store._conn.execute(sql)

        if backend == "polars":
            import polars as pl
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            df = pl.DataFrame(
                [dict(zip(columns, row)) for row in rows],
                strict=False,
            )
        elif backend == "pandas":
            df = result.fetchdf()
        else:
            raise FMPError(f"Unknown backend: {backend!r}. Use 'polars' or 'pandas'.")

        # 8. Apply post-compute features
        if post_compute_defs and backend == "polars":
            df = self._apply_post_compute(df, post_compute_defs, reference_data)
        elif post_compute_defs and backend == "pandas":
            raise FMPError(
                "Post-compute features (EMA, MACD, beta, etc.) require backend='polars'."
            )

        return df

    def _fetch_reference_data(
        self,
        post_compute_defs: list[PostComputeFieldDef],
        grouped: dict[str, list],
    ) -> dict:
        """Fetch reference symbols needed by post-compute features (e.g., ^GSPC)."""
        ref_symbols: set[str] = set()
        for pc in post_compute_defs:
            ref_symbols.update(pc.reference_symbols)

        if not ref_symbols:
            return {}

        reference_data: dict = {}
        for sym in ref_symbols:
            ds = DATASETS.get("daily_price")
            if not ds:
                continue
            params: dict[str, str] = {"symbol": sym}
            if self._start:
                params["from"] = self._start
            if self._end:
                params["to"] = self._end
            try:
                rows = self._http.get(ds.endpoint, params=params)
                if rows:
                    for row in rows:
                        row.setdefault("symbol", sym)
                    self._store.write("daily_price", rows)
                    import polars as pl
                    reference_data[sym] = pl.DataFrame(rows, strict=False)
            except Exception:
                pass

        return {"reference_data": reference_data}

    @staticmethod
    def _apply_post_compute(df, post_compute_defs, ctx):
        """Apply post-compute features to the DataFrame."""
        for pc in post_compute_defs:
            try:
                series = pc.compute_fn(df, ctx)
                df = df.with_columns(series.alias(pc.name))
            except Exception:
                import polars as pl
                df = df.with_columns(pl.lit(None).cast(pl.Float64).alias(pc.name))
        return df

    # ------------------------------------------------------------------
    # Internal: grain resolution
    # ------------------------------------------------------------------

    def _resolve_target_grain(
        self, grouped: dict[str, list],
    ) -> Grain:
        if self._target_grain is not None:
            return self._target_grain

        # Pick the finest non-snapshot grain
        grains = [
            DATASETS[ds_name].grain
            for ds_name in grouped
            if DATASETS[ds_name].grain != Grain.SNAPSHOT
        ]
        if not grains:
            return Grain.SNAPSHOT
        return min(grains)

    # ------------------------------------------------------------------
    # Internal: fetch and store data
    # ------------------------------------------------------------------

    def _fetch_datasets(self, grouped: dict[str, list]) -> None:
        """Fetch each required dataset, writing to the bitemporal store."""
        tasks: list[tuple[str, str | None]] = []  # (dataset_name, symbol_or_None)

        for ds_name in grouped:
            ds = DATASETS[ds_name]
            ttl = self._ttls.get(ds.ttl_category, self._ttls.get("default", 3600))

            if "symbol" not in ds.keys:
                # Date-only dataset (e.g., treasury_rates) — fetch once
                if not self._force and self._store.is_fresh(ds_name, None, ttl):
                    continue
                tasks.append((ds_name, None))
            else:
                for sym in self._symbols:
                    if not self._force and self._store.is_fresh(ds_name, sym, ttl):
                        continue
                    tasks.append((ds_name, sym))

        if not tasks:
            return

        def _fetch_one(ds_name: str, symbol: str | None) -> None:
            ds = DATASETS[ds_name]
            params: dict[str, str] = {}
            if symbol:
                params["symbol"] = symbol
            if "date" in ds.keys and self._start:
                params["from"] = self._start
            if "date" in ds.keys and self._end:
                params["to"] = self._end
            rows = self._http.get(ds.endpoint, params=params)
            if rows:
                if symbol:
                    for row in rows:
                        row.setdefault("symbol", symbol)
                self._store.write(ds_name, rows)

        with ThreadPoolExecutor(max_workers=min(10, len(tasks))) as pool:
            futures = {
                pool.submit(_fetch_one, ds_name, sym): (ds_name, sym)
                for ds_name, sym in tasks
            }
            for future in as_completed(futures):
                exc = future.exception()
                if exc:
                    ds_name, sym = futures[future]
                    # Log but don't fail the whole query for partial errors
                    pass

    # ------------------------------------------------------------------
    # Internal: SQL generation
    # ------------------------------------------------------------------

    def _generate_sql(
        self,
        grouped: dict[str, list],
        target: Grain,
        derived: list[DerivedFieldDef] | None = None,
    ) -> str:
        """Build the full CTE-based SQL query."""
        ctes: list[str] = []
        aligned_names: list[str] = []
        dataset_infos: list[tuple[str, Grain, list]] = []

        sym_placeholders = ", ".join(f"'{s}'" for s in self._symbols)

        for ds_name, fields in grouped.items():
            ds = DATASETS[ds_name]
            field_names = [f.name for f in fields]

            # ── Dedup CTE ──
            select_cols = list(ds.keys) + field_names
            dedup_select = ", ".join(select_cols)
            partition_keys = ", ".join(ds.keys)

            where_parts: list[str] = []
            has_symbol = "symbol" in ds.keys
            if has_symbol:
                where_parts.append(f"symbol IN ({sym_placeholders})")
            # For datasets coarser than the target grain, skip the start-date
            # filter — ASOF JOIN needs preceding data to carry forward.
            will_asof = (
                ds.grain != Grain.SNAPSHOT
                and ds.grain > target
            )
            if "date" in ds.keys:
                if self._start and not will_asof:
                    where_parts.append(f"date >= '{self._start}'")
                if self._end:
                    where_parts.append(f"date <= '{self._end}'")
            where_clause = " AND ".join(where_parts)

            dedup_name = f"{ds_name}_dedup"
            ctes.append(
                f"{dedup_name} AS (\n"
                f"    SELECT {dedup_select}\n"
                f"    FROM {ds_name}\n"
                f"    WHERE {where_clause}\n"
                f"    QUALIFY ROW_NUMBER() OVER (\n"
                f"        PARTITION BY {partition_keys}\n"
                f"        ORDER BY _fetched_at DESC\n"
                f"    ) = 1\n"
                f")"
            )

            # ── Alignment CTE (if needed) ──
            aligned_name = dedup_name
            if ds.grain != Grain.SNAPSHOT and ds.grain != target:
                if ds.grain < target:
                    # Finer → coarser: roll up with aggregation
                    aligned_name = f"{ds_name}_agg"
                    trunc_unit = target.trunc_unit
                    agg_exprs = []
                    for f in fields:
                        agg_fn = self._agg_overrides.get(f.name, f.agg)
                        template = _AGG_SQL.get(agg_fn, "LAST({col} ORDER BY date)")
                        agg_exprs.append(f"{template.format(col=f.name)} AS {f.name}")

                    has_sym = "symbol" in ds.keys
                    group_cols = (
                        "symbol, " if has_sym else ""
                    ) + f"DATE_TRUNC('{trunc_unit}', date)"
                    select_prefix = (
                        "symbol, " if has_sym else ""
                    ) + f"DATE_TRUNC('{trunc_unit}', date) AS date"
                    ctes.append(
                        f"{aligned_name} AS (\n"
                        f"    SELECT {select_prefix},\n"
                        f"           {', '.join(agg_exprs)}\n"
                        f"    FROM {dedup_name}\n"
                        f"    GROUP BY {group_cols}\n"
                        f")"
                    )
                # Coarser → finer: handled via ASOF JOIN in final SELECT

            aligned_names.append(aligned_name)
            dataset_infos.append((aligned_name, ds.grain, fields))

        # ── Build field-to-alias mapping and SELECT ──
        derived = derived or []

        if len(dataset_infos) == 1:
            name, grain, fields = dataset_infos[0]
            ds_def = DATASETS[[k for k, v in DATASETS.items()
                               if any(name.startswith(k) for _ in [1])][0]]
            has_symbol = "symbol" in ds_def.keys
            field_to_alias: dict[str, str] = {f.name: f.name for f in fields}
            base_cols = [f.name for f in fields]
            key_cols = []
            if has_symbol:
                key_cols.append("symbol")
            if grain != Grain.SNAPSHOT:
                key_cols.append("date")
            derived_exprs = self._resolve_derived_exprs(derived, field_to_alias)
            all_cols = key_cols + base_cols + derived_exprs
            has_lag = any(d.requires_lag for d in derived)
            partition = "PARTITION BY symbol ORDER BY date" if has_symbol else "ORDER BY date"
            window = f"\nWINDOW w AS ({partition})" if has_lag else ""
            return (
                f"WITH {', '.join(ctes)}\n"
                f"SELECT {', '.join(all_cols)}\n"
                f"FROM {name}{window}\n"
                f"ORDER BY {', '.join(key_cols) if key_cols else 'date'}"
            )

        # Multiple datasets — need joins
        anchor = None
        others: list[tuple[str, Grain, list]] = []
        for info in dataset_infos:
            name, grain, fields = info
            if grain == target or (grain != Grain.SNAPSHOT and grain < target):
                if anchor is None:
                    anchor = info
                else:
                    others.append(info)
            else:
                others.append(info)

        if anchor is None:
            for i, info in enumerate(dataset_infos):
                if info[1] != Grain.SNAPSHOT:
                    anchor = info
                    others = [x for j, x in enumerate(dataset_infos) if j != i]
                    break
            if anchor is None:
                anchor = dataset_infos[0]
                others = dataset_infos[1:]

        anchor_name, anchor_grain, anchor_fields = anchor
        anchor_alias = "t0"

        # Determine if anchor has symbol
        anchor_ds_name = anchor_name.replace("_dedup", "").replace("_agg", "")
        anchor_ds = DATASETS.get(anchor_ds_name)
        anchor_has_symbol = anchor_ds is not None and "symbol" in anchor_ds.keys

        # Build field-to-alias mapping
        field_to_alias = {}
        select_parts = []
        if anchor_has_symbol:
            select_parts.append(f"{anchor_alias}.symbol")
        if anchor_grain != Grain.SNAPSHOT:
            select_parts.append(f"{anchor_alias}.date")
        for f in anchor_fields:
            select_parts.append(f"{anchor_alias}.{f.name}")
            field_to_alias[f.name] = f"{anchor_alias}.{f.name}"

        # Build JOIN clauses
        join_clauses: list[str] = []
        for i, (name, grain, fields) in enumerate(others, 1):
            alias = f"t{i}"
            for f in fields:
                select_parts.append(f"{alias}.{f.name}")
                field_to_alias[f.name] = f"{alias}.{f.name}"

            # Determine if this dataset has a symbol key
            other_ds_name = name.replace("_dedup", "").replace("_agg", "")
            other_ds = DATASETS.get(other_ds_name)
            other_has_symbol = other_ds and "symbol" in other_ds.keys

            if not other_has_symbol:
                # Date-only dataset (e.g., treasury_rates) — join on date only
                join_clauses.append(
                    f"LEFT JOIN {name} {alias} ON {anchor_alias}.date = {alias}.date"
                )
            elif grain == Grain.SNAPSHOT:
                join_clauses.append(
                    f"LEFT JOIN {name} {alias} ON {anchor_alias}.symbol = {alias}.symbol"
                )
            elif grain > target:
                join_clauses.append(
                    f"ASOF JOIN {name} {alias} "
                    f"ON {anchor_alias}.symbol = {alias}.symbol "
                    f"AND {anchor_alias}.date >= {alias}.date"
                )
            else:
                if anchor_grain == Grain.SNAPSHOT:
                    join_clauses.append(
                        f"LEFT JOIN {name} {alias} ON {anchor_alias}.symbol = {alias}.symbol"
                    )
                else:
                    join_clauses.append(
                        f"LEFT JOIN {name} {alias} "
                        f"ON {anchor_alias}.symbol = {alias}.symbol "
                        f"AND {anchor_alias}.date = {alias}.date"
                    )

        # Add derived expressions
        derived_exprs = self._resolve_derived_exprs(derived, field_to_alias)
        select_parts.extend(derived_exprs)

        select_str = ",\n       ".join(select_parts)
        joins_str = "\n".join(join_clauses)
        order = f"{anchor_alias}.symbol"
        if anchor_grain != Grain.SNAPSHOT:
            order += f", {anchor_alias}.date"

        has_lag = any(d.requires_lag for d in derived)
        window = (
            f"\nWINDOW w AS (PARTITION BY {anchor_alias}.symbol ORDER BY {anchor_alias}.date)"
            if has_lag else ""
        )

        final = (
            f"WITH {','.join(chr(10) + cte for cte in ctes)}\n"
            f"SELECT {select_str}\n"
            f"FROM {anchor_name} {anchor_alias}\n"
            f"{joins_str}{window}\n"
            f"ORDER BY {order}"
        )
        return final

    @staticmethod
    def _resolve_derived_exprs(
        derived: list[DerivedFieldDef],
        field_to_alias: dict[str, str],
    ) -> list[str]:
        """Substitute base field references with table aliases in derived expressions."""
        results: list[str] = []
        for d in derived:
            expr = d.expression
            # Replace base field names with aliased versions.
            # Sort by length descending to avoid partial matches.
            for field_name in sorted(field_to_alias, key=len, reverse=True):
                alias = field_to_alias[field_name]
                if alias != field_name:
                    # Use word-boundary replacement to avoid partial matches
                    import re
                    expr = re.sub(rf'\b{re.escape(field_name)}\b', alias, expr)
            results.append(f"({expr}) AS {d.name}")
        return results
