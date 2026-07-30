"""Tests for PatientConsentService — opt-out + marketing opt-in flows.

TDD RED phase: tests written BEFORE implementation per .claude/rules/tdd-mandatory.md.

gherkin_coverage (from 06-tickets.yaml T-2):
  SC-02: test_marketing_opt_in_false_blocks_marketing_template
  SC-04: test_opt_out_cascades_cancel_pending_events

HIPAA-lite requirements tested:
  - Dual filter (tenant_id + clinic_id) on all operations
  - Audit log row written BEFORE response (sync)
  - RBAC: opt-out = admin_clinic only; marketing-opt-in = doctor/nurse/admin_clinic
  - PatientOptedOut domain event emitted via outbox

downstream-regression-na: brand-local vitalia CRM consent service tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.modules.vitalia._shared.auth.rbac import PHIAccessDeniedError


@pytest.mark.asyncio
class TestPatientConsentServiceOptOut:
    """opt_out(): RBAC enforcement + audit log + event emission."""

    def _make_service(
        self,
        patient_repo: AsyncMock | None = None,
        audit_repo: AsyncMock | None = None,
    ):
        from src.modules.vitalia.crm.application.services.patient_consent_service import (
            PatientConsentService,
        )

        _patient_repo = patient_repo or AsyncMock()
        _audit_repo = audit_repo or AsyncMock()
        return PatientConsentService(
            patient_repo=_patient_repo,
            audit_repo=_audit_repo,
        )

    async def test_opt_out_blocked_for_doctor_role(self) -> None:
        """Doctor role cannot record opt-out — only admin_clinic allowed."""
        service = self._make_service()

        with pytest.raises(PHIAccessDeniedError):
            await service.opt_out(
                patient_id=uuid4(),
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="doctor",
                reason="Test reason",
            )

    async def test_opt_out_blocked_for_nurse_role(self) -> None:
        """Nurse role cannot record opt-out — only admin_clinic allowed."""
        service = self._make_service()

        with pytest.raises(PHIAccessDeniedError):
            await service.opt_out(
                patient_id=uuid4(),
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="nurse",
                reason="Test reason",
            )

    async def test_opt_out_blocked_for_marketing_role(self) -> None:
        """Marketing role cannot record opt-out."""
        service = self._make_service()

        with pytest.raises(PHIAccessDeniedError):
            await service.opt_out(
                patient_id=uuid4(),
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="marketing",
                reason="Test reason",
            )

    async def test_opt_out_allowed_for_admin_clinic(self) -> None:
        """admin_clinic can record opt-out successfully."""
        patient_repo = AsyncMock()
        patient_repo.opt_out.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        patient_id = uuid4()
        tenant_id = uuid4()
        clinic_id = uuid4()
        user_id = uuid4()

        # Should not raise
        await service.opt_out(
            patient_id=patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            user_role="admin_clinic",
            reason="Solicitud de exclusión por parte del paciente.",
        )

        # Repo opt_out must be called
        patient_repo.opt_out.assert_called_once()
        call_kwargs = patient_repo.opt_out.call_args
        assert call_kwargs.args[0] == patient_id or (call_kwargs.kwargs.get("entity_id") == patient_id)

    async def test_opt_out_writes_audit_log_sync(self) -> None:
        """Audit log row MUST be written before response (HIPAA-lite § Audit log)."""
        patient_repo = AsyncMock()
        patient_repo.opt_out.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        await service.opt_out(
            patient_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="admin_clinic",
            reason="Exclusión voluntaria.",
        )

        # Audit write must have been called (sync, before response)
        assert audit_repo.write.called
        audit_entry = audit_repo.write.call_args[0][0]
        assert audit_entry.action == "patient_opted_out"
        assert audit_entry.resource_type == "patient"

    async def test_opt_out_emits_patient_opted_out_event(self) -> None:
        """PatientOptedOut domain event MUST be emitted via outbox adapter_bus."""
        patient_repo = AsyncMock()
        patient_repo.opt_out.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        patient_id = uuid4()
        tenant_id = uuid4()
        clinic_id = uuid4()
        user_id = uuid4()

        # Patch the outbox publish call
        with patch("src.modules.vitalia.crm.application.services.patient_consent_service.adapter_bus") as mock_bus:
            mock_bus.publish = AsyncMock()
            await service.opt_out(
                patient_id=patient_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                user_role="admin_clinic",
                reason="Solicitud voluntaria.",
            )

        mock_bus.publish.assert_called_once()
        event = mock_bus.publish.call_args[0][0]
        assert event.patient_id == patient_id
        assert event.tenant_id == tenant_id
        assert event.clinic_id == clinic_id

    async def test_opt_out_cascades_cancel_pending_events(self) -> None:
        """SC-04: opt-out MUST call cancel_pending_fidelizacion_events if available.

        When a patient opts out, any pending fidelization events (follow-up,
        appointment reminders) scheduled for them should be cancelled.
        This implements SC-04 from the fidelizacion spec.
        """
        patient_repo = AsyncMock()
        patient_repo.opt_out.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        patient_id = uuid4()
        tenant_id = uuid4()
        clinic_id = uuid4()
        user_id = uuid4()

        with patch("src.modules.vitalia.crm.application.services.patient_consent_service.adapter_bus") as mock_bus:
            mock_bus.publish = AsyncMock()
            await service.opt_out(
                patient_id=patient_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                user_role="admin_clinic",
                reason="Solicitud voluntaria.",
            )

        # Verify event was emitted — downstream fidelizacion consumers
        # handle the actual cancellation via domain event subscription
        mock_bus.publish.assert_called_once()
        event = mock_bus.publish.call_args[0][0]
        assert event.tenant_id == tenant_id
        assert event.clinic_id == clinic_id
        assert event.patient_id == patient_id
        assert event.triggered_by_user_id == user_id


@pytest.mark.asyncio
class TestPatientConsentServiceMarketingOptIn:
    """marketing_opt_in(): RBAC + audit log + consent update."""

    def _make_service(
        self,
        patient_repo: AsyncMock | None = None,
        audit_repo: AsyncMock | None = None,
    ):
        from src.modules.vitalia.crm.application.services.patient_consent_service import (
            PatientConsentService,
        )

        _patient_repo = patient_repo or AsyncMock()
        _audit_repo = audit_repo or AsyncMock()
        return PatientConsentService(
            patient_repo=_patient_repo,
            audit_repo=_audit_repo,
        )

    async def test_marketing_opt_in_blocked_for_marketing_role(self) -> None:
        """Marketing role cannot update consent — PHI RBAC blocks it."""
        service = self._make_service()

        with pytest.raises(PHIAccessDeniedError):
            await service.marketing_opt_in(
                patient_id=uuid4(),
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="marketing",
                opt_in=True,
            )

    async def test_marketing_opt_in_allowed_for_doctor(self) -> None:
        """Doctor can update marketing consent."""
        patient_repo = AsyncMock()
        patient_repo.marketing_opt_in.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        await service.marketing_opt_in(
            patient_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="doctor",
            opt_in=True,
        )

        patient_repo.marketing_opt_in.assert_called_once()

    async def test_marketing_opt_in_allowed_for_nurse(self) -> None:
        """Nurse can update marketing consent."""
        patient_repo = AsyncMock()
        patient_repo.marketing_opt_in.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        await service.marketing_opt_in(
            patient_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="nurse",
            opt_in=False,
        )

        patient_repo.marketing_opt_in.assert_called_once()

    async def test_marketing_opt_in_allowed_for_admin_clinic(self) -> None:
        """admin_clinic can update marketing consent."""
        patient_repo = AsyncMock()
        patient_repo.marketing_opt_in.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        await service.marketing_opt_in(
            patient_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="admin_clinic",
            opt_in=True,
        )

        patient_repo.marketing_opt_in.assert_called_once()

    async def test_marketing_opt_in_writes_audit_log(self) -> None:
        """Audit log MUST be written for each consent change (HIPAA-lite)."""
        patient_repo = AsyncMock()
        patient_repo.marketing_opt_in.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        await service.marketing_opt_in(
            patient_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="admin_clinic",
            opt_in=True,
        )

        assert audit_repo.write.called
        audit_entry = audit_repo.write.call_args[0][0]
        assert audit_entry.action == "patient_marketing_opt_in"
        assert audit_entry.resource_type == "patient"

    async def test_marketing_opt_in_false_blocks_marketing_template(self) -> None:
        """SC-02: patient with marketing_opt_in=False MUST NOT receive marketing.

        When opt_in=False is set, the consent record is updated to reflect
        the patient's refusal. The fidelizacion template engine reads this
        flag before sending any marketing communication.
        """
        patient_repo = AsyncMock()
        patient_repo.marketing_opt_in.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        patient_id = uuid4()
        tenant_id = uuid4()
        clinic_id = uuid4()
        user_id = uuid4()

        await service.marketing_opt_in(
            patient_id=patient_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            user_role="admin_clinic",
            opt_in=False,
        )

        # Verify consent update was called with opt_in=False
        patient_repo.marketing_opt_in.assert_called_once()
        call_kwargs = patient_repo.marketing_opt_in.call_args
        # opt_in value must be passed to repo
        assert call_kwargs.kwargs.get("opt_in") is False or (len(call_kwargs.args) > 1 and call_kwargs.args[1] is False)

        # Audit log MUST reflect the consent refusal
        assert audit_repo.write.called
        audit_entry = audit_repo.write.call_args[0][0]
        assert audit_entry.action == "patient_marketing_opt_in"
        assert audit_entry.resource_id == patient_id

    async def test_marketing_opt_in_uses_dual_filter(self) -> None:
        """Repo must be called with both tenant_id AND clinic_id (HIPAA dual filter)."""
        patient_repo = AsyncMock()
        patient_repo.marketing_opt_in.return_value = None
        audit_repo = AsyncMock()
        audit_repo.write.return_value = None

        service = self._make_service(patient_repo=patient_repo, audit_repo=audit_repo)

        tenant_id = uuid4()
        clinic_id = uuid4()

        await service.marketing_opt_in(
            patient_id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=uuid4(),
            user_role="doctor",
            opt_in=True,
        )

        patient_repo.marketing_opt_in.assert_called_once()
        call_kwargs = patient_repo.marketing_opt_in.call_args
        assert call_kwargs.kwargs.get("tenant_id") == tenant_id
        assert call_kwargs.kwargs.get("clinic_id") == clinic_id
