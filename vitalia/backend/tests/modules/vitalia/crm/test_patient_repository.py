"""Tests for PatientRepository — dual filter enforcement + audit row.

TDD: RED tests defined before implementation (T-infra-9).

Uses unit-level mocking (no live DB). Integration-marked tests are skipped
when Postgres is not available (per T-infra-9 acceptance criteria).

downstream-regression-na: brand-local CRM patient repo tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia._shared.repositories.phi_repository import (
    MissingClinicFilterError,
    PhiRepositoryBase,
)


class TestPatientRepositoryInheritance:
    """PatientRepository must subclass PhiRepositoryBase."""

    def test_patient_repository_is_phi_repository(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        assert issubclass(PatientRepository, PhiRepositoryBase)

    def test_patient_repository_implements_get_by_id(self) -> None:
        import inspect

        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        assert hasattr(PatientRepository, "get_by_id")
        assert inspect.iscoroutinefunction(PatientRepository.get_by_id)

    def test_patient_repository_implements_list_by_filter(self) -> None:
        import inspect

        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        assert hasattr(PatientRepository, "list_by_filter")
        assert inspect.iscoroutinefunction(PatientRepository.list_by_filter)


class TestPatientRepositoryDualFilter:
    """PatientRepository enforces tenant_id + clinic_id dual filter."""

    def test_validate_dual_filter_called_on_get(self) -> None:
        """get_by_id must call validate_dual_filter (provided by PhiRepositoryBase)."""
        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        mock_session = AsyncMock()
        mock_audit = AsyncMock()
        repo = PatientRepository(session=mock_session, audit_repo=mock_audit)

        # validate_dual_filter raises MissingClinicFilterError when clinic_id is None
        with pytest.raises(MissingClinicFilterError):
            import asyncio

            # asyncio.run (no get_event_loop): py3.12 RuntimeError sin loop corriente
            asyncio.run(
                repo.get_by_id(entity_id=uuid4(), tenant_id=uuid4(), clinic_id=None)  # type: ignore[arg-type]
            )

    def test_validate_dual_filter_raises_when_tenant_id_missing(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        mock_session = AsyncMock()
        mock_audit = AsyncMock()
        repo = PatientRepository(session=mock_session, audit_repo=mock_audit)

        with pytest.raises(ValueError, match="tenant_id"):
            import asyncio

            # asyncio.run (no get_event_loop): py3.12 RuntimeError sin loop corriente
            asyncio.run(
                repo.get_by_id(entity_id=uuid4(), tenant_id=None, clinic_id=uuid4())  # type: ignore[arg-type]
            )


class TestPatientRepositoryAudit:
    """PatientRepository writes audit log row on PHI access."""

    def test_audit_repo_is_accepted_in_constructor(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        mock_session = AsyncMock()
        mock_audit = AsyncMock()
        repo = PatientRepository(session=mock_session, audit_repo=mock_audit)
        assert repo._audit_repo is mock_audit

    def test_opt_out_method_exists_and_is_async(self) -> None:
        import inspect

        from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
            PatientRepository,
        )

        assert hasattr(PatientRepository, "opt_out")
        assert inspect.iscoroutinefunction(PatientRepository.opt_out)
