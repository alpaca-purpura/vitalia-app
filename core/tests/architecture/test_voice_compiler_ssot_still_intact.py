"""Architecture fitness: PersonalityCompiler SSoT still lives ONLY in brand-studio post Story 6.

Per 03-arch.md §7.7 + ADR-001 §2.4. Re-runs Story 5 V-AG-3 invariant in Story 6
context: only `luana_core_brand_studio.domain.personality` may declare
`class PersonalityCompiler`. Story 6 (luana-core-copilot) must NOT introduce
a parallel implementation.

D-T3 carries this principle forward: BrandVoicePort introduction is Story 7
territory. Until Story 7, brand voice flows through copilot via the existing
`copilot_provider` indirection — copilot DOES NOT redefine PersonalityCompiler.

V-AG-7 validator. Regression cement for Story 5.
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]

CANONICAL_PATH = CORE_DIR / "luana-core-brand-studio" / "src" / "luana_core_brand_studio" / "domain" / "personality.py"

CLASS_PATTERN = re.compile(r"^\s*class\s+PersonalityCompiler\b")


def test_personality_compiler_canonical_unchanged():
    """PersonalityCompiler class MUST still exist in brand-studio/domain/personality.py."""
    assert CANONICAL_PATH.exists(), (
        f"Canonical PersonalityCompiler file missing: {CANONICAL_PATH}. "
        "ADR-001 §2.4 cement violation — voice compiler v2 SSoT lost (Story 5 regression)."
    )

    text = CANONICAL_PATH.read_text(encoding="utf-8")
    found = any(CLASS_PATTERN.search(line) for line in text.splitlines())

    assert found, (
        f"`class PersonalityCompiler` not found in canonical file {CANONICAL_PATH}. "
        "ADR-001 §2.4 cement violation — class must be defined verbatim there."
    )


def test_no_mirror_personality_compiler_in_copilot():
    """No `class PersonalityCompiler` introduced inside luana-core-copilot.

    Re-runs Story 5 V-AG-3 invariant scoped to Story 6 territory. Catches
    accidental Story 6 mirror introductions while Story 5 invariant is
    being re-checked at every PR.
    """
    copilot_src = CORE_DIR / "luana-core-copilot" / "src" / "luana_core_copilot"
    if not copilot_src.exists():
        # Package not yet present — Story 6 not started. Nothing to check.
        return

    violations: list[str] = []
    for path in copilot_src.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if CLASS_PATTERN.search(line):
                violations.append(
                    f"{path.relative_to(copilot_src)}:{lineno}: {line.strip()}",
                )

    assert not violations, (
        "V-AG-7 Story 5 regression cement: PersonalityCompiler mirror introduced "
        "in luana-core-copilot.\n"
        "BrandVoicePort introduction is Story 7. Story 6 MUST consume brand voice "
        "through existing copilot_provider indirection, NOT redefine PersonalityCompiler.\n\n"
        "Violations:\n" + "\n".join(violations)
    )


def test_no_mirror_personality_compiler_workspace_wide():
    """No `class PersonalityCompiler` declarations outside canonical brand-studio.

    Defensive scan: catches mirrors anywhere in core/ workspace, not just
    luana-core-copilot. Mirrors the Story 5 V-AG-3 test.
    """
    violations: list[str] = []

    for path in CORE_DIR.rglob("*.py"):
        try:
            if path.resolve() == CANONICAL_PATH.resolve():
                continue
        except OSError:
            continue

        if "__pycache__" in path.parts or ".venv" in path.parts:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for lineno, line in enumerate(text.splitlines(), 1):
            if CLASS_PATTERN.search(line):
                violations.append(f"{path.relative_to(CORE_DIR)}:{lineno}: {line.strip()}")

    assert not violations, (
        "PersonalityCompiler MUST NOT be mirrored outside brand-studio/domain/personality.py "
        "(ADR-001 §2.4 SSoT cement). Found duplicate(s):\n" + "\n".join(violations)
    )
