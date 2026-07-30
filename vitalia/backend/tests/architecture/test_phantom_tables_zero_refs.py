"""Architecture gate: zero references to phantom tables across ALL source files.

Phantom tables (never existed in migrations):
  - vitalia_clinics    (replaced by vitalia_clinic_branches in 023_vitalia_clinics)
  - vitalia_tenants    (tenant data lives in engine 'tenants' table via 022)
  - vitalia_user_profiles  (user data lives in engine 'users' table via 022)

This gate validates SC-13 from 04-validators.yaml: grep must return 0 hits.

Validator ID: phantom_code_zero_grep + be_arch_phantom_tables_zero_refs
"""

from __future__ import annotations

import re
from pathlib import Path

WS = Path(__file__).parents[4]  # → luana-vitalia/
SRC_DIR = WS / "vitalia" / "backend" / "src"
TESTS_DIR = WS / "vitalia" / "backend" / "tests"

# Phantom tables that must NOT appear in src/ (migrations may reference in comments)
_PHANTOM_TABLE_PATTERNS = [
    r"\bvitalia_clinics\b",
    r"\bvitalia_tenants\b",
    r"\bvitalia_user_profiles\b",
]
_COMPILED = [re.compile(p) for p in _PHANTOM_TABLE_PATTERNS]

# Paths to exclude from scan: migration files are allowed to have these in
# comments as documentation; architecture tests themselves reference them.
_EXCLUDE_SUFFIXES = (".pyc",)
_EXCLUDE_FILES = {"test_phantom_tables_zero_refs.py"}  # self-reference OK

# Strip docstrings before scanning so documentation mentions of phantom names
# (e.g. "No raw SQL to phantom tables (vitalia_clinics, vitalia_tenants)") don't
# trigger false positives. Only runtime code paths are checked.
_DOCSTRING_RE = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', re.DOTALL)


def _strip_docstrings(content: str) -> str:
    """Remove triple-quoted docstrings from Python source before scanning."""
    return _DOCSTRING_RE.sub("", content)


def _scan_directory(root: Path) -> list[str]:
    """Scan Python files in root for phantom table references (docstrings excluded)."""
    hits = []
    for py_file in root.rglob("*.py"):
        if py_file.name in _EXCLUDE_FILES:
            continue
        if any(py_file.suffix == s for s in _EXCLUDE_SUFFIXES):
            continue
        # Allow migration files (alembic/versions/), only check src/modules/
        if "alembic" in py_file.parts:
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        # Strip docstrings — they may document phantom names as context, not code
        code_only = _strip_docstrings(content)
        for lineno, line in enumerate(code_only.splitlines(), start=1):
            # Skip comment lines (inline comments still checked)
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in _COMPILED:
                if pattern.search(line):
                    hits.append(f"{py_file.relative_to(WS)}:{lineno}: {line.strip()!r}")
    return hits


def test_no_phantom_vitalia_clinics_in_src() -> None:
    """src/ must not reference phantom table vitalia_clinics."""
    hits = [h for h in _scan_directory(SRC_DIR) if "vitalia_clinics" in h]
    assert not hits, (
        "Found references to phantom table 'vitalia_clinics' in src/.\n"
        "Clinic data lives in 'vitalia_clinic_branches' (migration 023).\n"
        "Tenant data lives in engine 'tenants' table (migration 022).\n"
        "Hits:\n" + "\n".join(hits)
    )


def test_no_phantom_vitalia_tenants_in_src() -> None:
    """src/ must not reference phantom table vitalia_tenants."""
    hits = [h for h in _scan_directory(SRC_DIR) if "vitalia_tenants" in h]
    assert not hits, (
        "Found references to phantom table 'vitalia_tenants' in src/.\n"
        "Tenant data lives in engine 'tenants' table consumed via TenantRepository.\n"
        "Hits:\n" + "\n".join(hits)
    )


def test_no_phantom_vitalia_user_profiles_in_src() -> None:
    """src/ must not reference phantom table vitalia_user_profiles."""
    hits = [h for h in _scan_directory(SRC_DIR) if "vitalia_user_profiles" in h]
    assert not hits, (
        "Found references to phantom table 'vitalia_user_profiles' in src/.\n"
        "User data lives in engine 'users' table consumed via UserRepository.\n"
        "Hits:\n" + "\n".join(hits)
    )
