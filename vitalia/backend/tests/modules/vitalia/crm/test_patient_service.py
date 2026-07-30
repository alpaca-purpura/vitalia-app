"""Tests for PatientService — RBAC decorator + opt-out flow.

TDD: RED tests defined before implementation (T-infra-9).

downstream-regression-na: brand-local CRM patient service tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia._shared.auth.rbac import PHIAccessDeniedError
from src.modules.vitalia.crm.application.services.patient_service import PatientService


class TestPatientServiceRbac:
    """PatientService methods enforce RBAC via @require_phi_access."""

    def _make_service(self) -> PatientService:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_patient_repo = AsyncMock()
        mock_audit_repo = AsyncMock()
        return PatientService(
            patient_repo=mock_patient_repo,
            audit_repo=mock_audit_repo,
        )

    @pytest.mark.asyncio
    async def test_get_patient_blocked_for_marketing_role(self) -> None:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_repo = AsyncMock()
        mock_audit = AsyncMock()
        service = PatientService(patient_repo=mock_repo, audit_repo=mock_audit)

        with pytest.raises(PHIAccessDeniedError):
            await service.get_by_id(
                patient_id=uuid4(),
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="marketing",
            )

    @pytest.mark.asyncio
    async def test_get_patient_blocked_for_receptionist_role(self) -> None:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_repo = AsyncMock()
        mock_audit = AsyncMock()
        service = PatientService(patient_repo=mock_repo, audit_repo=mock_audit)

        with pytest.raises(PHIAccessDeniedError):
            await service.get_by_id(
                patient_id=uuid4(),
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="receptionist",
            )

    @pytest.mark.asyncio
    async def test_get_patient_allowed_for_doctor(self) -> None:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None  # patient not found — OK for RBAC test
        mock_audit = AsyncMock()
        service = PatientService(patient_repo=mock_repo, audit_repo=mock_audit)

        # Should NOT raise PHIAccessDeniedError for doctor role
        result = await service.get_by_id(
            patient_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="doctor",
        )
        assert result is None  # not found

    @pytest.mark.asyncio
    async def test_update_blocked_for_marketing_role(self) -> None:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_repo = AsyncMock()
        mock_audit = AsyncMock()
        service = PatientService(patient_repo=mock_repo, audit_repo=mock_audit)

        with pytest.raises(PHIAccessDeniedError):
            await service.update(
                patient_id=uuid4(),
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="marketing",
                updates={},
            )


class TestPatientServiceOptOut:
    """PatientService opt_out sets marketing_opt_out_at."""

    @pytest.mark.asyncio
    async def test_opt_out_allowed_for_admin_clinic(self) -> None:
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_repo = AsyncMock()
        mock_repo.opt_out.return_value = None
        mock_audit = AsyncMock()
        service = PatientService(patient_repo=mock_repo, audit_repo=mock_audit)

        # Should not raise for admin_clinic
        await service.opt_out(
            patient_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="admin_clinic",
            reason="Patient requested removal",
        )
        mock_repo.opt_out.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_opt_out_blocked_for_patient_role(self) -> None:
        """Patient role cannot self-serve opt-out via this endpoint."""
        from src.modules.vitalia.crm.application.services.patient_service import (
            PatientService,
        )

        mock_repo = AsyncMock()
        mock_audit = AsyncMock()
        service = PatientService(patient_repo=mock_repo, audit_repo=mock_audit)

        with pytest.raises(PHIAccessDeniedError):
            await service.opt_out(
                patient_id=uuid4(),
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="patient",
                reason="self",
            )
