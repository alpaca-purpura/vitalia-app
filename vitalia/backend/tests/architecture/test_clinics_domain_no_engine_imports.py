"""Architecture gate: vitalia/clinics/domain/ must be pure Python (no engine imports).

DDD Inside-Out rule: domain layer is the innermost ring — ZERO framework imports.
- No sqlalchemy imports
- No luana_core_iam imports (domain does not know about infra)
- No fastapi imports
- Only: pydantic, uuid, datetime, enum, dataclasses, and vitalia domain-local imports

Validator ID: be_arch_clinics_domain_no_engine_imports (04-validators.yaml)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WS = Path(__file__).parents[4]  # → luana-vitalia/
CLINICS_DOMAIN = WS / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "clinics" / "domain"

_FORBIDDEN_IMPORTS = [
    r"^from sqlalchemy",
    r"^import sqlalchemy",
    r"^from luana_core_iam",
    r"^import luana_core_iam",
    r"^from fastapi",
    r"^import fastapi",
    r"^from alembic",
    r"^import alembic",
    r"^from luana_core_platform\.core\.database",
    r"^from luana_core_platform\.persistence",
]
_COMPILED = [re.compile(p, re.MULTILINE) for p in _FORBIDDEN_IMPORTS]


def test_clinics_domain_dir_exists() -> None:
    """vitalia/clinics/domain/ must exist."""
    assert CLINICS_DOMAIN.exists(), (
        f"Clinics domain directory missing: {CLINICS_DOMAIN}\n"
        "Run T-be-clinics-extension ticket to scaffold the DDD module."
    )


def test_clinics_domain_no_framework_imports() -> None:
    """Domain files must be pure Python (no sqlalchemy/iam/fastapi)."""
    if not CLINICS_DOMAIN.exists():
        pytest.skip("Clinics domain not yet created (pending T-be-clinics-extension)")

    violations: list[str] = []
    for py_file in CLINICS_DOMAIN.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in _COMPILED:
            for match in pattern.finditer(content):
                lineno = content[: match.start()].count("\n") + 1
                violations.append(f"{py_file.relative_to(WS)}:{lineno}: {match.group().strip()!r}")

    assert not violations, (
        "Domain layer must be pure Python (DDD Inside-Out).\n"
        "No framework imports allowed in domain/.\n"
        "Violations:\n" + "\n".join(violations)
    )
