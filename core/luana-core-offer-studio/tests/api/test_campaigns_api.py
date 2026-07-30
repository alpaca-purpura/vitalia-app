"""Integration tests for ``GET /offer/products/{id}/campaigns``.

NOTE: Deferred to Story 8 — campaigns.py requires src.modules.advertising (Story 8 lift).
All tests in this file are skipped per 05-guidelines.md §3.3.
"""

import pytest

pytest.skip(
    "DEFERRED Story 8 — campaigns.py needs advertising module (luana_core_advertising not yet lifted)",
    allow_module_level=True,
)
