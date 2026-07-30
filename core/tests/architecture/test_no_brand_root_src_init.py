"""Architecture fitness: brand root `src/__init__.py` ban (BF1 origen 2026-05-16).

Cross-brand namespace collision guard. Python `find_spec("src")` resolves
to the alphabetically-first `{brand}/src/__init__.py` it finds, shadowing
all other brands' `src` namespaces and breaking conftest imports that do
`import src.shared.*`.

Bootstrap of the multibrand layout (Story 8+) accidentally created empty
`{brand}/src/__init__.py` files in every brand root (incl. `core/`) via a
mass-applied pyproject template that declared `packages = ["src"]`. The
hatchling wheel section tolerates a missing `src/` directory, but the
`__init__.py` files themselves break cross-brand baseline tests.

This test enforces the post-BF1 invariant: NO brand root may contain
`src/__init__.py`. Each brand's Python code lives under
`{brand}/backend/src/` (FastAPI app convention with its own pyproject and
implicit namespace package).

Allowed: `{brand}/backend/src/` (no `__init__.py` — namespace package
per PEP 420) and `core/luana-core-*/src/luana_core_*/` (named packages).
Forbidden: `{brand}/src/__init__.py` at brand root level.
"""

from __future__ import annotations

from pathlib import Path

# Workspace root = parents[3] (this file: core/tests/architecture/X.py).
_WORKSPACE_ROOT: Path = Path(__file__).resolve().parents[3]

# Brand verticals — 4 active + 6 pending bootstrap (per CLAUDE.md + PORTFOLIO).
# `core/` also gets the guard because it suffered the same bootstrap mistake.
_BRANDS_AND_CORE: list[str] = [
    "core",
    "comunify",
    "fitflow",
    "fixia",
    "guestly",
    "inmoflow",
    "lupulo",
    "nicolify",
    "retailly",
    "saasora",
    "vitalia",
]


def test_no_brand_root_src_init() -> None:
    """No brand root may have `{brand}/src/__init__.py` (cross-brand ns collision).

    Real Python code lives under `{brand}/backend/src/` (implicit namespace
    package) or `core/luana-core-*/src/luana_core_*/` (named packages).
    """
    offenders: list[str] = []
    for brand in _BRANDS_AND_CORE:
        init_path = _WORKSPACE_ROOT / brand / "src" / "__init__.py"
        if init_path.exists():
            offenders.append(str(init_path.relative_to(_WORKSPACE_ROOT)))

    assert not offenders, (
        "Brand root `src/__init__.py` files create cross-brand namespace "
        "collision (Python `find_spec('src')` resolves alphabetically to the "
        "first match and shadows all others, breaking conftest imports). "
        "Each brand's code must live under `{brand}/backend/src/` (implicit "
        "namespace package — no __init__.py at src/ root). Offenders:\n  - "
        + "\n  - ".join(offenders)
    )
