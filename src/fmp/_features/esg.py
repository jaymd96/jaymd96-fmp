"""§21 — ESG derived features."""

from __future__ import annotations

from fmp._features._base import _d  # noqa: F401

FEATURES = [
    _d("esg_composite", "esg_score", ("esg_score",), category="esg"),
    _d("esg_env", "esg_environmental", ("esg_environmental",), category="esg"),
    _d("esg_soc", "esg_social", ("esg_social",), category="esg"),
    _d("esg_gov", "esg_governance", ("esg_governance",), category="esg"),
]
