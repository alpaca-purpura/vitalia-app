"""RED tests — AppointmentStatusService: status transition + audit log + telemetry event.

TDD: tests define expected interface BEFORE implementation.
All tests use in-memory mocks — no Postgres required (pure unit tests).

Contract (03-arch § 5 + hipaa-lite.md):
- Status transitions: CONFIRMED → PENDING|CANCELLED|NO_SHOW|COMPLETED
- Audit log sync write with from_status → to_status fields
- Growth studio event emitted on status change

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
    from src.modules.vitalia.scheduling.application.services.appointment_status_service import (  # noqa: PLC0415
        AppointmentStatusService,
    )

    return AppointmentStatusService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
APPT_ID = uuid4()
USER_ID = uuid4()


def _make_detail_dict(status: str = "SCHEDULED") -> dict:
    return {
        "appointment_id": str(APPT_ID),
        "patient_id": str(uuid4()),
        "tenant_id": str(TENANT_ID),
        "clinic_id": str(CLINIC_ID),
        "patient_name_masked": "P. Hernández",
        "dni_masked": "12.***.***",
        "service": "Control mensual",
        "doctor_id": str(uuid4()),
        "start_at": datetime(2026, 5, 27, 9, 0, tzinfo=timezone.utc),
        "end_at": datetime(2026, 5, 27, 9, 30, tzinfo=timezone.utc),
        "duration_minutes": 30,
        "status": status,
        "payment_status": "sin_pago",
        "origin": "walk_in",
        "currency": "PEN",
        "currency_override": None,
        "booking_metadata": {},
        "created_at": datetime(2026, 5, 26, tzinfo=timezone.utc),
        "updated_at": None,
        "payments": [],
    }


def _make_mock_repo(initial_detail: dict | None = None) -> MagicMock:
    repo = MagicMock()
    if initial_detail is None:
        initial_detail = _make_detail_dict("SCHEDULED")
    repo.get_by_id = AsyncMock(return_value=initial_detail)
    repo.update_status = AsyncMock(return_value={**initial_detail, "status": "CANCELLED"})
    # T-BE-4: clinic_map mirror propagation (always set up so existing tests don't TypeError)
    repo.update_clinic_map_status = AsyncMock(return_value=None)
    return repo


def _make_mock_audit_writer() -> MagicMock:
    writer = MagicMock()
    writer.write = AsyncMock(return_value=None)
    return writer


def _make_mock_growth_emitter() -> MagicMock:
    emitter = MagicMock()
    emitter.emit_event = AsyncMock(return_value=None)
    return emitter


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAppointmentStatusServiceAuditLog:
    """Audit log must include from_status + to_status fields."""

    @pytest.mark.asyncio
    async def test_status_change_emits_audit_log_with_from_to(self):
        """change_status() must write audit log with from_status + to_status.

        HIPAA-lite mandate: status change is a PHI-adjacent mutation.
        Audit log must capture the transition (from_status → to_status).
        """
        AppointmentStatusService = _import_service()
        repo = _make_mock_repo(_make_detail_dict("SCHEDULED"))
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = AppointmentStatusService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.change_status(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            new_status="CANCELLED",
            reason="Paciente canceló",
            user_id=USER_ID,
        )

        audit_writer.write.assert_called_once()
        call_kwargs = audit_writer.write.call_args.kwargs
        assert call_kwargs.get("tenant_id") == TENANT_ID
        assert call_kwargs.get("clinic_id") == CLINIC_ID
        # Payload must contain from/to status
        payload = call_kwargs.get("payload", {})
        assert "from_status" in payload or "from" in str(payload)
        assert "to_status" in payload or "to" in str(payload) or "CANCELLED" in str(payload)

    @pytest.mark.asyncio
    async def test_audit_log_action_is_status_change(self):
        """Audit action must identify this as a status_change event."""
        AppointmentStatusService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = AppointmentStatusService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.change_status(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            new_status="NO_SHOW",
            reason=None,
            user_id=USER_ID,
        )

        call_kwargs = audit_writer.write.call_args.kwargs
        action = call_kwargs.get("action", "")
        assert "status" in action.lower() or "appointment" in action.lower()


class TestAppointmentStatusServiceTelemetry:
    """Growth studio event emitted on status change."""

    @pytest.mark.asyncio
    async def test_status_change_emits_growth_studio_event(self):
        """change_status() must emit a growth_studio_event after audit log write.

        Telemetry is fire-forget (not mandatory sync like audit_log) but MUST
        be called on every status change for funnel analytics.
        """
        AppointmentStatusService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = AppointmentStatusService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.change_status(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            new_status="COMPLETED",
            reason=None,
            user_id=USER_ID,
        )

        growth_emitter.emit_event.assert_called_once()
        call_kwargs = growth_emitter.emit_event.call_args.kwargs
        # Event must reference appointment status change
        event_type = call_kwargs.get("event_type", "")
        assert (
            "appointment" in event_type.lower() or "status" in event_type.lower() or "completed" in event_type.lower()
        )

    @pytest.mark.asyncio
    async def test_growth_event_entity_id_is_appointment(self):
        """Growth studio event entity_id must reference the appointment."""
        AppointmentStatusService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = AppointmentStatusService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.change_status(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            new_status="CANCELLED",
            reason=None,
            user_id=USER_ID,
        )

        call_kwargs = growth_emitter.emit_event.call_args.kwargs
        entity_id = call_kwargs.get("entity_id")
        assert entity_id == APPT_ID or str(entity_id) == str(APPT_ID)


class TestAppointmentStatusServiceCrossClinic:
    """Cross-clinic status change returns 404."""

    @pytest.mark.asyncio
    async def test_cross_clinic_returns_404(self):
        """change_status() on cross-clinic appointment must raise AppointmentNotFoundError."""
        AppointmentStatusService = _import_service()
        # Repo returns None → appointment not in this clinic
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = AppointmentStatusService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        from src.modules.vitalia.scheduling.domain.exceptions import AppointmentNotFoundError  # noqa: PLC0415

        OTHER_CLINIC = uuid4()
        with pytest.raises(AppointmentNotFoundError):
            await service.change_status(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=OTHER_CLINIC,
                new_status="CANCELLED",
                reason=None,
                user_id=USER_ID,
            )


# ---------------------------------------------------------------------------
# T-BE-4: clinic_map status mirror propagation
# ---------------------------------------------------------------------------


class TestAppointmentStatusServiceClinicMapMirror:
    """T-BE-4: change_status must propagate status to clinic_map mirror."""

    @pytest.mark.asyncio
    async def test_cancel_updates_clinic_map_status_mirror(self):
        """change_status(CANCELLED) must call repo.update_clinic_map_status().

        When a CANCELLED appointment frees its slot, the clinic_map mirror
        status must also be set to CANCELLED so the EXCLUDE constraint
        (WHERE status <> 'CANCELLED') allows re-booking of that slot.
        """
        AppointmentStatusService = _import_service()
        repo = _make_mock_repo(_make_detail_dict("SCHEDULED"))
        repo.update_clinic_map_status = AsyncMock(return_value=None)
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = AppointmentStatusService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.change_status(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            new_status="CANCELLED",
            reason="Paciente canceló",
            user_id=USER_ID,
        )

        repo.update_clinic_map_status.assert_called_once()
        kw = repo.update_clinic_map_status.call_args.kwargs
        assert kw.get("new_status") == "CANCELLED"
        assert kw.get("tenant_id") == TENANT_ID
        assert kw.get("clinic_id") == CLINIC_ID

    @pytest.mark.asyncio
    async def test_complete_updates_clinic_map_status_mirror(self):
        """change_status(COMPLETED) must also propagate to clinic_map mirror."""
        AppointmentStatusService = _import_service()
        repo = _make_mock_repo(_make_detail_dict("SCHEDULED"))
        repo.update_clinic_map_status = AsyncMock(return_value=None)
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = AppointmentStatusService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.change_status(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            new_status="COMPLETED",
            reason=None,
            user_id=USER_ID,
        )

        repo.update_clinic_map_status.assert_called_once()
        kw = repo.update_clinic_map_status.call_args.kwargs
        assert kw.get("new_status") == "COMPLETED"
