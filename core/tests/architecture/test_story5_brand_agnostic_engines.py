"""Architecture fitness: Story 5 engines are brand-agnostic.

Per 03-arch.md §7.1 + outcome §2 brand isolation strategy + ADR-001 §2.4.

Story 5 packages (brand-studio + offer-studio) MUST NOT contain brand-specific
conditionals or hardcoded brand identifiers. Brand isolation is by path
(per-brand value injection happens at vertical bootstrap layers — Stories
11-13), NOT by `if brand == ...` checks inside engine source.

Specifically:
- No 'if brand ==' conditional in source
- No hardcoded Clerk app IDs (app_{...} pattern)
- No hardcoded brand slugs as literals (nicolify, vitalia, comunify, lupulo)
  that gate logic branches — brand slug in comments/docs is allowed

V-AG-1 validator.
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]

STORY5_PACKAGES = [
    "luana-core-brand-studio",
    "luana-core-offer-studio",
]

# Known brand slugs in luana-platform — must not gate logic branches
BRAND_SLUGS = ["nicolify", "vitalia", "comunify", "lupulo"]


def _get_py_files(pkg_name: str):
    pkg_dir = CORE_DIR / pkg_name / "src"
    if not pkg_dir.exists():
        return []
    return list(pkg_dir.rglob("*.py"))


def test_no_brand_conditional():
    """No 'if brand ==' pattern in Story 5 source files."""
    pattern = re.compile(r"if\s+brand\s*==")
    violations = []
    for pkg_name in STORY5_PACKAGES:
        for path in _get_py_files(pkg_name):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    violations.append(
                        f"{pkg_name}/{path.relative_to(CORE_DIR / pkg_name / 'src')}:{lineno}: {line.strip()}",
                    )
    assert not violations, "Story 5 packages must be brand-agnostic. Found 'if brand ==' in:\n" + "\n".join(violations)


def test_no_hardcoded_clerk_app_ids():
    """No hardcoded Clerk app IDs in Story 5 source files.

    Clerk app IDs start with 'app_' followed by >=10 alphanumeric chars.
    """
    pattern = re.compile(r"\bapp_[A-Za-z0-9]{10,}\b")
    violations = []
    for pkg_name in STORY5_PACKAGES:
        for path in _get_py_files(pkg_name):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if pattern.search(line):
                    violations.append(
                        f"{pkg_name}/{path.relative_to(CORE_DIR / pkg_name / 'src')}:{lineno}: {line.strip()}",
                    )
    assert not violations, "Story 5 packages must have no hardcoded Clerk app IDs. Found in:\n" + "\n".join(violations)


def test_no_brand_slug_in_logic():
    """No brand slug (nicolify/vitalia/comunify/lupulo) used in conditional logic.

    Brand slugs in comments, docstrings, or string literals not in conditionals
    are allowed (e.g. documentation examples). Only flag when they appear in
    if/elif/match statements or as function arguments in brand-routing calls.
    """
    # Match 'if ... nicolify' or 'elif ... vitalia' style logic branches
    slug_in_conditional = re.compile(r"\b(if|elif)\b[^#\n]*\b(" + "|".join(BRAND_SLUGS) + r")\b")
    violations = []
    for pkg_name in STORY5_PACKAGES:
        for path in _get_py_files(pkg_name):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if slug_in_conditional.search(line):
                    violations.append(
                        f"{pkg_name}/{path.relative_to(CORE_DIR / pkg_name / 'src')}:{lineno}: {line.strip()}",
                    )
    assert not violations, (
        "Story 5 packages must not branch on brand slug. Found brand-conditional logic in:\n" + "\n".join(violations)
    )
