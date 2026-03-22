"""§19 — Sector-relative derived features.

Most sector-relative features require cross-sectional peer-group queries
(e.g., sector median P/E) that cannot be expressed as single-row SQL
expressions.  Stubs are listed below; full implementations will follow
once the cross-sectional query layer is available.
"""

from __future__ import annotations

from fmp._features._base import _d  # noqa: F401

FEATURES: list = []
