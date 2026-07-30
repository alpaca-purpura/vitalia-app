"""Architecture fitness: Story 7 sales-agent engine is brand-agnostic.

Per 03-arch.md §7.1 + outcome §2 brand isolation strategy + ADR-001 §2.4.

Story 7 package (luana-core-sales-agent) MUST NOT contain brand-specific
conditionals or hardcoded brand identifiers. Brand isolation is by path
(per-brand value injection happens at vertical bootstrap layers — Stories
11-13), NOT by `if brand == ...` checks inside engine source.

Specifically:
- No 'if brand ==', 'if tenant.brand ==', 'if self.brand ==' conditionals
- No brand-slug equality literal comparisons
  (nicolify, vitalia, comunify, lupulo)
- No hardcoded Clerk app IDs (app_{...} pattern)
- No hardcoded API_KEY / SECRET / TOKEN literals (must reference env/settings)

V-AG-1 validator (Story 7 parity of Story 6 V-AG-1).
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]

STORY7_PACKAGES = [
    ("luana-core-sales-agent", "luana_core_sales_agent"),
]

# Known brand slugs in luana-platform — must not gate logic branches
BRAND_SLUGS = ["nicolify", "vitalia", "comunify", "lupulo"]

FORBIDDEN_CONDITIONAL_PATTERNS = [
    re.compile(r"if\s+brand\s*=="),
    re.compile(r"if\s+tenant\.brand\s*=="),
    re.compile(r"if\s+self\.brand\s*=="),
]

BRAND_SLUG_EQUALITY = re.compile(
    r'\bbrand\s*==\s*["\'](' + "|".join(BRAND_SLUGS) + r')["\']',
)

CLERK_APP_ID_PATTERN = re.compile(r"\bapp_[A-Za-z0-9]{10,}\b")

HARDCODED_SECRET_PATTERN = re.compile(
    r'(API_KEY|SECRET|TOKEN)\s*=\s*["\'](?!os\.|settings\.|env|getenv).{8,}["\']',
)


def _get_py_files(pkg_dir_name: str, pkg_module_name: str):
    pkg_dir = CORE_DIR / pkg_dir_name / "src" / pkg_module_name
    if not pkg_dir.exists():
        return []
    return list(pkg_dir.rglob("*.py"))


def test_no_brand_conditional():
    """No 'if brand ==' style conditionals in Story 7 source."""
    violations = []
    for pkg_dir_name, pkg_module_name in STORY7_PACKAGES:
        for path in _get_py_files(pkg_dir_name, pkg_module_name):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                for pattern in FORBIDDEN_CONDITIONAL_PATTERNS:
                    if pattern.search(line):
                        violations.append(
                            f"{pkg_dir_name}/{path.relative_to(CORE_DIR / pkg_dir_name / 'src' / pkg_module_name)}:"
                            f"{lineno}: {line.strip()}",
                        )

    assert not violations, "Story 7 packages must be brand-agnostic. Found brand-conditional in:\n" + "\n".join(
        violations
    )


def test_no_brand_slug_equality_literal():
    """No `brand == "nicolify"` style literal comparisons."""
    violations = []
    for pkg_dir_name, pkg_module_name in STORY7_PACKAGES:
        for path in _get_py_files(pkg_dir_name, pkg_module_name):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if BRAND_SLUG_EQUALITY.search(line):
                    violations.append(
                        f"{pkg_dir_name}/{path.relative_to(CORE_DIR / pkg_dir_name / 'src' / pkg_module_name)}:"
                        f"{lineno}: {line.strip()}",
                    )

    assert not violations, (
        "Story 7 packages must not branch on brand slug literals. "
        "Found brand-slug equality in:\n" + "\n".join(violations)
    )


def test_no_hardcoded_clerk_app_ids():
    """No hardcoded Clerk app IDs in Story 7 source files."""
    violations = []
    for pkg_dir_name, pkg_module_name in STORY7_PACKAGES:
        for path in _get_py_files(pkg_dir_name, pkg_module_name):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if CLERK_APP_ID_PATTERN.search(line):
                    violations.append(
                        f"{pkg_dir_name}/{path.relative_to(CORE_DIR / pkg_dir_name / 'src' / pkg_module_name)}:"
                        f"{lineno}: {line.strip()}",
                    )

    assert not violations, "Story 7 packages must have no hardcoded Clerk app IDs. Found in:\n" + "\n".join(violations)


def test_no_hardcoded_secrets():
    """No hardcoded API_KEY/SECRET/TOKEN literal assignments in Story 7 source files.

    Must reference env / os.getenv / settings.* / similar.
    """
    violations = []
    for pkg_dir_name, pkg_module_name in STORY7_PACKAGES:
        for path in _get_py_files(pkg_dir_name, pkg_module_name):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if HARDCODED_SECRET_PATTERN.search(line):
                    violations.append(
                        f"{pkg_dir_name}/{path.relative_to(CORE_DIR / pkg_dir_name / 'src' / pkg_module_name)}:"
                        f"{lineno}: {line.strip()}",
                    )

    assert not violations, "Story 7 packages must not contain hardcoded secrets. Found in:\n" + "\n".join(violations)
