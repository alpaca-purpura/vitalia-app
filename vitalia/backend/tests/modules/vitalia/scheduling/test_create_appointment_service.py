"""RED tests — CreateAppointmentService: clinic_map persist + audit log + telemetry.

TDD: tests define expected interface BEFORE implementation.
All tests use in-memory mocks — no Postgres required (pure unit tests).

Contract (03-arch A12 + § 5 + hipaa-lite.md + T-BE-4):
- Create persists appointment + clinic_map (A12 brand-local FK)
- clinic_map receives mirror cols: start_time, end_time, status=SCHEDULED (T-BE-4)
- Pre-insert availability check → OutOfWorkingHoursError on OUT_OF_HOURS (T-BE-4)
- IntegrityError pgcode=23P01 → AppointmentOverlapError (T-BE-4, TOCTOU-safe)
- patient_id is REAL (no uuid4 stub) — PHI bug fix (T-BE-4)
- Audit log sync write (HIPAA PHI write = mandatory log)
- Telemetry growth_studio_event emitted (create_appointment)

Per 05-guidelines TDD-mandatory + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------


def _import_service():
    from src.modules.vitalia.scheduling.application.services.create_appointment_service import (  # noqa: PLC0415
        CreateAppointmentService,
    )

    return CreateAppointmentService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
OFFER_ID = uuid4()
PATIENT_ID = uuid4()
DOCTOR_ID = uuid4()
APPT_ID = uuid4()
USER_ID = uuid4()


def _make_create_request() -> dict:
    return {
        "origin": "walk_in",
        "offer_id": OFFER_ID,  # T-BE-4 bugfix: required FK
        "patient_id": PATIENT_ID,
        "doctor_id": DOCTOR_ID,
        "service_label": "Limpieza dental",
        "start_time": datetime(2027, 5, 28, 9, 0, tzinfo=timezone.utc),  # future — past guard (G-round-2)
        "end_time": datetime(2027, 5, 28, 9, 30, tzinfo=timezone.utc),
        "notes_internal": None,
        "currency_override": None,
    }


def _make_mock_scheduling_repo() -> MagicMock:
    """Mock scheduling repo that returns a detail dict after creation."""
    repo = MagicMock()
    detail = {
        "appointment_id": str(APPT_ID),
        "patient_id": str(PATIENT_ID),
        "tenant_id": str(TENANT_ID),
        "clinic_id": str(CLINIC_ID),
        "patient_name_masked": "P. Paciente",
        "dni_masked": "12.***.***",
        "service": "Limpieza dental",
        "doctor_id": str(DOCTOR_ID),
        "start_at": datetime(2026, 5, 28, 9, 0, tzinfo=timezone.utc),
        "end_at": datetime(2026, 5, 28, 9, 30, tzinfo=timezone.utc),
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
    repo.create = AsyncMock(return_value=APPT_ID)
    repo.create_clinic_map = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=detail)
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


class TestCreateAppointmentServiceClinicMap:
    """A12: Create persists clinic_map (brand-local FK)."""

    @pytest.mark.asyncio
    async def test_create_persists_clinic_map(self):
        """create_appointment() must call repo.create_clinic_map() after creating appointment.

        Per 03-arch A12: brand-local clinic_id binding is stored in
        vitalia_appointment_clinic_map, not in the engine appointments table.
        The service MUST persist both: appointment + clinic_map in same transaction.
        """
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            **_make_create_request(),
        )

        # clinic_map must have been persisted
        repo.create_clinic_map.assert_called_once()
        map_kwargs = repo.create_clinic_map.call_args.kwargs
        assert map_kwargs.get("tenant_id") == TENANT_ID
        assert map_kwargs.get("clinic_id") == CLINIC_ID
        assert map_kwargs.get("appointment_id") == APPT_ID or str(map_kwargs.get("appointment_id")) == str(APPT_ID)

    @pytest.mark.asyncio
    async def test_create_returns_appointment_id(self):
        """create_appointment() must return the created appointment detail."""
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        result = await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            **_make_create_request(),
        )

        assert result is not None
        appt_id = result.get("appointment_id")
        assert appt_id is not None


class TestCreateAppointmentServiceAuditLog:
    """Audit log sync write on create."""

    @pytest.mark.asyncio
    async def test_create_emits_audit_log(self):
        """create_appointment() must write audit log row before returning.

        HIPAA-lite mandate: creating a PHI-adjacent record requires audit row.
        """
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            **_make_create_request(),
        )

        audit_writer.write.assert_called_once()
        call_kwargs = audit_writer.write.call_args.kwargs
        assert call_kwargs.get("tenant_id") == TENANT_ID
        assert call_kwargs.get("clinic_id") == CLINIC_ID
        # Action should reference appointment creation
        action = call_kwargs.get("action", "")
        assert "appointment" in action.lower() or "create" in action.lower()


class TestCreateAppointmentServiceTelemetry:
    """Growth studio event emitted on create."""

    @pytest.mark.asyncio
    async def test_create_emits_telemetry_event(self):
        """create_appointment() must emit create_appointment growth_studio_event.

        7 critical telemetry events per 03-arch § 10.
        create_appointment is one of them.
        """
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            **_make_create_request(),
        )

        growth_emitter.emit_event.assert_called_once()
        call_kwargs = growth_emitter.emit_event.call_args.kwargs
        event_type = call_kwargs.get("event_type", "")
        assert "create" in event_type.lower() or "appointment" in event_type.lower()

    @pytest.mark.asyncio
    async def test_telemetry_tenant_and_clinic_passed(self):
        """Growth event must include tenant_id and clinic_id."""
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            **_make_create_request(),
        )

        call_kwargs = growth_emitter.emit_event.call_args.kwargs
        assert call_kwargs.get("tenant_id") == TENANT_ID
        assert call_kwargs.get("clinic_id") == CLINIC_ID


# ---------------------------------------------------------------------------
# T-BE-4: mirror columns, overlap, out-of-hours, real patient_id
# ---------------------------------------------------------------------------


class TestCreateAppointmentServiceMirrorColumns:
    """T-BE-4: clinic_map receives start_time, end_time, status=SCHEDULED."""

    @pytest.mark.asyncio
    async def test_clinic_map_receives_start_time_end_time_status(self):
        """create_clinic_map must be called with start_time, end_time, status=SCHEDULED.

        Per T-BE-4 + migration 050: vitalia_appointment_clinic_map has mirror cols
        start_time/end_time/status to enable the EXCLUDE constraint.
        Without these the constraint never fires (slot never blocked).
        """
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        start = datetime(2027, 6, 22, 9, 0, tzinfo=timezone.utc)
        end = datetime(2027, 6, 22, 9, 30, tzinfo=timezone.utc)

        await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            offer_id=OFFER_ID,
            user_id=USER_ID,
            origin="walk_in",
            patient_id=PATIENT_ID,
            doctor_id=DOCTOR_ID,
            service_label="Limpieza dental",
            start_time=start,
            end_time=end,
        )

        repo.create_clinic_map.assert_called_once()
        kw = repo.create_clinic_map.call_args.kwargs
        assert kw.get("start_time") == start, "start_time must be passed to create_clinic_map"
        assert kw.get("end_time") == end, "end_time must be passed to create_clinic_map"
        assert kw.get("status") == "SCHEDULED", "status must be SCHEDULED on create"


class TestCreateAppointmentServiceOverlap:
    """T-BE-4: IntegrityError 23P01 → AppointmentOverlapError (HTTP 409)."""

    @pytest.mark.asyncio
    async def test_overlap_raises_appointment_overlap_error(self):
        """When repo.create_clinic_map raises IntegrityError pgcode=23P01,
        service must raise AppointmentOverlapError.

        TOCTOU-safe: pre-check is NOT used; DB EXCLUDE constraint is the gate.
        Catches sqlalchemy.exc.IntegrityError with orig.pgcode == '23P01'.
        """
        from src.modules.vitalia.scheduling.domain.exceptions import AppointmentOverlapError  # noqa: PLC0415

        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()

        # Simulate Postgres EXCLUDE violation on clinic_map insert
        pg_error = MagicMock()
        pg_error.pgcode = "23P01"
        repo.create_clinic_map = AsyncMock(side_effect=IntegrityError("EXCLUDE", {}, pg_error))

        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        with pytest.raises(AppointmentOverlapError):
            await service.create_appointment(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                offer_id=OFFER_ID,
                user_id=USER_ID,
                origin="walk_in",
                patient_id=PATIENT_ID,
                doctor_id=DOCTOR_ID,
                service_label="Limpieza dental",
                start_time=datetime(2027, 6, 22, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2027, 6, 22, 9, 30, tzinfo=timezone.utc),
            )

    @pytest.mark.asyncio
    async def test_other_integrity_error_reraises(self):
        """IntegrityError with pgcode != 23P01 must NOT be swallowed."""
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()

        pg_error = MagicMock()
        pg_error.pgcode = "23505"  # unique violation, not EXCLUDE
        repo.create_clinic_map = AsyncMock(side_effect=IntegrityError("UNIQUE", {}, pg_error))

        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        with pytest.raises(IntegrityError):
            await service.create_appointment(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                offer_id=OFFER_ID,
                user_id=USER_ID,
                origin="walk_in",
                patient_id=PATIENT_ID,
                doctor_id=DOCTOR_ID,
                service_label="Limpieza dental",
                start_time=datetime(2027, 6, 22, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2027, 6, 22, 10, 30, tzinfo=timezone.utc),
            )


class TestCreateAppointmentServiceOutOfHours:
    """T-BE-4: Availability check → OutOfWorkingHoursError (HTTP 422)."""

    @pytest.mark.asyncio
    async def test_out_of_hours_raises_before_insert(self):
        """When availability_check_service returns OUT_OF_HOURS,
        service must raise OutOfWorkingHoursError WITHOUT calling repo.create().

        No insert must happen — the check is pre-insert.
        """
        from src.modules.vitalia.scheduling.domain.availability_check import (  # noqa: PLC0415
            AvailabilityCheckResult,
            AvailabilityStatus,
        )
        from src.modules.vitalia.scheduling.domain.exceptions import OutOfWorkingHoursError  # noqa: PLC0415

        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()

        avail_svc = MagicMock()
        avail_svc.check = AsyncMock(
            return_value=AvailabilityCheckResult(
                status=AvailabilityStatus.OUT_OF_HOURS,
                conflict_label=None,
                conflict_start=None,
            )
        )

        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
            availability_check_service=avail_svc,
        )

        with pytest.raises(OutOfWorkingHoursError):
            await service.create_appointment(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                offer_id=OFFER_ID,
                user_id=USER_ID,
                origin="walk_in",
                patient_id=PATIENT_ID,
                doctor_id=DOCTOR_ID,
                service_label="Limpieza dental",
                start_time=datetime(2027, 6, 22, 7, 0, tzinfo=timezone.utc),  # before hours
                end_time=datetime(2027, 6, 22, 7, 30, tzinfo=timezone.utc),
            )

        # No insert should have been called
        repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_availability_check_service_skips_check(self):
        """When availability_check_service=None (default), check is skipped.

        Mateo manual flow doesn't require availability pre-check
        (staff knows the schedule; EXCLUDE handles overlaps).
        """
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()

        # No availability_check_service → default None
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        result = await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            offer_id=OFFER_ID,
            user_id=USER_ID,
            origin="walk_in",
            patient_id=PATIENT_ID,
            doctor_id=DOCTOR_ID,
            service_label="Limpieza dental",
            start_time=datetime(2027, 6, 22, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2027, 6, 22, 9, 30, tzinfo=timezone.utc),
        )

        assert result is not None  # happy path completed
        repo.create.assert_called_once()


class TestCreateAppointmentServiceRealPatientId:
    """T-BE-4: patient_id must be real — no uuid4() stub."""

    @pytest.mark.asyncio
    async def test_real_patient_id_passed_to_repo(self):
        """patient_id supplied by caller must be forwarded to repo.create() as-is.

        PHI bug fix: old code generated uuid4() stub when patient_new_data was set.
        T-BE-5 now handles inline patient creation and provides real patient_id.
        The stub is gone — patient_id is REQUIRED.
        """
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        real_patient_id = uuid4()

        await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            offer_id=OFFER_ID,
            user_id=USER_ID,
            origin="walk_in",
            patient_id=real_patient_id,
            doctor_id=DOCTOR_ID,
            service_label="Limpieza dental",
            start_time=datetime(2027, 6, 22, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2027, 6, 22, 9, 30, tzinfo=timezone.utc),
        )

        repo.create.assert_called_once()
        kw = repo.create.call_args.kwargs
        assert kw.get("patient_id") == real_patient_id, (
            f"Expected real patient_id={real_patient_id}, got {kw.get('patient_id')}"
        )


# ---------------------------------------------------------------------------
# G-round-2: Past appointment guard (server-side authority)
# ---------------------------------------------------------------------------


class TestCreateAppointmentServicePastGuard:
    """G-round-2 regression: start_time in the past → PastAppointmentError (HTTP 422).

    Chris correction: "no debo poder sacar citas para fechas y horas pasadas."
    The guard lives in the service (server-side authority — FE cannot be trusted).
    """

    @pytest.mark.asyncio
    async def test_past_start_time_raises_past_appointment_error(self):
        """start_time strictly in the past → PastAppointmentError; repo.create NOT called.

        RED regression test for G-round-2 guard. Must raise before any DB write.
        """
        from src.modules.vitalia.scheduling.domain.exceptions import PastAppointmentError  # noqa: PLC0415

        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        with pytest.raises(PastAppointmentError):
            await service.create_appointment(
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                offer_id=OFFER_ID,
                user_id=USER_ID,
                origin="walk_in",
                patient_id=PATIENT_ID,
                doctor_id=DOCTOR_ID,
                service_label="Limpieza dental",
                start_time=datetime(2000, 1, 1, 9, 0, tzinfo=timezone.utc),  # clearly past
                end_time=datetime(2000, 1, 1, 9, 30, tzinfo=timezone.utc),
            )

        repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_future_start_time_is_allowed(self):
        """start_time in the future → guard does NOT fire; happy path proceeds.

        Verifies the guard does not over-block valid future appointments (regression guard).
        """
        CreateAppointmentService = _import_service()
        repo = _make_mock_scheduling_repo()
        audit_writer = _make_mock_audit_writer()
        growth_emitter = _make_mock_growth_emitter()
        service = CreateAppointmentService(
            repo=repo,
            audit_writer=audit_writer,
            growth_emitter=growth_emitter,
        )

        result = await service.create_appointment(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            offer_id=OFFER_ID,
            user_id=USER_ID,
            origin="walk_in",
            patient_id=PATIENT_ID,
            doctor_id=DOCTOR_ID,
            service_label="Limpieza dental",
            start_time=datetime(2030, 6, 15, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2030, 6, 15, 10, 30, tzinfo=timezone.utc),
        )

        assert result is not None
        repo.create.assert_called_once()
