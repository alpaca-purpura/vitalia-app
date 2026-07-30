"""Smoke test — verifies the vitalia module is importable."""

from __future__ import annotations


def test_module_importable() -> None:
    """A1/A3 scaffold smoke: vitalia module can be imported."""
    from src.modules.vitalia import __init__  # noqa: F401

    assert True
