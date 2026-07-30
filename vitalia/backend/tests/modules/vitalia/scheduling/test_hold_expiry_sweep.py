# cap: scheduling.mateo-agenda
"""RED tests — HoldExpirySweepService + SchedulingHoldService (SC-10 / V-FN-10).

TDD: tests define expected interface BEFORE implementation.
All tests use in-memory mocks — no Postgres required (pure unit tests).

Contract (03-arch § 7 + 05-guidelines + hipaa-lite.md):
- Sweep lists expired holds → cancels appointment → releases slot → emits activity
- Sweep is idempotent (double-run = no-op for already-processed holds)
- SchedulingHoldService reads TTL from tenant_config (default 30min)
- mark_slot_confirmed called with confirmed=True on create, False on sweep release
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Import helpers (lazy — tests RED until modules exist)
# ---------------------------------------------------------------------------


def _import_sweep_service():
    from src.modules.vitalia.scheduling.application.services.hold_expiry_sweep_service import (  # noqa: PLC0415
        HoldExpirySweepService,
    )

    return HoldExpirySweepService


def _import_hold_service():
    from src.modules.vitalia.scheduling.application.services.scheduling_hold_service import (  # noqa: PLC0415
        SchedulingHoldService,
    )

    return SchedulingHoldService


def _import_hold_port():
    from src.modules.vitalia.scheduling.application.ports.scheduling_hold_port import (  # noqa: PLC0415
        SchedulingHoldPort,
    )

    return SchedulingHoldPort


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
APPT_ID_1 = uuid4()
APPT_ID_2 = uuid4()
SLOT_ID_1 = uuid4()
NOW = datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)


def _make_mock_hold_port(expired_appointments: list | None = None) -> MagicMock:
    """Mock SchedulingHoldPort."""
    port = MagicMock()
    port.mark_slot_confirmed = AsyncMock(return_value=None)
    port.set_hold = AsyncMock(return_value=None)
    port.list_expired_holds = AsyncMock(return_value=expired_appointments if expired_appointments is not None else [])
    return port


def _make_mock_appointment_repo() -> MagicMock:
    """Mock appointment repo for status updates."""
    repo = MagicMock()
    repo.cancel_appointment = AsyncMock(return_value=None)
    repo.get_slot_id_for_appointment = AsyncMock(return_value=SLOT_ID_1)
    return repo


def _make_mock_audit_writer() -> MagicMock:
    writer = MagicMock()
    writer.write = AsyncMock(return_value=None)
    return writer


def _make_mock_activity_emitter() -> MagicMock:
    emitter = MagicMock()
    emitter.emit = AsyncMock(return_value=None)
    return emitter


# ---------------------------------------------------------------------------
# Tests: SchedulingHoldPort (ABC interface)
# ---------------------------------------------------------------------------


class TestSchedulingHoldPortAbstract:
    """SchedulingHoldPort must be abstract (cannot instantiate directly)."""

    def test_port_is_abstract(self):
        """SchedulingHoldPort is an ABC — direct instantiation should fail."""
        SchedulingHoldPort = _import_hold_port()
        with pytest.raises(TypeError):
            SchedulingHoldPort()  # type: ignore[abstract]

    def test_port_has_mark_slot_confirmed(self):
        """Port must declare mark_slot_confirmed abstract method."""
        SchedulingHoldPort = _import_hold_port()
        assert hasattr(SchedulingHoldPort, "mark_slot_confirmed")
        assert getattr(SchedulingHoldPort.mark_slot_confirmed, "__isabstractmethod__", False)

    def test_port_has_set_hold(self):
        """Port must declare set_hold abstract method."""
        SchedulingHoldPort = _import_hold_port()
        assert hasattr(SchedulingHoldPort, "set_hold")
        assert getattr(SchedulingHoldPort.set_hold, "__isabstractmethod__", False)

    def test_port_has_list_expired_holds(self):
        """Port must declare list_expired_holds abstract method."""
        SchedulingHoldPort = _import_hold_port()
        assert hasattr(SchedulingHoldPort, "list_expired_holds")
        assert getattr(SchedulingHoldPort.list_expired_holds, "__isabstractmethod__", False)


# ---------------------------------------------------------------------------
# Tests: HoldExpirySweepService (SC-10 / V-FN-10)
# ---------------------------------------------------------------------------


class TestHoldExpirySweepService:
    """SC-10: Sweep job releases expired holds."""

    @pytest.mark.asyncio
    async def test_sweep_empty_no_ops(self):
        """Sweep with no expired holds = no-op (idempotent baseline)."""
        HoldExpirySweepService = _import_sweep_service()
        port = _make_mock_hold_port(expired_appointments=[])
        appointment_repo = _make_mock_appointment_repo()
        audit_writer = _make_mock_audit_writer()
        activity_emitter = _make_mock_activity_emitter()

        service = HoldExpirySweepService(
            hold_port=port,
            appointment_repo=appointment_repo,
            audit_writer=audit_writer,
            activity_emitter=activity_emitter,
        )

        released = await service.sweep_expired(tenant_id=TENANT_ID, now=NOW)

        assert released == 0
        port.mark_slot_confirmed.assert_not_called()
        appointment_repo.cancel_appointment.assert_not_called()

    @pytest.mark.asyncio
    async def test_sweep_releases_expired_hold(self):
        """Sweep with 1 expired hold: cancel appointment + release slot."""
        HoldExpirySweepService = _import_sweep_service()
        port = _make_mock_hold_port(expired_appointments=[APPT_ID_1])
        appointment_repo = _make_mock_appointment_repo()
        audit_writer = _make_mock_audit_writer()
        activity_emitter = _make_mock_activity_emitter()

        service = HoldExpirySweepService(
            hold_port=port,
            appointment_repo=appointment_repo,
            audit_writer=audit_writer,
            activity_emitter=activity_emitter,
        )

        released = await service.sweep_expired(tenant_id=TENANT_ID, now=NOW)

        assert released == 1
        # Slot released (confirmed=False)
        port.mark_slot_confirmed.assert_called_once()
        mark_kwargs = port.mark_slot_confirmed.call_args.kwargs
        assert mark_kwargs.get("confirmed") is False
        assert mark_kwargs.get("tenant_id") == TENANT_ID

    @pytest.mark.asyncio
    async def test_sweep_cancels_appointment(self):
        """Sweep marks appointment as expired/cancelled."""
        HoldExpirySweepService = _import_sweep_service()
        port = _make_mock_hold_port(expired_appointments=[APPT_ID_1])
        appointment_repo = _make_mock_appointment_repo()
        audit_writer = _make_mock_audit_writer()
        activity_emitter = _make_mock_activity_emitter()

        service = HoldExpirySweepService(
            hold_port=port,
            appointment_repo=appointment_repo,
            audit_writer=audit_writer,
            activity_emitter=activity_emitter,
        )

        await service.sweep_expired(tenant_id=TENANT_ID, now=NOW)

        appointment_repo.cancel_appointment.assert_called_once()
        cancel_kwargs = appointment_repo.cancel_appointment.call_args.kwargs
        assert cancel_kwargs.get("appointment_id") == APPT_ID_1
        assert cancel_kwargs.get("tenant_id") == TENANT_ID

    @pytest.mark.asyncio
    async def test_sweep_emits_activity_event(self):
        """Sweep emits activity event for inbox (glass-box visibility)."""
        HoldExpirySweepService = _import_sweep_service()
        port = _make_mock_hold_port(expired_appointments=[APPT_ID_1])
        appointment_repo = _make_mock_appointment_repo()
        audit_writer = _make_mock_audit_writer()
        activity_emitter = _make_mock_activity_emitter()

        service = HoldExpirySweepService(
            hold_port=port,
            appointment_repo=appointment_repo,
            audit_writer=audit_writer,
            activity_emitter=activity_emitter,
        )

        await service.sweep_expired(tenant_id=TENANT_ID, now=NOW)

        activity_emitter.emit.assert_called_once()
        emit_kwargs = activity_emitter.emit.call_args.kwargs
        # activity event must include tenant_id (no PHI in activity)
        assert emit_kwargs.get("tenant_id") == TENANT_ID

    @pytest.mark.asyncio
    async def test_sweep_multiple_expired_holds(self):
        """Sweep processes multiple expired holds."""
        HoldExpirySweepService = _import_sweep_service()
        port = _make_mock_hold_port(expired_appointments=[APPT_ID_1, APPT_ID_2])
        appointment_repo = _make_mock_appointment_repo()
        audit_writer = _make_mock_audit_writer()
        activity_emitter = _make_mock_activity_emitter()

        service = HoldExpirySweepService(
            hold_port=port,
            appointment_repo=appointment_repo,
            audit_writer=audit_writer,
            activity_emitter=activity_emitter,
        )

        released = await service.sweep_expired(tenant_id=TENANT_ID, now=NOW)

        assert released == 2
        assert port.mark_slot_confirmed.call_count == 2
        assert appointment_repo.cancel_appointment.call_count == 2

    @pytest.mark.asyncio
    async def test_sweep_idempotent_second_run(self):
        """Sweep is idempotent: second run with empty list = 0 released."""
        HoldExpirySweepService = _import_sweep_service()
        # First run: 1 expired
        port = _make_mock_hold_port(expired_appointments=[APPT_ID_1])
        appointment_repo = _make_mock_appointment_repo()
        audit_writer = _make_mock_audit_writer()
        activity_emitter = _make_mock_activity_emitter()

        service = HoldExpirySweepService(
            hold_port=port,
            appointment_repo=appointment_repo,
            audit_writer=audit_writer,
            activity_emitter=activity_emitter,
        )

        first = await service.sweep_expired(tenant_id=TENANT_ID, now=NOW)
        assert first == 1

        # Second run: same NOW but list_expired_holds returns empty (already processed)
        port.list_expired_holds = AsyncMock(return_value=[])
        second = await service.sweep_expired(tenant_id=TENANT_ID, now=NOW)
        assert second == 0


# ---------------------------------------------------------------------------
# Tests: SchedulingHoldService (TTL state machine)
# ---------------------------------------------------------------------------


class TestSchedulingHoldService:
    """SchedulingHoldService: TTL from tenant_config + mark slot + set hold."""

    @pytest.mark.asyncio
    async def test_hold_service_marks_slot_confirmed(self):
        """SchedulingHoldService.book_with_hold calls mark_slot_confirmed(confirmed=True)."""
        SchedulingHoldService = _import_hold_service()
        port = _make_mock_hold_port()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = MagicMock()
        growth_emitter.emit_event = AsyncMock(return_value=None)

        # tenant_config with custom TTL
        tenant_config = {"adrian_hold_ttl_minutes": 45}

        service = SchedulingHoldService(
            hold_port=port,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        appt_id = uuid4()
        await service.book_with_hold(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            appointment_id=appt_id,
            slot_id=SLOT_ID_1,
            tenant_config=tenant_config,
            now=NOW,
        )

        port.mark_slot_confirmed.assert_called_once()
        mark_kwargs = port.mark_slot_confirmed.call_args.kwargs
        assert mark_kwargs.get("confirmed") is True
        assert mark_kwargs.get("slot_id") == SLOT_ID_1
        assert mark_kwargs.get("tenant_id") == TENANT_ID
        assert mark_kwargs.get("clinic_id") == CLINIC_ID

    @pytest.mark.asyncio
    async def test_hold_service_sets_hold_pending_payment(self):
        """SchedulingHoldService.book_with_hold calls set_hold(hold_pending_payment)."""
        SchedulingHoldService = _import_hold_service()
        port = _make_mock_hold_port()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = MagicMock()
        growth_emitter.emit_event = AsyncMock(return_value=None)

        tenant_config = {"adrian_hold_ttl_minutes": 30}

        service = SchedulingHoldService(
            hold_port=port,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        appt_id = uuid4()
        await service.book_with_hold(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            appointment_id=appt_id,
            slot_id=SLOT_ID_1,
            tenant_config=tenant_config,
            now=NOW,
        )

        port.set_hold.assert_called_once()
        hold_kwargs = port.set_hold.call_args.kwargs
        assert hold_kwargs.get("status") == "hold_pending_payment"
        assert hold_kwargs.get("appointment_id") == appt_id
        assert hold_kwargs.get("tenant_id") == TENANT_ID

    @pytest.mark.asyncio
    async def test_hold_service_ttl_from_tenant_config(self):
        """TTL is read from tenant_config.adrian_hold_ttl_minutes, NOT hardcoded."""
        SchedulingHoldService = _import_hold_service()
        port = _make_mock_hold_port()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = MagicMock()
        growth_emitter.emit_event = AsyncMock(return_value=None)

        # Custom TTL = 60 minutes
        tenant_config = {"adrian_hold_ttl_minutes": 60}

        service = SchedulingHoldService(
            hold_port=port,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        appt_id = uuid4()
        await service.book_with_hold(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            appointment_id=appt_id,
            slot_id=SLOT_ID_1,
            tenant_config=tenant_config,
            now=NOW,
        )

        hold_kwargs = port.set_hold.call_args.kwargs
        expected_expiry = NOW + timedelta(minutes=60)
        actual_expiry = hold_kwargs.get("expires_at")
        assert actual_expiry is not None
        # Allow 1 second tolerance
        assert abs((actual_expiry - expected_expiry).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_hold_service_default_ttl_30_minutes(self):
        """Default TTL = 30 minutes when tenant_config missing the key."""
        SchedulingHoldService = _import_hold_service()
        port = _make_mock_hold_port()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = MagicMock()
        growth_emitter.emit_event = AsyncMock(return_value=None)

        # No TTL in config → default 30
        tenant_config: dict = {}

        service = SchedulingHoldService(
            hold_port=port,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        appt_id = uuid4()
        await service.book_with_hold(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            appointment_id=appt_id,
            slot_id=SLOT_ID_1,
            tenant_config=tenant_config,
            now=NOW,
        )

        hold_kwargs = port.set_hold.call_args.kwargs
        expected_expiry = NOW + timedelta(minutes=30)
        actual_expiry = hold_kwargs.get("expires_at")
        assert actual_expiry is not None
        assert abs((actual_expiry - expected_expiry).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_hold_service_emits_audit_log(self):
        """SchedulingHoldService.book_with_hold writes audit log (HIPAA PHI write)."""
        SchedulingHoldService = _import_hold_service()
        port = _make_mock_hold_port()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = MagicMock()
        growth_emitter.emit_event = AsyncMock(return_value=None)

        service = SchedulingHoldService(
            hold_port=port,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        appt_id = uuid4()
        await service.book_with_hold(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            appointment_id=appt_id,
            slot_id=SLOT_ID_1,
            tenant_config={},
            now=NOW,
        )

        audit_writer.write.assert_called_once()
        audit_kwargs = audit_writer.write.call_args.kwargs
        assert audit_kwargs.get("tenant_id") == TENANT_ID
        assert audit_kwargs.get("clinic_id") == CLINIC_ID
        action = audit_kwargs.get("action", "")
        assert "hold" in action.lower() or "appointment" in action.lower()


# ---------------------------------------------------------------------------
# Tests: create_appointment_service slot-marking extension (EXTEND)
# ---------------------------------------------------------------------------


class TestCreateAppointmentServiceSlotMarking:
    """EXTEND: create_appointment now marks the availability slot."""

    @pytest.mark.asyncio
    async def test_create_marks_slot_confirmed_when_hold_service_provided(self):
        """create_appointment with hold_service calls mark_slot_confirmed(True)."""
        from src.modules.vitalia.scheduling.application.services.create_appointment_service import (  # noqa: PLC0415
            CreateAppointmentService,
        )

        SLOT_ID = uuid4()

        repo = MagicMock()
        repo.create = AsyncMock(return_value=APPT_ID_1)
        repo.create_clinic_map = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(
            return_value={
                "appointment_id": str(APPT_ID_1),
                "patient_id": str(uuid4()),
                "tenant_id": str(TENANT_ID),
                "clinic_id": str(CLINIC_ID),
                "patient_name_masked": "P. Paciente",
                "dni_masked": "—",
                "service_label": "Consulta",
                "doctor_id": str(uuid4()),
                "start_at": NOW,
                "end_at": NOW + timedelta(minutes=30),
                "duration_minutes": 30,
                "status": "SCHEDULED",
                "payment_status": "sin_pago",
                "origin": "proactivo_adrian",
                "currency": "PEN",
                "currency_override": None,
                "booking_metadata": {},
                "created_at": NOW,
                "updated_at": None,
                "payments": [],
            }
        )

        audit_writer = MagicMock()
        audit_writer.write = AsyncMock(return_value=None)

        growth_emitter = MagicMock()
        growth_emitter.emit_event = AsyncMock(return_value=None)

        hold_service = MagicMock()
        hold_service.book_with_hold = AsyncMock(return_value=None)

        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
            hold_service=hold_service,
        )

        await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            offer_id=uuid4(),  # T-BE-4: required FK
            user_id=uuid4(),
            origin="proactivo_adrian",
            patient_id=uuid4(),
            doctor_id=uuid4(),
            service_label="Consulta",
            start_time=NOW,
            end_time=NOW + timedelta(minutes=30),
            slot_id=SLOT_ID,
            tenant_config={"adrian_hold_ttl_minutes": 30},
        )

        hold_service.book_with_hold.assert_called_once()
        kwargs = hold_service.book_with_hold.call_args.kwargs
        assert kwargs.get("slot_id") == SLOT_ID
        assert kwargs.get("appointment_id") == APPT_ID_1
        assert kwargs.get("tenant_id") == TENANT_ID

    @pytest.mark.asyncio
    async def test_create_no_slot_marking_when_no_hold_service(self):
        """create_appointment WITHOUT hold_service = backwards-compatible (Mateo manual create)."""
        from src.modules.vitalia.scheduling.application.services.create_appointment_service import (  # noqa: PLC0415
            CreateAppointmentService,
        )

        repo = MagicMock()
        repo.create = AsyncMock(return_value=APPT_ID_1)
        repo.create_clinic_map = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(
            return_value={
                "appointment_id": str(APPT_ID_1),
                "status": "SCHEDULED",
            }
        )

        audit_writer = MagicMock()
        audit_writer.write = AsyncMock(return_value=None)

        growth_emitter = MagicMock()
        growth_emitter.emit_event = AsyncMock(return_value=None)

        # No hold_service (Mateo manual flow)
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
            # hold_service=None  (default)
        )

        # Should NOT raise — backwards compatible
        result = await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            offer_id=uuid4(),  # T-BE-4: required FK
            user_id=uuid4(),
            origin="walk_in",
            patient_id=uuid4(),
            doctor_id=uuid4(),
            service_label="Consulta",
            start_time=NOW,
            end_time=NOW + timedelta(minutes=30),
        )

        assert result is not None
