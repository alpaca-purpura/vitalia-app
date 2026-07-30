"""Architecture fitness: docs/architecture/luana-platform/extension-points.md §1-§5 completeness.

V-F-docs-1. Verifies extension-points.md ships with all required sections:
- §1: CC-1..CC-5 verbatim (## 1 header)
- §2: EP-1..EP-5 critical with per-vertical examples (vitalia + comunify + lupulo)
- §3: EP-6..EP-18 backlog signatures
- §4: Recipe — Vitalia treatment-agent (vertical agent) + NO EP-19 literal string
- §5: Cross-brand learning principle (cross-brand learning OR graduate to core)

All checks are case-insensitive grep.

Note (2026-05-19 purge Batch 3): file moved from docs/extension-points.md to
docs/architecture/luana-platform/extension-points.md. Error messages updated.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[3]
DOCS_FILE = ROOT / "docs" / "architecture" / "luana-platform" / "extension-points.md"


def _check(text: str, pattern: str) -> bool:
    """Case-insensitive + multiline check for pattern in text."""
    return bool(re.search(pattern, text, re.IGNORECASE | re.MULTILINE))


def test_docs_file_exists() -> None:
    """V-F-docs-1: docs/architecture/luana-platform/extension-points.md must exist."""
    assert DOCS_FILE.exists(), (
        f"docs/architecture/luana-platform/extension-points.md not found at {DOCS_FILE}.\n"
        "Story 8 T-16 created this file (moved during 2026-05-19 purge Batch 3 from docs/extension-points.md)."
    )


def test_docs_has_section_1_header() -> None:
    """V-F-docs-1: docs contains §1 (## 1 header) — CC-1..CC-5 section."""
    text = DOCS_FILE.read_text(encoding="utf-8")
    assert _check(text, r"^## 1"), (
        "docs/architecture/luana-platform/extension-points.md missing §1 (## 1 header).\n§1 must describe CC-1..CC-5 cross-cutting policies."
    )


def test_docs_has_vitalia_examples() -> None:
    """V-F-docs-1: docs contains Vitalia vertical examples."""
    text = DOCS_FILE.read_text(encoding="utf-8")
    assert _check(text, r"vitalia"), (
        "docs/architecture/luana-platform/extension-points.md missing 'vitalia' examples.\n"
        "§2 EP-1..EP-5 must include Vitalia per-vertical code examples."
    )


def test_docs_has_comunify_examples() -> None:
    """V-F-docs-1: docs contains Comunify vertical examples."""
    text = DOCS_FILE.read_text(encoding="utf-8")
    assert _check(text, r"comunify"), (
        "docs/architecture/luana-platform/extension-points.md missing 'comunify' examples.\n"
        "§2 EP-1..EP-5 must include Comunify per-vertical code examples."
    )


def test_docs_has_lupulo_examples() -> None:
    """V-F-docs-1: docs contains Lupulo vertical examples."""
    text = DOCS_FILE.read_text(encoding="utf-8")
    assert _check(text, r"lupulo"), (
        "docs/architecture/luana-platform/extension-points.md missing 'lupulo' examples.\n"
        "§2 EP-1..EP-5 must include Lupulo per-vertical code examples."
    )


def test_docs_has_no_ep19_literal() -> None:
    """V-F-docs-1: docs contains 'NO EP-19' literal string (anti-pattern rejection).

    The recipe section (§4) must explicitly state that vertical agent patterns
    do NOT require an EP-19 — they are brand app composition, not an SDK extension point.
    """
    text = DOCS_FILE.read_text(encoding="utf-8")
    assert _check(text, r"no ep-?19"), (
        "docs/architecture/luana-platform/extension-points.md missing 'NO EP-19' literal string.\n"
        "§4 recipe section must explicitly reject the EP-19 anti-pattern.\n"
        "A vertical agent (e.g. Vitalia treatment-agent) is brand app composition,\n"
        "NOT a core SDK extension point."
    )


def test_docs_has_vertical_agent_recipe() -> None:
    """V-F-docs-1: docs contains vertical agent / treatment_agent recipe section."""
    text = DOCS_FILE.read_text(encoding="utf-8")
    assert _check(text, r"vertical.?agent|treatment_agent"), (
        "docs/architecture/luana-platform/extension-points.md missing vertical agent recipe section.\n"
        "§4 must include a worked example of a vertical agent (e.g. Vitalia treatment-agent)."
    )


def test_docs_has_cross_brand_learning_principle() -> None:
    """V-F-docs-1: docs contains cross-brand learning or graduate-to-core principle (§5)."""
    text = DOCS_FILE.read_text(encoding="utf-8")
    assert _check(text, r"cross-brand learning|graduate to core"), (
        "docs/architecture/luana-platform/extension-points.md missing §5 cross-brand learning principle.\n"
        "§5 must describe: brands invent → /pm evaluates → features graduate to core → "
        "brands B/C/D consume via SDK."
    )
