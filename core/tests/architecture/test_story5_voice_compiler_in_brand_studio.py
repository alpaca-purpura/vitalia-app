"""Architecture fitness: PersonalityCompiler SSoT lives in brand-studio.

Per 03-arch.md §7.3 + §10 + ADR-001 §2.4. The voice compiler v2 (PersonalityCompiler)
MUST live verbatim in luana-core-brand-studio.domain.personality and NOT be
mirrored anywhere else in the core/ workspace.

This test BLOCKS any future story from creating a parallel PersonalityCompiler
class (Story 7 BrandVoicePort lift will consume this single class from
brand-studio via port abstraction; it MUST NOT re-implement it).

V-AG-3 validator.
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]

CANONICAL_PATH = CORE_DIR / "luana-core-brand-studio" / "src" / "luana_core_brand_studio" / "domain" / "personality.py"

# Match `class PersonalityCompiler` at start of line (possibly indented for nested)
CLASS_PATTERN = re.compile(r"^\s*class\s+PersonalityCompiler\b")


def test_personality_compiler_exists_in_canonical_location():
    """PersonalityCompiler class MUST exist in brand-studio/domain/personality.py."""
    assert CANONICAL_PATH.exists(), (
        f"Canonical PersonalityCompiler file missing: {CANONICAL_PATH}. "
        "ADR-001 §2.4 cement violation — voice compiler v2 SSoT lost."
    )

    text = CANONICAL_PATH.read_text(encoding="utf-8")
    found = any(CLASS_PATTERN.search(line) for line in text.splitlines())

    assert found, (
        f"`class PersonalityCompiler` not found in canonical file {CANONICAL_PATH}. "
        "ADR-001 §2.4 cement violation — placement requires the class be defined there verbatim."
    )


def test_no_mirror_personality_compiler_class():
    """No `class PersonalityCompiler` outside the canonical brand-studio location."""
    violations = []

    for path in CORE_DIR.rglob("*.py"):
        # Skip the canonical location
        try:
            if path.resolve() == CANONICAL_PATH.resolve():
                continue
        except OSError:
            continue

        # Skip __pycache__ and .venv (anything under .venv shouldn't be in
        # core/ but defensive)
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
