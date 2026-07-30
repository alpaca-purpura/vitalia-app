"""Architecture fitness: workspace members alphabetical post-Story-8.

V-NF-1. Story 8 baseline: 26 Python workspace members + 7 TS workspace members.
Enforces alphabetical ordering of Python members (excluding 'core' root and
brand app TS entries: nicolify, vitalia, comunify, lupulo).

Story 7 baseline was 23. Story 8 adds 3:
  - core/luana-core-campaigns
  - core/luana-core-extension-sdk
  - apps/test-brand

Total Python-26 = all members except 'core', 'nicolify', 'vitalia', 'comunify', 'lupulo'.
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).parents[3]
PYPROJECT = ROOT / "pyproject.toml"

_BRAND_TS_APPS = frozenset({"nicolify", "vitalia", "comunify", "lupulo"})
_ROOT_META = frozenset({"core"})
_EXCLUDE = _BRAND_TS_APPS | _ROOT_META

_EXPECTED_COUNT = 28  # post 2026-06-02: +1 luana-core-flows (durable-flows-engine proposal 2026-06-02)
_EXPECTED_TS_COUNT = 7
_TS_PACKAGES_DIR = ROOT / "core" / "@luana"


def _python_members() -> list[str]:
    """Return the 26 Python workspace members from pyproject.toml."""
    data = tomllib.loads(PYPROJECT.read_text())
    members: list[str] = data["tool"]["uv"]["workspace"]["members"]
    return [m for m in members if m not in _EXCLUDE]


def test_python_member_count_is_27() -> None:
    """V-NF-1: exactly 28 Python workspace members post 2026-06-02.

    Story 8 baseline was 26. ADR-003 Proposal #4 (scheduling lift) added
    luana-core-scheduling = 27. Durable-flows-engine proposal 2026-06-02 added
    luana-core-flows = 28 total.
    """
    members = _python_members()
    assert len(members) == _EXPECTED_COUNT, (
        f"Expected {_EXPECTED_COUNT} Python workspace members, got {len(members)}.\n"
        f"Current members: {members}\n\n"
        "2026-06-02 baseline: 28 = 27 (scheduling) + 1 NEW (luana-core-flows, durable-flows-engine)."
    )


def test_python_members_alphabetical() -> None:
    """V-NF-1: Python workspace members must be in strict alphabetical order.

    Excludes 'core' root node and brand TS apps (nicolify/vitalia/comunify/lupulo)
    which appear at the end by convention.
    """
    members = _python_members()
    expected = sorted(members)
    assert members == expected, (
        "Python workspace members are NOT alphabetical.\n\n"
        "Current order diverges from sorted order.\n"
        "Fix: reorder [tool.uv.workspace] members in luana-platform/pyproject.toml.\n\n"
        f"Current:  {members}\n"
        f"Expected: {expected}"
    )


def test_story8_new_members_present() -> None:
    """V-NF-1: the 3 NEW Story-8 Python packages must be registered."""
    members = _python_members()
    required = [
        "core/luana-core-campaigns",
        "core/luana-core-extension-sdk",
        "apps/test-brand",
    ]
    missing = [m for m in required if m not in members]
    assert not missing, (
        f"Story 8 required workspace members missing: {missing}\n"
        "Add them to [tool.uv.workspace] members in pyproject.toml."
    )


def test_ts_package_count_is_7() -> None:
    """V-NF-1: exactly 7 TS workspace members under core/@luana/."""
    ts_pkgs = sorted(p.name for p in _TS_PACKAGES_DIR.iterdir() if p.is_dir())
    assert len(ts_pkgs) == _EXPECTED_TS_COUNT, (
        f"Expected {_EXPECTED_TS_COUNT} TS packages under core/@luana/, got {len(ts_pkgs)}.\nFound: {ts_pkgs}"
    )
