"""Architecture gate: admin modules must NOT use raw SQL session.execute(text(...)).

Post vitalia-adopt-luana-core-iam rewrite (story T-be-admin-rewrite):
- admin/modules/tenants.py must use TenantRepository from luana_core_iam
- admin/modules/users.py must use UserRepository from luana_core_iam
- No session.execute(text("SELECT ... FROM vitalia_*")) patterns allowed

This test validates the REWRITE is complete (no phantom SQL residual).

Validator ID: be_arch_no_raw_sql_in_admin (04-validators.yaml)
"""

from __future__ import annotations

import re
from pathlib import Path

WS = Path(__file__).parents[4]  # vitalia/backend/tests/architecture/test_*.py → luana-vitalia/
ADMIN_MODULES_DIR = WS / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "admin" / "modules"

# Pattern: session.execute(text(  — phantom SQL indicator
_RAW_SQL_PATTERNS = [
    r"session\.execute\s*\(\s*text\s*\(",
    r"FROM\s+vitalia_clinics",
    r"FROM\s+vitalia_tenants",
    r"FROM\s+vitalia_user_profiles",
    r"INSERT\s+INTO\s+vitalia_clinics",
    r"INSERT\s+INTO\s+vitalia_tenants",
    r"INSERT\s+INTO\s+vitalia_user_profiles",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _RAW_SQL_PATTERNS]


def _scan_file(path: Path) -> list[tuple[int, str]]:
    """Return list of (lineno, pattern) hits in file (skips docstrings + comments)."""
    hits = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return hits

    # Remove docstrings before scanning (triple-quoted strings used as docs)
    import re  # noqa: PLC0415

    docstring_re = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', re.DOTALL)
    stripped = docstring_re.sub("", content)

    for lineno, line in enumerate(stripped.splitlines(), start=1):
        stripped_line = line.strip()
        if stripped_line.startswith("#"):
            continue
        for pattern in _COMPILED:
            if pattern.search(line):
                hits.append((lineno, f"{pattern.pattern!r} in {path.name}:{lineno}: {line.strip()!r}"))
    return hits


def test_tenants_module_no_raw_sql() -> None:
    """admin/modules/tenants.py must not have raw SQL against phantom tables."""
    target = ADMIN_MODULES_DIR / "tenants.py"
    assert target.exists(), f"Missing file: {target}"
    hits = _scan_file(target)
    assert not hits, (
        "admin/modules/tenants.py still contains phantom raw SQL after rewrite.\n"
        "Run: T-be-admin-rewrite ticket to eliminate phantom code.\n"
        "Hits:\n" + "\n".join(h for _, h in hits)
    )


def test_users_module_no_raw_sql() -> None:
    """admin/modules/users.py must not have raw SQL against phantom tables."""
    target = ADMIN_MODULES_DIR / "users.py"
    assert target.exists(), f"Missing file: {target}"
    hits = _scan_file(target)
    assert not hits, (
        "admin/modules/users.py still contains phantom raw SQL after rewrite.\n"
        "Run: T-be-admin-rewrite ticket to eliminate phantom code.\n"
        "Hits:\n" + "\n".join(h for _, h in hits)
    )


def test_admin_modules_no_phantom_tables() -> None:
    """ALL admin modules must have zero references to phantom tables."""
    all_hits: list[str] = []
    for py_file in ADMIN_MODULES_DIR.glob("*.py"):
        hits = _scan_file(py_file)
        all_hits.extend(h for _, h in hits)

    assert not all_hits, (
        "Admin modules contain phantom table references.\n"
        "These tables do not exist in any migration:\n"
        "  vitalia_clinics, vitalia_tenants, vitalia_user_profiles\n\n"
        "After rewrite, admin must consume engine repos only.\n"
        "Hits:\n" + "\n".join(all_hits)
    )
