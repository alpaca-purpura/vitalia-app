"""Architecture gate: admin modules MUST import from luana_core_iam engine repos.

Post vitalia-adopt-luana-core-iam rewrite:
- tenants.py must import TenantRepository from luana_core_iam
- users.py must import UserRepository from luana_core_iam
- Neither module may import sanitize_phi_payload from compliance_service_adapter
  (that was the phantom compliance adapter — replaced by write_audit_log_sync)

Validator ID: be_arch_admin_consumes_engine_repos (04-validators.yaml)
"""

from __future__ import annotations

import re
from pathlib import Path

WS = Path(__file__).parents[4]  # → luana-vitalia/
ADMIN_MODULES_DIR = WS / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "admin" / "modules"

# Must be present: engine repo imports
_REQUIRED_IN_TENANTS = [
    r"luana_core_iam.*TenantRepository|TenantRepository.*luana_core_iam",
]
_REQUIRED_IN_USERS = [
    r"luana_core_iam.*UserRepository|UserRepository.*luana_core_iam",
]

# Must NOT be present: phantom compliance adapter
_FORBIDDEN_PATTERNS = [
    r"compliance_service_adapter",
    r"sanitize_phi_payload",
    r"vitalia_user_profiles",
    r"vitalia_tenants\b",  # not vitalia_tenants_columns (migration name OK)
    r"vitalia_clinics",
]
_FORBIDDEN_RE = [re.compile(p, re.IGNORECASE) for p in _FORBIDDEN_PATTERNS]


def _file_content(name: str) -> str:
    path = ADMIN_MODULES_DIR / name
    assert path.exists(), f"Missing: {path}"
    return path.read_text(encoding="utf-8")


def test_tenants_imports_engine_repo() -> None:
    """admin/modules/tenants.py must import TenantRepository from luana_core_iam."""
    content = _file_content("tenants.py")
    found = any(re.search(p, content) for p in _REQUIRED_IN_TENANTS)
    assert found, (
        "admin/modules/tenants.py is missing import of TenantRepository from luana_core_iam.\n"
        "Required: from luana_core_iam.infrastructure.repositories.tenant_repository import TenantRepository"
    )


def test_users_imports_engine_repo() -> None:
    """admin/modules/users.py must import UserRepository from luana_core_iam."""
    content = _file_content("users.py")
    found = any(re.search(p, content) for p in _REQUIRED_IN_USERS)
    assert found, (
        "admin/modules/users.py is missing import of UserRepository from luana_core_iam.\n"
        "Required: from luana_core_iam.infrastructure.repositories.user_repository import UserRepository"
    )


_DOCSTRING_RE = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', re.DOTALL)


def _strip_docstrings(content: str) -> str:
    """Remove triple-quoted docstrings from source content before scanning."""
    return _DOCSTRING_RE.sub("", content)


def test_admin_modules_no_phantom_compliance_adapter() -> None:
    """Admin modules must NOT import from compliance_service_adapter (phantom).

    Docstrings are excluded from scanning: they may cite phantom table names
    as documentation context (e.g. "NO raw SQL to phantom tables (vitalia_clinics, vitalia_tenants)").
    Only runtime code is scanned for forbidden patterns.
    """
    for py_file in ADMIN_MODULES_DIR.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        # Strip docstrings before scanning — they may reference phantom names as docs
        code_only = _strip_docstrings(content)
        for pattern in _FORBIDDEN_RE:
            assert not pattern.search(code_only), (
                f"Phantom reference found in {py_file.name}:\n"
                f"  Pattern: {pattern.pattern!r}\n"
                f"After rewrite admin must use:\n"
                f"  from src.modules.vitalia.audit.audit_writer import write_audit_log_sync\n"
                f"  from luana_core_iam.infrastructure.repositories import ..."
            )
