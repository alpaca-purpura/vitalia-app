"""Architecture fitness: PersonalityCompiler SSoT regression — Stories 5+6+7.

Per 03-arch.md §7.7 + ADR-001 §2.4. Re-runs Story 5 V-AG-3 + Story 6 V-AG-7
invariant in Story 7 context: only `luana_core_brand_studio.domain.personality`
may declare `class PersonalityCompiler`. Stories 5+6+7 must NOT introduce
parallel implementations.

Story 7 specifically: D-T3 BrandVoicePort introduction creates a hexagonal
port WRAPPING the existing compiler. The compiler itself stays in
brand_studio/domain/personality.py — port adapter binds it in brand_studio
composition root. sales-agent NEVER redefines or mirrors.

V-AG-7 validator. Regression cement for Stories 5+6+7.
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
        "ADR-001 §2.4 cement violation — voice compiler v2 SSoT lost "
        "(Story 5+6+7 regression)."
    )

    text = CANONICAL_PATH.read_text(encoding="utf-8")
    found = any(CLASS_PATTERN.search(line) for line in text.splitlines())

    assert found, (
        f"`class PersonalityCompiler` not found in canonical file {CANONICAL_PATH}. "
        "ADR-001 §2.4 cement violation — class must be defined verbatim there."
    )


def test_no_mirror_personality_compiler_in_sales_agent():
    """No `class PersonalityCompiler` introduced inside luana-core-sales-agent.

    Re-runs Story 5 V-AG-3 invariant scoped to Story 7 territory. Catches
    accidental Story 7 mirror introductions while Story 5 invariant is
    being re-checked at every PR.

    D-T3 cardinal: sales-agent consumes voice via BrandVoicePort hexagonal
    port. It MUST NEVER redefine PersonalityCompiler.
    """
    sales_agent_src = CORE_DIR / "luana-core-sales-agent" / "src" / "luana_core_sales_agent"
    if not sales_agent_src.exists():
        # Package not yet present — Story 7 not started. Nothing to check.
        return

    violations: list[str] = []
    for path in sales_agent_src.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if CLASS_PATTERN.search(line):
                violations.append(
                    f"{path.relative_to(sales_agent_src)}:{lineno}: {line.strip()}",
                )

    assert not violations, (
        "V-AG-7 Story 5+6+7 regression cement: PersonalityCompiler mirror "
        "introduced in luana-core-sales-agent.\n"
        "D-T3 cardinal: sales-agent consumes voice via BrandVoicePort. "
        "MUST NEVER redefine PersonalityCompiler.\n\n"
        "Violations:\n" + "\n".join(violations)
    )


def test_no_mirror_personality_compiler_workspace_wide():
    """No `class PersonalityCompiler` declarations outside canonical brand-studio.

    Defensive scan: catches mirrors anywhere in core/ workspace, not just
    luana-core-sales-agent. Mirrors the Story 5 V-AG-3 test + Story 6 V-AG-7.
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
        "(ADR-001 §2.4 SSoT cement Stories 5+6+7). Found duplicate(s):\n" + "\n".join(violations)
    )
