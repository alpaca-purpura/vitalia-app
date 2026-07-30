# cap: clinics.lisa.doctores
"""DoctorRepository unit tests — dual-filter enforcement (non-integration).

Tests that DoctorRepository inherits PhiRepositoryBase and validates dual filter.
Does NOT require a DB connection — validates contract only.
"""

from __future__ import annotations

import pytest


def test_doctor_repository_inherits_compound_scope_repository_base() -> None:
    """DoctorRepository must inherit CompoundScopeRepositoryBase (engine — post lift 2026-05-20).

    Arch gate: test_compound_scope_repository_used.py requires new PHI repos to use engine base.
    See vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo.
    """
    from luana_core_platform.repositories.compound_scope_repository import (
        CompoundScopeRepositoryBase,
    )

    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
        DoctorRepository,
    )

    assert issubclass(DoctorRepository, CompoundScopeRepositoryBase), (
        "DoctorRepository must inherit CompoundScopeRepositoryBase (engine) for HIPAA dual-filter. "
        "Post engine lift 2026-05-20 — new PHI repos must use engine base, not brand-local. "
        "See vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo."
    )


def test_doctor_repository_validates_dual_filter() -> None:
    """validate_dual_filter raises MissingClinicFilterError when clinic_id is None."""
    from unittest.mock import MagicMock
    from uuid import uuid4

    from src.modules.vitalia._shared.repositories.phi_repository import (
        MissingClinicFilterError,
    )
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
        DoctorRepository,
    )

    mock_session = MagicMock()
    mock_kek = MagicMock()
    repo = DoctorRepository(session=mock_session, kek=mock_kek)

    with pytest.raises(MissingClinicFilterError):
        repo.validate_dual_filter(tenant_id=uuid4(), clinic_id=None)


def test_doctor_repository_validates_tenant_id() -> None:
    """validate_dual_filter raises ValueError when tenant_id is None."""
    from unittest.mock import MagicMock
    from uuid import uuid4

    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
        DoctorRepository,
    )

    mock_session = MagicMock()
    mock_kek = MagicMock()
    repo = DoctorRepository(session=mock_session, kek=mock_kek)

    with pytest.raises(ValueError, match="tenant_id"):
        repo.validate_dual_filter(tenant_id=None, clinic_id=uuid4())


def test_dni_hash_is_deterministic() -> None:
    """compute_dni_hash must return same hash for same input and KEK."""
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
        compute_dni_hash,
    )

    kek = "0" * 64  # 32 bytes hex
    h1 = compute_dni_hash("12345678", kek)
    h2 = compute_dni_hash("12345678", kek)
    assert h1 == h2
    assert isinstance(h1, str)
    assert len(h1) == 64  # SHA-256 hex digest


def test_dni_hash_is_different_for_different_values() -> None:
    """compute_dni_hash for different DNIs must produce different hashes."""
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
        compute_dni_hash,
    )

    kek = "0" * 64
    h1 = compute_dni_hash("12345678", kek)
    h2 = compute_dni_hash("87654321", kek)
    assert h1 != h2
