"""RED tests — AppointmentDetailService: PHI mask + audit log + cross-clinic 404.

TDD: tests define expected interface BEFORE implementation.
All tests use in-memory mocks — no Postgres required (pure unit tests).

Contract (03-arch § 5 + hipaa-lite.md):
- PHI masking applied to detail projection (name + dni + phone + email)
- Audit log sync write before returning response
- Cross-clinic appointment returns None → service raises 404

Per 05-guidelines TDD-mandatory + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------


def _import_service():
    from src.modules.vitalia.scheduling.application.services.appointment_detail_service import (  # noqa: PLC0415
        AppointmentDetailService,
    )

    return AppointmentDetailService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
OTHER_CLINIC_ID = uuid4()
APPT_ID = uuid4()
PATIENT_ID = uuid4()
USER_ID = uuid4()


def _make_detail_dict(clinic_id=None) -> dict:
    return {
        "appointment_id": str(APPT_ID),
        "patient_id": str(PATIENT_ID),
        "tenant_id": str(TENANT_ID),
        "clinic_id": str(clinic_id or CLINIC_ID),
        "patient_name_masked": "P. Hernández",
        "dni_masked": "12.***.***",
        "service": "Control mensual",
        "doctor_id": str(uuid4()),
        "start_at": datetime(2026, 5, 27, 9, 0, tzinfo=timezone.utc),
        "end_at": datetime(2026, 5, 27, 9, 30, tzinfo=timezone.utc),
        "duration_minutes": 30,
        "status": "SCHEDULED",
        "payment_status": "sin_pago",
        "origin": "walk_in",
        "currency": "PEN",
        "currency_override": None,
        "booking_metadata": {},
        "created_at": datetime(2026, 5, 26, tzinfo=timezone.utc),
        "updated_at": None,
        "payments": [],
    }


def _make_mock_repo(detail: dict | None = "DEFAULT") -> MagicMock:
    repo = MagicMock()
    if detail == "DEFAULT":
        detail = _make_detail_dict()
    repo.get_by_id = AsyncMock(return_value=detail)
    return repo


def _make_mock_audit_writer() -> MagicMock:
    writer = MagicMock()
    writer.write = AsyncMock(return_value=None)
    return writer


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAppointmentDetailServicePhiMask:
    """A1: PHI masking applied to detail projection."""

    @pytest.mark.asyncio
    async def test_phi_mask_applied_to_response(self):
        """get_detail() must return PHI-masked patient fields.

        The detail DTO must contain masked name/dni — never raw PHI.
        The repo already returns masked values (masking applied at SQL layer),
        but the service must validate/ensure the masked fields are present.
        """
        AppointmentDetailService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        service = AppointmentDetailService(repo=repo, audit_writer=audit_writer)

        result = await service.get_detail(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
        )

        assert result is not None
        # Name must be masked (initial + surname)
        patient_name = result.get("patient_name_masked", "")
        assert "." in patient_name or len(patient_name.split()) <= 2

        # DNI must be masked if present
        dni = result.get("dni_masked", "")
        if dni:
            assert "***" in dni or "*" in dni

    @pytest.mark.asyncio
    async def test_phi_mask_raw_name_not_exposed(self):
        """Service must not pass a raw patient_name field through unmasked."""
        AppointmentDetailService = _import_service()
        raw_detail = _make_detail_dict()
        raw_detail["patient_name_masked"] = "P. Hernández"  # already masked by repo
        # Inject raw name to verify service doesn't re-expose it
        raw_detail["raw_patient_name"] = "Pedro Hernández"

        repo = _make_mock_repo(raw_detail)
        audit_writer = _make_mock_audit_writer()
        service = AppointmentDetailService(repo=repo, audit_writer=audit_writer)

        result = await service.get_detail(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
        )

        # Raw name should not leak into response
        assert result is not None
        assert "raw_patient_name" not in result or result.get("raw_patient_name") is None


class TestAppointmentDetailServiceAuditLog:
    """A2: Audit log sync write before response."""

    @pytest.mark.asyncio
    async def test_audit_log_sync_write(self):
        """get_detail() must write audit log row before returning.

        HIPAA-lite mandate: every PHI read must log synchronously.
        """
        AppointmentDetailService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        service = AppointmentDetailService(repo=repo, audit_writer=audit_writer)

        await service.get_detail(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
        )

        audit_writer.write.assert_called_once()
        call_kwargs = audit_writer.write.call_args.kwargs
        assert call_kwargs.get("tenant_id") == TENANT_ID
        assert call_kwargs.get("clinic_id") == CLINIC_ID
        assert call_kwargs.get("resource_id") == APPT_ID

    @pytest.mark.asyncio
    async def test_audit_log_action_is_read(self):
        """Audit log action must identify this as a PHI read event."""
        AppointmentDetailService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        service = AppointmentDetailService(repo=repo, audit_writer=audit_writer)

        await service.get_detail(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
        )

        call_kwargs = audit_writer.write.call_args.kwargs
        action = call_kwargs.get("action", "")
        # Action must reference appointment read
        assert "appointment" in action.lower() or "read" in action.lower() or "detail" in action.lower()


class TestAppointmentDetailServiceCrossClinic:
    """A3: Cross-clinic returns 404 (not data leak)."""

    @pytest.mark.asyncio
    async def test_cross_clinic_returns_404(self):
        """get_detail() must raise 404 when appointment not found (cross-clinic).

        Repo returns None for cross-clinic (dual filter rejects). Service
        must raise AppointmentNotFoundError which maps to HTTP 404.
        """
        AppointmentDetailService = _import_service()
        # Repo returns None for cross-clinic query
        repo = _make_mock_repo(detail=None)
        audit_writer = _make_mock_audit_writer()
        service = AppointmentDetailService(repo=repo, audit_writer=audit_writer)

        from src.modules.vitalia.scheduling.domain.exceptions import AppointmentNotFoundError  # noqa: PLC0415

        with pytest.raises(AppointmentNotFoundError):
            await service.get_detail(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=OTHER_CLINIC_ID,
                user_id=USER_ID,
            )

    @pytest.mark.asyncio
    async def test_cross_clinic_still_writes_suspicious_audit_log(self):
        """Even on cross-clinic 404, the audit writer is still called.

        The attempt to access cross-clinic PHI should be logged (suspicious access).
        """
        AppointmentDetailService = _import_service()
        repo = _make_mock_repo(detail=None)
        audit_writer = _make_mock_audit_writer()
        service = AppointmentDetailService(repo=repo, audit_writer=audit_writer)

        from src.modules.vitalia.scheduling.domain.exceptions import AppointmentNotFoundError  # noqa: PLC0415

        with pytest.raises(AppointmentNotFoundError):
            await service.get_detail(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=OTHER_CLINIC_ID,
                user_id=USER_ID,
            )

        # Audit must be written even on not-found
        audit_writer.write.assert_called_once()
