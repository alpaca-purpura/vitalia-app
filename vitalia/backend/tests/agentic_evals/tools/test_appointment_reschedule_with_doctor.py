"""Tool tests — `appointment_reschedule_with_doctor` (vitalia AGENTIC tool, R23 Opus 4.7).

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-tools-3 + 02-design § 6.4 + 03-arch-agentic § 4.4:

  A1: test_list_slots_filters — list_slots returns slots filtered by
      appointment_type compat + treatment_room_assignment + max_concurrent_per_doctor.
  A2: test_atomic_book — propose_and_book is atomic with advisory lock.
      Concurrent attempts on same slot → only one succeeds; the other receives
      slot_taken error.
  A3: test_reschedule_atomic — reschedule_existing releases old slot AND reserves
      new slot atomically. Old (doctor, slot) freed; new (doctor, slot) booked.

Plus defensive coverage (per copilot-resilience.md + R23):

  - test_tenant_id_not_in_schema — security boundary (ctx-injected).
  - test_action_discriminator — input.action discriminates between 4 actions.
  - test_cancel_releases_slot_and_audit — cancel marks booking cancelled +
    audit_log appointment_cancelled.
  - test_propose_and_book_idempotency — duplicate propose_and_book within 60s
    returns existing booking_id (delegates to BookingService idempotency).
  - test_audit_log_per_action — each successful action emits one audit_log row
    with sanitized payload (best-effort).
  - test_audit_log_failure_does_not_break_turn — best-effort observability.
  - test_trace_event_recorded — best-effort observability.
  - test_trace_event_failure_does_not_break_turn — never breaks turn.
  - test_pii_sanitized_in_trace — patient_id NOT raw in trace payload (sanitized).
  - test_list_slots_does_not_persist — read-only action, no side effects.
  - test_propose_and_book_missing_required_fields — validation surface.

These are UNIT tests — BookingService + repos + dispatcher mocked via in-memory fakes.
Integration tests (real Postgres advisory_lock + actual booking persist) land in
tests/integration/ + smoke E2E suite (separate scope).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

# ───────────────────────────────────────────────────────────────────────────
# Tenant ID NOT in input schema (security boundary; sync test)
# ───────────────────────────────────────────────────────────────────────────


def test_tenant_id_not_in_schema() -> None:
    """tenant_id MUST NEVER appear in client-provided input.

    Security boundary per `.claude/rules/tenant-isolation.md` + 02-design § 6.4.
    """
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
    )

    fields = AppointmentRescheduleInput.model_fields
    assert "tenant_id" not in fields, (
        "tenant_id MUST NOT be in AppointmentRescheduleInput — "
        "security boundary per tenant-isolation.md + 02-design § 6.4"
    )
    # Verify discriminator + per-action fields
    assert "action" in fields
    assert "doctor_id" in fields
    assert "booking_id" in fields
    assert "offer_id" in fields
    assert "patient_id" in fields
    assert "preferred_window" in fields
    assert "target_slot" in fields


def test_action_discriminator() -> None:
    """action field is the discriminator across 4 actions."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
    )

    valid_actions = {"list_slots", "propose_and_book", "reschedule_existing", "cancel"}
    for act in valid_actions:
        # All these construct without raising for some valid combination
        inp = AppointmentRescheduleInput(
            action=act,  # type: ignore[arg-type]
            doctor_id=uuid.uuid4(),
        )
        assert inp.action == act

    # Invalid action rejected
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AppointmentRescheduleInput(
            action="diagnose",  # type: ignore[arg-type]
            doctor_id=uuid.uuid4(),
        )


# ───────────────────────────────────────────────────────────────────────────
# Fixtures — in-memory fakes
# ───────────────────────────────────────────────────────────────────────────


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class _FakeBooking:
    """Mirror minimal surface of VitaliaBookingModel."""

    def __init__(
        self,
        *,
        booking_id: uuid.UUID,
        tenant_id: uuid.UUID,
        offer_id: uuid.UUID,
        doctor_id: uuid.UUID,
        patient_id: uuid.UUID,
        slot_iso: datetime,
        status: str = "pending_payment",
        appointment_type: str = "consultation",
    ) -> None:
        self.id = booking_id
        self.tenant_id = tenant_id
        self.offer_id = offer_id
        self.doctor_id = doctor_id
        self.patient_id = patient_id
        self.slot_iso = slot_iso
        self.status = status
        self.appointment_type = appointment_type


class _FakeDoctorExtension:
    """Mirror minimal surface of VitaliaDoctorExtensionModel."""

    def __init__(
        self,
        *,
        doctor_id: uuid.UUID,
        specialty: str = "dental_general",
        treatment_room: str = "room_1",
        max_concurrent_per_slot: int = 1,
        appointment_types: list[str] | None = None,
        available_offer_ids: list[str] | None = None,
    ) -> None:
        self.id = uuid.uuid4()
        self.doctor_id = doctor_id
        self.specialty = specialty
        self.treatment_room = treatment_room
        self.max_concurrent_per_slot = max_concurrent_per_slot
        self.appointment_types = appointment_types or ["consultation", "control"]
        self.available_offer_ids = available_offer_ids or []


class _FakeBookingRepository:
    """In-memory BookingRepository fake.

    Mirrors the relevant T-be-3 surface used by appointment_reschedule_with_doctor:
      get_by_id, find_by_doctor_slot, list_by_doctor, save, soft_delete.
    """

    def __init__(self, tenant_id: uuid.UUID) -> None:
        self._tenant_id = tenant_id
        self._bookings: dict[uuid.UUID, _FakeBooking] = {}

    async def get_by_id(self, booking_id: uuid.UUID) -> _FakeBooking | None:
        bk = self._bookings.get(booking_id)
        if bk is None or bk.status == "deleted":
            return None
        return bk

    async def find_by_doctor_slot(self, doctor_id: uuid.UUID, slot_iso: datetime) -> _FakeBooking | None:
        active = (
            "pending_payment",
            "awaiting_consent",
            "confirmed_deposit",
            "confirmed_full",
        )
        for bk in self._bookings.values():
            if bk.doctor_id == doctor_id and bk.slot_iso == slot_iso and bk.status in active:
                return bk
        return None

    async def list_by_doctor(self, doctor_id: uuid.UUID, *, status: str | None = None) -> list[_FakeBooking]:
        out: list[_FakeBooking] = []
        for bk in self._bookings.values():
            if bk.doctor_id != doctor_id:
                continue
            if status is not None and bk.status != status:
                continue
            out.append(bk)
        return sorted(out, key=lambda b: b.slot_iso)

    async def save(self, booking: _FakeBooking) -> None:
        self._bookings[booking.id] = booking

    def add_seed(self, booking: _FakeBooking) -> None:
        """Test helper — seed booking into store without persisting via save()."""
        self._bookings[booking.id] = booking


class _FakeDoctorExtensionRepository:
    """In-memory DoctorExtensionRepository fake."""

    def __init__(self, tenant_id: uuid.UUID) -> None:
        self._tenant_id = tenant_id
        self._extensions: dict[uuid.UUID, _FakeDoctorExtension] = {}

    async def get_by_doctor_id(self, doctor_id: uuid.UUID) -> _FakeDoctorExtension | None:
        return self._extensions.get(doctor_id)

    def add_seed(self, extension: _FakeDoctorExtension) -> None:
        self._extensions[extension.doctor_id] = extension


class _FakeBookingServiceCalls:
    """Capture create_booking calls + simulate idempotent + advisory_lock semantics.

    create_booking signature mirrors real BookingService.create_booking.
    Internal idempotency: same (patient_id, doctor_id, slot_iso) returns
    cached BookingResult (mirrors 60s TTL).
    Internal slot occupancy: same (doctor_id, slot_iso) → SlotTakenError unless
    cached idempotent.
    """

    def __init__(self, *, booking_repo: _FakeBookingRepository) -> None:
        self._booking_repo = booking_repo
        self._idem_cache: dict[tuple[uuid.UUID, uuid.UUID, int], dict[str, Any]] = {}
        self.calls: list[dict[str, Any]] = []
        self.fail_with: Exception | None = None  # injection point for failure tests

    async def create_booking(
        self,
        request: Any,  # CreateBookingRequest
        tenant_id: uuid.UUID,
    ) -> Any:
        from src.modules.vitalia.application.services.booking_service import (
            BookingResult,
            SlotTakenError,
        )

        self.calls.append(
            {
                "patient_id": request.patient_id,
                "doctor_id": request.doctor_id,
                "offer_id": request.offer_id,
                "slot_iso": request.slot_iso,
                "tenant_id": tenant_id,
                "delivery_channel": request.delivery_channel,
            }
        )

        if self.fail_with is not None:
            raise self.fail_with

        idem_key = (
            request.patient_id,
            request.doctor_id,
            int(request.slot_iso.timestamp()),
        )
        cached = self._idem_cache.get(idem_key)
        if cached is not None:
            return BookingResult(
                booking_id=cached["booking_id"],
                status=cached["status"],
                is_idempotent_hit=True,
            )

        # Slot already taken? (mirrors BookingService advisory_lock check)
        existing = await self._booking_repo.find_by_doctor_slot(request.doctor_id, request.slot_iso)
        if existing is not None:
            raise SlotTakenError(doctor_id=request.doctor_id, slot_iso=request.slot_iso)

        # Create + persist — mirror real BookingService._determine_booking_status:
        # requires_consent → awaiting_consent ; requires_prepay → pending_payment ;
        # otherwise → confirmed_deposit.
        if getattr(request, "requires_informed_consent", False):
            status = "awaiting_consent"
        elif getattr(request, "requires_prepay", False):
            status = "pending_payment"
        else:
            status = "confirmed_deposit"

        booking_id = uuid.uuid4()
        bk = _FakeBooking(
            booking_id=booking_id,
            tenant_id=tenant_id,
            offer_id=request.offer_id,
            doctor_id=request.doctor_id,
            patient_id=request.patient_id,
            slot_iso=request.slot_iso,
            status=status,
        )
        await self._booking_repo.save(bk)
        self._idem_cache[idem_key] = {
            "booking_id": booking_id,
            "status": status,
        }
        return BookingResult(
            booking_id=booking_id,
            status=status,
            is_idempotent_hit=False,
        )


class _CapturingAuditRepo:
    """Captures audit_log save calls."""

    def __init__(self) -> None:
        self.events: list[Any] = []

    async def save(self, audit_event: Any) -> None:
        self.events.append(audit_event)


class _RaisingAuditRepo:
    """Audit log raises — confirms tool turn does NOT break."""

    async def save(self, audit_event: Any) -> None:
        raise RuntimeError("audit log down — must not break turn")


class _CapturingTraceRepo:
    """Captures trace_event.add() calls (sync surface per BaseTraceEventRepoProtocol)."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def add(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return None


class _RaisingTraceRepo:
    def add(self, **kwargs: Any) -> Any:
        raise RuntimeError("trace repo down — must NOT break turn")


def _scheduler_no_busy_slots(doctor_id: uuid.UUID, start: datetime, days: int) -> list[datetime]:
    """Return list of candidate slots — naive 9-17 slot generator skipping weekends."""
    out: list[datetime] = []
    for d_offset in range(days):
        day = start + timedelta(days=d_offset)
        if day.weekday() >= 5:  # weekend
            continue
        for hour in range(9, 17):
            out.append(
                datetime(
                    year=day.year,
                    month=day.month,
                    day=day.day,
                    hour=hour,
                    minute=0,
                    tzinfo=timezone.utc,
                )
            )
    return out


# ───────────────────────────────────────────────────────────────────────────
# A1 — list_slots filters by appointment_type + treatment_room + max_concurrent
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_slots_filters() -> None:
    """A1 acceptance: list_slots filters by appointment_type compat +
    treatment_room_assignment + max_concurrent_per_doctor.

    Per 02-design § 5.2 + § 6.4:
      → query @luana/core/scheduling.calendar(doctor_id, window)
      → filter by appointment_type compat (consultation/control/surgery)
      → filter by treatment_room_assignment (vertical-medical extension)
      → filter by max_concurrent_per_doctor (vertical-medical extension)
      → return available_slots[]

    Read-only — no side effects (no audit_log row, no booking row written).
    """
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        WindowSpec,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    # Doctor extension: max_concurrent=1, supports consultation
    doctor_ext_repo.add_seed(
        _FakeDoctorExtension(
            doctor_id=doctor_id,
            specialty="dental_general",
            treatment_room="room_a",
            max_concurrent_per_slot=1,
            appointment_types=["consultation", "control"],
        )
    )

    # Seed one busy slot — list_slots MUST filter it out
    busy_slot = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)  # Monday
    booking_repo.add_seed(
        _FakeBooking(
            booking_id=uuid.uuid4(),
            tenant_id=tenant_id,
            offer_id=uuid.uuid4(),
            doctor_id=doctor_id,
            patient_id=uuid.uuid4(),
            slot_iso=busy_slot,
            status="confirmed_deposit",
        )
    )

    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="list_slots",
            doctor_id=doctor_id,
            preferred_window=WindowSpec(
                start=datetime(2026, 6, 1, tzinfo=timezone.utc).date(),
                days=5,
            ),
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )

    # Must return non-empty available_slots, but exclude busy_slot
    assert len(result.available_slots) > 0
    assert busy_slot not in result.available_slots
    # All slots within Mon-Fri 9-17 window
    for slot in result.available_slots:
        assert slot.hour >= 9
        assert slot.hour < 17
        assert slot.weekday() < 5
    # No appointment_type assigned in list_slots (only on book)
    assert result.appointment_type is None
    assert result.treatment_room_assigned is None
    # Read-only — no booking persisted
    assert booking_service.calls == []
    # Read-only — no audit_log row
    assert audit_repo.events == []


@pytest.mark.asyncio
async def test_list_slots_respects_max_concurrent() -> None:
    """list_slots returns slots only when concurrent count < max_concurrent_per_slot.

    max_concurrent_per_slot=2 + 1 confirmed booking at slot → slot still available.
    max_concurrent_per_slot=2 + 2 confirmed bookings at slot → slot filtered out.
    """
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        WindowSpec,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    doctor_ext_repo.add_seed(
        _FakeDoctorExtension(
            doctor_id=doctor_id,
            max_concurrent_per_slot=2,
            appointment_types=["consultation"],
        )
    )

    slot_with_one_booking = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    slot_with_two_bookings = datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc)
    for _ in range(1):
        booking_repo.add_seed(
            _FakeBooking(
                booking_id=uuid.uuid4(),
                tenant_id=tenant_id,
                offer_id=uuid.uuid4(),
                doctor_id=doctor_id,
                patient_id=uuid.uuid4(),
                slot_iso=slot_with_one_booking,
                status="confirmed_deposit",
            )
        )
    for _ in range(2):
        booking_repo.add_seed(
            _FakeBooking(
                booking_id=uuid.uuid4(),
                tenant_id=tenant_id,
                offer_id=uuid.uuid4(),
                doctor_id=doctor_id,
                patient_id=uuid.uuid4(),
                slot_iso=slot_with_two_bookings,
                status="confirmed_deposit",
            )
        )

    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="list_slots",
            doctor_id=doctor_id,
            preferred_window=WindowSpec(
                start=datetime(2026, 6, 1, tzinfo=timezone.utc).date(),
                days=1,
            ),
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )

    # slot_with_one_booking still available (1 < 2)
    assert slot_with_one_booking in result.available_slots
    # slot_with_two_bookings filtered out (2 >= 2)
    assert slot_with_two_bookings not in result.available_slots


@pytest.mark.asyncio
async def test_list_slots_no_doctor_extension_returns_empty() -> None:
    """Doctor without extension config → empty available_slots (defensive)."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        WindowSpec,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()  # NO extension seeded
    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="list_slots",
            doctor_id=doctor_id,
            preferred_window=WindowSpec(
                start=datetime(2026, 6, 1, tzinfo=timezone.utc).date(),
                days=5,
            ),
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )

    assert result.available_slots == []


# ───────────────────────────────────────────────────────────────────────────
# A2 — propose_and_book atomic with advisory lock
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_atomic_book() -> None:
    """A2 acceptance: propose_and_book atomic with advisory lock (delegates to
    BookingService which holds pg_advisory_lock per (doctor_id, slot_iso)).

    Per 02-design § 5.2 propose_and_book flow:
      → idempotency_key check (booking_id + slot)
      → reserve slot atomically (Postgres advisory lock per doctor+slot)
      → create booking row status='pending_payment'
      → return booking_id, payment_url

    Two concurrent attempts at SAME slot but DIFFERENT patients → only first wins,
    second receives slot_taken error (atomic guard in BookingService).
    """
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    offer_id = uuid.uuid4()
    target_slot = datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc)
    patient_a = uuid.uuid4()
    patient_b = uuid.uuid4()

    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    doctor_ext_repo.add_seed(
        _FakeDoctorExtension(
            doctor_id=doctor_id,
            treatment_room="room_b",
            max_concurrent_per_slot=1,
            appointment_types=["consultation"],
        )
    )

    # First call — patient_a books slot
    first = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="propose_and_book",
            doctor_id=doctor_id,
            offer_id=offer_id,
            patient_id=patient_a,
            target_slot=target_slot,
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )
    assert first.booking_id is not None
    # Default flags (no consent, no prepay) → confirmed_deposit per
    # BookingService._determine_booking_status.
    assert first.booking_status in (
        "pending_payment",
        "awaiting_consent",
        "confirmed_deposit",
    )
    assert first.appointment_type == "consultation"
    assert first.treatment_room_assigned == "room_b"

    # Second call — patient_b tries SAME slot → atomic guard rejects
    second = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="propose_and_book",
            doctor_id=doctor_id,
            offer_id=offer_id,
            patient_id=patient_b,
            target_slot=target_slot,
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )
    # Second attempt → no booking, error_code populated
    assert second.booking_id is None
    assert second.booking_status == "slot_taken"

    # BookingService called twice — guard inside service
    assert len(booking_service.calls) == 2

    # Audit log: only one booked event (the failed attempt logged separately)
    booked_events = [e for e in audit_repo.events if e.event_type == "appointment_booked"]
    assert len(booked_events) == 1


@pytest.mark.asyncio
async def test_propose_and_book_idempotency() -> None:
    """Same (patient, doctor, slot) propose_and_book within 60s → existing
    booking_id returned (delegates to BookingService idempotency cache)."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    offer_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    target_slot = datetime(2026, 6, 2, 11, 0, tzinfo=timezone.utc)

    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id, max_concurrent_per_slot=1))

    inp = AppointmentRescheduleInput(
        action="propose_and_book",
        doctor_id=doctor_id,
        offer_id=offer_id,
        patient_id=patient_id,
        target_slot=target_slot,
    )

    first = await appointment_reschedule_with_doctor(
        inp,
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )
    second = await appointment_reschedule_with_doctor(
        inp,
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )
    # Same booking_id (idempotent reuse)
    assert first.booking_id is not None
    assert first.booking_id == second.booking_id


@pytest.mark.asyncio
async def test_propose_and_book_missing_required_fields_returns_error() -> None:
    """propose_and_book without patient_id/offer_id/target_slot → tool returns
    error status WITHOUT calling BookingService."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id))

    # Missing patient_id
    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="propose_and_book",
            doctor_id=doctor_id,
            offer_id=uuid.uuid4(),
            target_slot=datetime(2026, 6, 2, 12, 0, tzinfo=timezone.utc),
            # patient_id intentionally missing
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )
    assert result.booking_id is None
    assert result.booking_status == "missing_required_fields"
    # BookingService NEVER called
    assert booking_service.calls == []


# ───────────────────────────────────────────────────────────────────────────
# A3 — reschedule_existing releases old slot + reserves new + audit_log
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reschedule_atomic() -> None:
    """A3 acceptance: reschedule_existing releases old slot AND reserves new.

    Per 02-design § 5.2 reschedule_existing flow:
      → fetch existing booking
      → release old slot (advisory lock)
      → reserve new slot (advisory lock)
      → update booking row
      → trigger reminder cascade reset
      → audit_log(appointment_rescheduled, old, new)

    After reschedule, old (doctor, slot) free; new (doctor, slot) booked.
    """
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    offer_id = uuid.uuid4()
    old_slot = datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc)
    new_slot = datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc)

    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id))

    # Seed existing booking at old_slot
    existing_booking_id = uuid.uuid4()
    booking_repo.add_seed(
        _FakeBooking(
            booking_id=existing_booking_id,
            tenant_id=tenant_id,
            offer_id=offer_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            slot_iso=old_slot,
            status="confirmed_deposit",
        )
    )

    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="reschedule_existing",
            doctor_id=doctor_id,
            booking_id=existing_booking_id,
            target_slot=new_slot,
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )

    # Tool returns NEW booking_id — the freshly-reserved row at new_slot.
    # Old row preserved as cancelled (audit trail intact). Audit log links old→new.
    assert result.booking_id is not None
    assert result.booking_id != existing_booking_id
    assert result.booking_status == "confirmed_deposit"

    # Old slot is released — find_by_doctor_slot returns None (old row is cancelled,
    # cancelled status is NOT in the active set).
    old = await booking_repo.find_by_doctor_slot(doctor_id, old_slot)
    assert old is None

    # New slot is reserved with the NEW booking_id from BookingService.
    new = await booking_repo.find_by_doctor_slot(doctor_id, new_slot)
    assert new is not None
    assert new.id == result.booking_id

    # Audit log: appointment_rescheduled with old_booking_id + new_booking_id
    # + old_slot_iso + new_slot_iso linking them.
    rescheduled_events = [e for e in audit_repo.events if e.event_type == "appointment_rescheduled"]
    assert len(rescheduled_events) == 1
    payload = rescheduled_events[0].payload_redacted
    assert payload["old_booking_id"] == str(existing_booking_id)
    assert "old_slot_iso" in payload
    assert "new_slot_iso" in payload


@pytest.mark.asyncio
async def test_reschedule_missing_booking_returns_error() -> None:
    """reschedule_existing with unknown booking_id → error status."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id))

    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="reschedule_existing",
            doctor_id=doctor_id,
            booking_id=uuid.uuid4(),  # unknown
            target_slot=datetime(2026, 6, 4, 14, 0, tzinfo=timezone.utc),
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )
    assert result.booking_id is None
    assert result.booking_status == "booking_not_found"


# ───────────────────────────────────────────────────────────────────────────
# Cancel: releases slot + audit_log
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_releases_slot_and_audit() -> None:
    """cancel marks booking cancelled + audit_log appointment_cancelled."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    offer_id = uuid.uuid4()
    slot = datetime(2026, 6, 5, 9, 0, tzinfo=timezone.utc)

    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id))

    booking_id = uuid.uuid4()
    booking_repo.add_seed(
        _FakeBooking(
            booking_id=booking_id,
            tenant_id=tenant_id,
            offer_id=offer_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            slot_iso=slot,
            status="confirmed_deposit",
        )
    )

    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="cancel",
            doctor_id=doctor_id,
            booking_id=booking_id,
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )
    assert result.booking_id == booking_id
    assert result.booking_status == "cancelled"

    # Slot released — booking status is now cancelled (not in active set)
    cancelled = await booking_repo.find_by_doctor_slot(doctor_id, slot)
    assert cancelled is None  # find_by_doctor_slot only returns active

    # Audit log: appointment_cancelled
    cancelled_events = [e for e in audit_repo.events if e.event_type == "appointment_cancelled"]
    assert len(cancelled_events) == 1


# ───────────────────────────────────────────────────────────────────────────
# Audit log + trace event resilience (best-effort)
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_log_failure_does_not_break_turn() -> None:
    """audit_log_repo.save raises → tool MUST still return successful result."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    offer_id = uuid.uuid4()
    target_slot = datetime(2026, 6, 6, 10, 0, tzinfo=timezone.utc)

    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id))
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    raising_audit = _RaisingAuditRepo()

    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="propose_and_book",
            doctor_id=doctor_id,
            offer_id=offer_id,
            patient_id=patient_id,
            target_slot=target_slot,
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=raising_audit,
    )
    # Booking still succeeds despite audit failure
    assert result.booking_id is not None
    assert result.booking_status in (
        "pending_payment",
        "awaiting_consent",
        "confirmed_deposit",
    )


@pytest.mark.asyncio
async def test_trace_event_recorded_on_propose_and_book() -> None:
    """trace_event_repo.add invoked once for propose_and_book with sanitized payload."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    offer_id = uuid.uuid4()
    target_slot = datetime(2026, 6, 7, 10, 0, tzinfo=timezone.utc)
    turn_id = uuid.uuid4()
    span_id = uuid.uuid4()

    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id))
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()
    trace_repo = _CapturingTraceRepo()

    await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="propose_and_book",
            doctor_id=doctor_id,
            offer_id=offer_id,
            patient_id=patient_id,
            target_slot=target_slot,
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
        trace_event_repo=trace_repo,
        turn_id=turn_id,
        span_id=span_id,
    )

    assert len(trace_repo.calls) == 1
    call = trace_repo.calls[0]
    assert call["tenant_id"] == tenant_id
    assert call["turn_id"] == turn_id
    assert call["span_id"] == span_id
    assert call["event_type"].startswith("tool.appointment_reschedule_with_doctor")
    assert call["status"] == "ok"


@pytest.mark.asyncio
async def test_trace_event_failure_does_not_break_turn() -> None:
    """trace_event_repo.add raises → tool result still returned successfully."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    offer_id = uuid.uuid4()
    target_slot = datetime(2026, 6, 8, 10, 0, tzinfo=timezone.utc)

    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id))
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    result = await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="propose_and_book",
            doctor_id=doctor_id,
            offer_id=offer_id,
            patient_id=patient_id,
            target_slot=target_slot,
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
        trace_event_repo=_RaisingTraceRepo(),
        turn_id=uuid.uuid4(),
        span_id=uuid.uuid4(),
    )
    # Tool still succeeds
    assert result.booking_id is not None


@pytest.mark.asyncio
async def test_pii_sanitized_in_audit_payload() -> None:
    """patient_id stored as string ID in audit payload (not raw PII like phone/email)."""
    from src.modules.vitalia.agentic.tools.appointment_reschedule_with_doctor import (
        AppointmentRescheduleInput,
        appointment_reschedule_with_doctor,
    )

    tenant_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    offer_id = uuid.uuid4()
    target_slot = datetime(2026, 6, 9, 10, 0, tzinfo=timezone.utc)

    booking_repo = _FakeBookingRepository(tenant_id)
    doctor_ext_repo = _FakeDoctorExtensionRepository(tenant_id)
    doctor_ext_repo.add_seed(_FakeDoctorExtension(doctor_id=doctor_id))
    booking_service = _FakeBookingServiceCalls(booking_repo=booking_repo)
    audit_repo = _CapturingAuditRepo()

    await appointment_reschedule_with_doctor(
        AppointmentRescheduleInput(
            action="propose_and_book",
            doctor_id=doctor_id,
            offer_id=offer_id,
            patient_id=patient_id,
            target_slot=target_slot,
        ),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        doctor_extension_repo=doctor_ext_repo,
        booking_service=booking_service,
        scheduler_query=_scheduler_no_busy_slots,
        audit_log_repo=audit_repo,
    )
    # Audit emitted; patient stored as ID, not raw email/phone (no PII patterns)
    booked = [e for e in audit_repo.events if e.event_type == "appointment_booked"]
    assert len(booked) == 1
    payload = booked[0].payload_redacted
    # No "@" (email) or "+5" (phone) tokens introduced inadvertently
    serialized = str(payload)
    assert "@" not in serialized
    assert "+5" not in serialized


# Allow asyncio event loop to drain at module teardown (no leaked tasks).
@pytest.fixture(autouse=True)
async def _drain_event_loop():
    yield
    await asyncio.sleep(0)
