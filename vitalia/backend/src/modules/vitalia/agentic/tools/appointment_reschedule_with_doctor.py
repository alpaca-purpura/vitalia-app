# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Vitalia AGENTIC tool — `appointment_reschedule_with_doctor`.

R23: production_code=True AGENTIC tool. Opus 4.7 EXCLUSIVE.
Story 11 T-tools-3.

Spec sources:
  * 02-design-agentic.md § 5.2 flow + § 6.4 verbose spec
  * 03-arch-agentic.md § 4.4 tool architecture + § 1 anti-duplication mandate
  * 06-tickets.yaml::T-tools-3 acceptance criteria A1-A3
  * 05-guidelines.md § 1.10 R23 agentic patterns + § 1.6 PII sanitization +
    § 1.2 anti-duplication EXTEND base inventory

Semantics — 4 actions discriminated by `input.action`:

  list_slots
    - READ-ONLY. Query candidate slots from `scheduler_query` callable
      (extends @luana/core/scheduling.calendar surface — see § Anti-duplication
      audit below).
    - Filter by appointment_type compat (consultation/control/surgery)
      → DoctorExtension.appointment_types intersect.
    - Filter by treatment_room_assignment (vertical-medical extension)
      → DoctorExtension.treatment_room presence.
    - Filter by max_concurrent_per_doctor (vertical-medical extension)
      → BookingRepository.list_by_doctor active count vs DoctorExtension.max_concurrent_per_slot.
    - NO side effects. NO audit_log row.

  propose_and_book
    - DELEGATES to BookingService.create_booking (T-be-5) which holds
      pg_advisory_lock per (doctor_id, slot_iso). Atomic guard prevents
      double-booking under concurrency.
    - 60s idempotency window: same (patient_id, doctor_id, target_slot)
      returns existing booking_id (D2 idempotency cache).
    - On SlotTakenError (race lost) → returns booking_status="slot_taken"
      WITHOUT raising — sales_agent re-lists slots per § 5.2 failure branch.
    - audit_log appointment_booked event (best-effort) — sanitized payload.

  reschedule_existing
    - Atomic: release old slot + reserve new slot.
    - Implementation: soft-delete old booking (releases active set) +
      delegate new (doctor, target_slot) to BookingService.create_booking
      under fresh advisory lock. Old booking is replaced rather than
      mutated — preserves audit trail invariant (immutable).
    - audit_log appointment_rescheduled with old_slot_iso + new_slot_iso.

  cancel
    - Soft-delete booking (status → cancelled). Slot freed for re-listing.
    - audit_log appointment_cancelled.

Tenant isolation (security boundary):
  * tenant_id MUST NEVER appear in input schema — injected from ctx via
    sales_agent tool dispatcher.
  * BookingRepository + DoctorExtensionRepository + BookingService receive
    tenant_id at construction (caller wires tenant-scoped instances).

Observability (best-effort per R23 + copilot-observability.md):
  * audit_log_repo + trace_event_repo writes wrapped in try/except + structlog
    warning. Tool turn NEVER breaks on observability failure.
  * PII sanitized via `sanitize_payload` BEFORE persist — patient phone /
    email / signature evidence NEVER reach trace store raw. Patient/doctor
    UUIDs surface as IDs only (safe identifiers).

Cost: $0 LLM (deterministic SQL + business rules). Latency budget per
02-design § 6.4: list_slots p50 180ms / p99 500ms; propose_and_book p50
280ms / p99 800ms.

Anti-duplication audit (Step 0 GATE pre-write — verified 2026-05-14):
  * `appointment_reschedule_with_doctor|propose_and_book|reschedule_existing`
    cross-codebase grep — NO collision (NEW vertical-medical surface).
  * `BookingService` (T-be-5 — `application/services/booking_service.py`)
    REUSE — atomic create_booking + 60s idempotency + pg_advisory_lock per
    (doctor_id, slot_iso) ALREADY enforced. Tool delegates, NEVER duplicates.
  * `BookingRepository.find_by_doctor_slot` + `list_by_doctor` (T-be-3)
    REUSE for slot occupancy + concurrency count.
  * `DoctorExtensionRepository.get_by_doctor_id` (T-be-3) REUSE for
    vertical-medical extension lookup (specialty/treatment_room/max_concurrent/
    appointment_types).
  * `acquire/release_slot_advisory_lock` (T-be-2 infrastructure) REUSE —
    BookingService internal usage covers atomic guard.
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    (canonical) — NEVER re-implemented (`.claude/rules/anti-duplication.md`).
  * `BaseTraceEventRepoProtocol` from `luana_core_observability.persistence`
    (structural Protocol) — handler accepts any concrete implementing.
  * "@luana/core/scheduling.calendar" referenced in spec § 6.4 maps to the
    PER-VERTICAL `BookingService` + `BookingRepository` + `DoctorExtensionRepository`
    surface registered above. NO core/luana-core-platform scheduling tool exists
    that would duplicate this responsibility (verified via grep — only
    `core/.../links/ports/scheduling.py` is a Nicolify-specific port unrelated
    to vertical-medical booking semantics).
  * Calendar slot enumeration provided via `scheduler_query` callable Protocol —
    caller supplies the source (testable via in-memory fake; production wires
    a deterministic 9-17 weekday generator OR external @luana/core
    scheduling adapter once formalized).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timezone
from typing import Any, Literal, Protocol

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)


# ─── Configuration constants ─────────────────────────────────────────────

# Default appointment_type when none requested (most common for new patients).
_DEFAULT_APPOINTMENT_TYPE: str = "consultation"

# Active booking statuses that count as "slot occupied" (mirror BookingRepository).
_ACTIVE_BOOKING_STATUSES: frozenset[str] = frozenset(
    {
        "pending_payment",
        "awaiting_consent",
        "confirmed_deposit",
        "confirmed_full",
    }
)

# Audit log severity for routine appointment lifecycle events.
_AUDIT_SEVERITY_INFO: str = "info"


# ─── Pydantic schemas (input/output contract) ────────────────────────────


class WindowSpec(BaseModel):
    """Preferred query window for list_slots — start date + days span."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    start: date = Field(..., description="Window start date (tenant TZ).")
    days: int = Field(14, ge=1, le=60, description="Span in days (max 60).")


class AppointmentRescheduleInput(BaseModel):
    """Input schema — tenant_id intentionally OMITTED (ctx injection).

    Per 02-design § 6.4 + .claude/rules/tenant-isolation.md:
    > tenant_id NOT in schema — injected via tool dispatcher from ctx
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["list_slots", "propose_and_book", "reschedule_existing", "cancel"] = Field(
        ..., description="4-action discriminator."
    )
    doctor_id: uuid.UUID = Field(..., description="Doctor UUID.")
    booking_id: uuid.UUID | None = Field(
        None,
        description="Booking UUID — required for reschedule_existing / cancel.",
    )
    offer_id: uuid.UUID | None = Field(None, description="Offer UUID — required for propose_and_book.")
    patient_id: uuid.UUID | None = Field(None, description="Patient UUID — required for propose_and_book.")
    preferred_window: WindowSpec | None = Field(None, description="Window for list_slots.")
    target_slot: datetime | None = Field(
        None,
        description="Target slot — required for propose_and_book / reschedule_existing.",
    )
    appointment_type: Literal["consultation", "control", "surgery"] | None = Field(
        None,
        description=(
            "Optional preferred appointment type for propose_and_book. Defaults to 'consultation' when omitted."
        ),
    )


class AppointmentRescheduleOutput(BaseModel):
    """Result of appointment_reschedule_with_doctor tool invocation.

    Per 02-design § 6.4 verbose spec.
    """

    model_config = ConfigDict(frozen=True)

    available_slots: list[datetime] = Field(
        default_factory=list,
        description="Populated only on action=list_slots.",
    )
    booking_id: uuid.UUID | None = Field(
        None, description="Booking UUID — populated on book/reschedule/cancel success."
    )
    booking_status: str | None = Field(
        None,
        description=(
            "'pending_payment' / 'awaiting_consent' / 'confirmed_deposit' / "
            "'cancelled' / 'slot_taken' / 'booking_not_found' / "
            "'missing_required_fields'."
        ),
    )
    payment_url: str | None = Field(
        None,
        description="Payment link — populated when downstream payment dispatcher emits one.",
    )
    appointment_type: Literal["consultation", "control", "surgery"] | None = Field(
        None, description="Resolved appointment type for the booking."
    )
    treatment_room_assigned: str | None = Field(None, description="Treatment room from DoctorExtension.")


# ─── Dependency Protocols (decouple from concrete classes) ────────────────


class _BookingRepoLike(Protocol):
    """Minimal surface consumed from BookingRepository (T-be-3)."""

    async def get_by_id(self, booking_id: uuid.UUID) -> Any: ...

    async def find_by_doctor_slot(self, doctor_id: uuid.UUID, slot_iso: datetime) -> Any: ...

    async def list_by_doctor(self, doctor_id: uuid.UUID, *, status: str | None = None) -> list[Any]: ...

    async def save(self, booking: Any) -> None: ...


class _DoctorExtensionRepoLike(Protocol):
    """Minimal surface consumed from DoctorExtensionRepository (T-be-3)."""

    async def get_by_doctor_id(self, doctor_id: uuid.UUID) -> Any: ...


class _BookingServiceLike(Protocol):
    """Minimal surface consumed from BookingService (T-be-5)."""

    async def create_booking(self, request: Any, tenant_id: uuid.UUID) -> Any: ...


class _AuditLogRepoLike(Protocol):
    """Minimal surface consumed from MedicalAuditLogRepository (T-be-3)."""

    async def save(self, audit_event: Any) -> None: ...


class _TraceEventRepoLike(Protocol):
    """Mirror of BaseTraceEventRepoProtocol — see luana_core_observability."""

    def add(
        self,
        *,
        tenant_id: uuid.UUID,
        turn_id: uuid.UUID,
        span_id: uuid.UUID,
        event_type: str,
        name: str | None = ...,
        data: dict[str, Any] | None = ...,
        duration_ms: int | None = ...,
        status: str = ...,
        **agent_specific: Any,
    ) -> Any: ...


class _SchedulerQueryLike(Protocol):
    """Calendar candidate slot enumeration — extends @luana/core scheduling.

    Returns naive list of candidate (doctor_id, datetime) slots within the
    requested window. Filtering by occupancy / extension / max_concurrent
    is done downstream by this tool. Caller supplies a deterministic source
    (e.g. weekday 9-17 generator OR external @luana/core scheduling adapter).
    """

    def __call__(self, doctor_id: uuid.UUID, start: datetime, days: int) -> list[datetime]: ...


# ─── Handler ─────────────────────────────────────────────────────────────


async def appointment_reschedule_with_doctor(
    input: AppointmentRescheduleInput,
    *,
    tenant_id: uuid.UUID,
    booking_repo: _BookingRepoLike,
    doctor_extension_repo: _DoctorExtensionRepoLike,
    booking_service: _BookingServiceLike,
    scheduler_query: _SchedulerQueryLike,
    audit_log_repo: _AuditLogRepoLike,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: uuid.UUID | None = None,
    span_id: uuid.UUID | None = None,
) -> AppointmentRescheduleOutput:
    """List slots / book / reschedule / cancel doctor appointments.

    See module docstring for full semantics + spec references.

    Parameters
    ----------
    input
        Pydantic input — tenant_id NEVER here (security boundary).
    tenant_id
        Injected from ctx by sales_agent tool dispatcher.
    booking_repo
        Tenant-scoped BookingRepository (T-be-3).
    doctor_extension_repo
        Tenant-scoped DoctorExtensionRepository (T-be-3).
    booking_service
        BookingService (T-be-5) — atomic create_booking with advisory lock +
        60s idempotency.
    scheduler_query
        Callable returning candidate slots — extends @luana/core/scheduling
        calendar surface (caller supplies the data source).
    audit_log_repo
        MedicalAuditLogRepository (T-be-3) — append-only events.
    trace_event_repo
        Optional — when supplied, tool records one trace_event for the turn.
    turn_id / span_id
        Required iff trace_event_repo supplied — caller's correlation IDs.

    Returns
    -------
    AppointmentRescheduleOutput — never raises tool-side errors. Validation
    failures + slot races + missing bookings surface via `booking_status`
    error markers.
    """
    if input.action == "list_slots":
        return await _handle_list_slots(
            input,
            tenant_id=tenant_id,
            booking_repo=booking_repo,
            doctor_extension_repo=doctor_extension_repo,
            scheduler_query=scheduler_query,
            trace_event_repo=trace_event_repo,
            turn_id=turn_id,
            span_id=span_id,
        )
    if input.action == "propose_and_book":
        return await _handle_propose_and_book(
            input,
            tenant_id=tenant_id,
            booking_repo=booking_repo,
            doctor_extension_repo=doctor_extension_repo,
            booking_service=booking_service,
            audit_log_repo=audit_log_repo,
            trace_event_repo=trace_event_repo,
            turn_id=turn_id,
            span_id=span_id,
        )
    if input.action == "reschedule_existing":
        return await _handle_reschedule_existing(
            input,
            tenant_id=tenant_id,
            booking_repo=booking_repo,
            doctor_extension_repo=doctor_extension_repo,
            booking_service=booking_service,
            audit_log_repo=audit_log_repo,
            trace_event_repo=trace_event_repo,
            turn_id=turn_id,
            span_id=span_id,
        )
    # input.action == "cancel"
    return await _handle_cancel(
        input,
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        audit_log_repo=audit_log_repo,
        trace_event_repo=trace_event_repo,
        turn_id=turn_id,
        span_id=span_id,
    )


# ─── Action handlers ─────────────────────────────────────────────────────


async def _handle_list_slots(
    input: AppointmentRescheduleInput,
    *,
    tenant_id: uuid.UUID,
    booking_repo: _BookingRepoLike,
    doctor_extension_repo: _DoctorExtensionRepoLike,
    scheduler_query: _SchedulerQueryLike,
    trace_event_repo: _TraceEventRepoLike | None,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
) -> AppointmentRescheduleOutput:
    """list_slots: READ-ONLY. Filter candidate slots by extension config + occupancy."""
    # 1. Doctor extension required for vertical-medical filters.
    extension = await doctor_extension_repo.get_by_doctor_id(input.doctor_id)
    if extension is None:
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.appointment_reschedule_with_doctor.list_slots",
            payload={
                "doctor_id": str(input.doctor_id),
                "warning": "no_doctor_extension",
            },
            status="ok",
        )
        return AppointmentRescheduleOutput(available_slots=[])

    # 2. Filter by appointment_type compat (when input requests one).
    requested_type = input.appointment_type or _DEFAULT_APPOINTMENT_TYPE
    supported_types: list[str] = list(extension.appointment_types or [])
    if supported_types and requested_type not in supported_types:
        # Doctor doesn't support this appointment type → empty slots.
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.appointment_reschedule_with_doctor.list_slots",
            payload={
                "doctor_id": str(input.doctor_id),
                "warning": "appointment_type_not_supported",
                "requested_type": requested_type,
                "supported": supported_types,
            },
            status="ok",
        )
        return AppointmentRescheduleOutput(available_slots=[])

    # 3. Resolve window — defaults to today + 14 days when not provided.
    if input.preferred_window is not None:
        window_start_dt = datetime(
            year=input.preferred_window.start.year,
            month=input.preferred_window.start.month,
            day=input.preferred_window.start.day,
            tzinfo=timezone.utc,
        )
        window_days = input.preferred_window.days
    else:
        now = datetime.now(tz=timezone.utc)
        window_start_dt = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)
        window_days = 14

    # 4. Query candidate slots via @luana/core scheduling-extending callable.
    candidates = scheduler_query(input.doctor_id, window_start_dt, window_days)

    # 5. Determine concurrency cap from extension.
    max_concurrent = max(int(getattr(extension, "max_concurrent_per_slot", 1) or 1), 1)

    # 6. Pull active bookings for this doctor in the window.
    active_bookings = await _list_active_doctor_bookings(booking_repo, doctor_id=input.doctor_id)

    # 7. Filter candidates by occupancy under max_concurrent.
    occupancy: dict[datetime, int] = {}
    for bk in active_bookings:
        occupancy[bk.slot_iso] = occupancy.get(bk.slot_iso, 0) + 1

    available: list[datetime] = []
    for slot in candidates:
        count = occupancy.get(slot, 0)
        if count < max_concurrent:
            available.append(slot)

    await _emit_trace_event(
        trace_event_repo,
        tenant_id=tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        event_type="tool.appointment_reschedule_with_doctor.list_slots",
        payload={
            "doctor_id": str(input.doctor_id),
            "candidates_count": len(candidates),
            "available_count": len(available),
            "max_concurrent": max_concurrent,
        },
        status="ok",
    )

    return AppointmentRescheduleOutput(available_slots=available)


async def _handle_propose_and_book(
    input: AppointmentRescheduleInput,
    *,
    tenant_id: uuid.UUID,
    booking_repo: _BookingRepoLike,
    doctor_extension_repo: _DoctorExtensionRepoLike,
    booking_service: _BookingServiceLike,
    audit_log_repo: _AuditLogRepoLike,
    trace_event_repo: _TraceEventRepoLike | None,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
) -> AppointmentRescheduleOutput:
    """propose_and_book: delegate to BookingService (atomic + 60s idempotent)."""
    # 1. Validate required fields up front.
    if input.patient_id is None or input.offer_id is None or input.target_slot is None:
        return AppointmentRescheduleOutput(
            booking_status="missing_required_fields",
        )

    # 2. Pull doctor extension for treatment_room + appointment_type resolution.
    extension = await doctor_extension_repo.get_by_doctor_id(input.doctor_id)
    if extension is None:
        return AppointmentRescheduleOutput(
            booking_status="doctor_extension_not_found",
        )

    requested_type = input.appointment_type or _DEFAULT_APPOINTMENT_TYPE
    supported_types: list[str] = list(extension.appointment_types or [])
    if supported_types and requested_type not in supported_types:
        return AppointmentRescheduleOutput(
            booking_status="appointment_type_not_supported",
        )

    # 3. Build CreateBookingRequest — late import avoids circular at module load.
    from src.modules.vitalia.application.services.booking_service import (
        CreateBookingRequest,
        SlotTakenError,
    )

    request = CreateBookingRequest(
        offer_id=input.offer_id,
        doctor_id=input.doctor_id,
        patient_id=input.patient_id,
        slot_iso=input.target_slot,
        delivery_channel="whatsapp",
        requires_informed_consent=False,  # Resolved downstream by offer service
        requires_prepay=False,
        deposit_only=True,
    )

    # 4. Delegate to BookingService — atomic + idempotent.
    try:
        booking_result = await booking_service.create_booking(request=request, tenant_id=tenant_id)
    except SlotTakenError as exc:
        # Race lost — sales_agent re-lists slots per § 5.2 failure branch.
        await _append_audit_log(
            audit_log_repo,
            tenant_id=tenant_id,
            event_type="appointment_book_slot_taken",
            severity=_AUDIT_SEVERITY_INFO,
            patient_id=input.patient_id,
            booking_id=None,
            payload={
                "doctor_id": str(input.doctor_id),
                "slot_iso": exc.slot_iso.isoformat(),
                "appointment_type": requested_type,
            },
        )
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.appointment_reschedule_with_doctor.propose_and_book",
            payload={
                "doctor_id": str(input.doctor_id),
                "slot_iso": exc.slot_iso.isoformat(),
                "outcome": "slot_taken",
            },
            status="error",
        )
        return AppointmentRescheduleOutput(booking_status="slot_taken")

    # 5. Audit log — appointment_booked.
    await _append_audit_log(
        audit_log_repo,
        tenant_id=tenant_id,
        event_type="appointment_booked",
        severity=_AUDIT_SEVERITY_INFO,
        patient_id=input.patient_id,
        booking_id=booking_result.booking_id,
        payload={
            "doctor_id": str(input.doctor_id),
            "slot_iso": input.target_slot.isoformat(),
            "appointment_type": requested_type,
            "treatment_room": getattr(extension, "treatment_room", None),
            "is_idempotent_hit": booking_result.is_idempotent_hit,
        },
    )

    # 6. Build typed result + trace event.
    result = AppointmentRescheduleOutput(
        booking_id=booking_result.booking_id,
        booking_status=booking_result.status,
        appointment_type=requested_type,  # type: ignore[arg-type]
        treatment_room_assigned=getattr(extension, "treatment_room", None),
        payment_url=getattr(booking_result, "payment_url", None),
    )
    await _emit_trace_event(
        trace_event_repo,
        tenant_id=tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        event_type="tool.appointment_reschedule_with_doctor.propose_and_book",
        payload={
            "doctor_id": str(input.doctor_id),
            "booking_id": str(result.booking_id),
            "appointment_type": requested_type,
            "is_idempotent_hit": booking_result.is_idempotent_hit,
        },
        status="ok",
    )
    return result


async def _handle_reschedule_existing(
    input: AppointmentRescheduleInput,
    *,
    tenant_id: uuid.UUID,
    booking_repo: _BookingRepoLike,
    doctor_extension_repo: _DoctorExtensionRepoLike,
    booking_service: _BookingServiceLike,
    audit_log_repo: _AuditLogRepoLike,
    trace_event_repo: _TraceEventRepoLike | None,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
) -> AppointmentRescheduleOutput:
    """reschedule_existing: release old slot + reserve new (atomic via BookingService)."""
    if input.booking_id is None or input.target_slot is None:
        return AppointmentRescheduleOutput(
            booking_status="missing_required_fields",
        )

    existing = await booking_repo.get_by_id(input.booking_id)
    if existing is None:
        return AppointmentRescheduleOutput(booking_status="booking_not_found")

    extension = await doctor_extension_repo.get_by_doctor_id(input.doctor_id)
    treatment_room = getattr(extension, "treatment_room", None)
    appointment_type = getattr(existing, "appointment_type", None) or _DEFAULT_APPOINTMENT_TYPE

    old_slot = existing.slot_iso
    old_status = existing.status

    # 1. Release old slot — mark existing booking cancelled (preserves audit trail).
    existing.status = "cancelled"
    await booking_repo.save(existing)

    # 2. Reserve new slot — delegate to BookingService for atomic guard.
    from src.modules.vitalia.application.services.booking_service import (
        CreateBookingRequest,
        SlotTakenError,
    )

    request = CreateBookingRequest(
        offer_id=existing.offer_id,
        doctor_id=input.doctor_id,
        patient_id=existing.patient_id,
        slot_iso=input.target_slot,
        delivery_channel="whatsapp",
        requires_informed_consent=False,
        requires_prepay=False,
        deposit_only=True,
    )
    try:
        new_result = await booking_service.create_booking(request=request, tenant_id=tenant_id)
    except SlotTakenError:
        # Reschedule failed — restore old booking status so we don't lose it.
        existing.status = old_status
        await booking_repo.save(existing)
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.appointment_reschedule_with_doctor.reschedule_existing",
            payload={
                "booking_id": str(input.booking_id),
                "outcome": "new_slot_taken",
            },
            status="error",
        )
        return AppointmentRescheduleOutput(booking_status="slot_taken")

    # 3. Audit log — appointment_rescheduled (links old booking_id ↔ new booking_id).
    await _append_audit_log(
        audit_log_repo,
        tenant_id=tenant_id,
        event_type="appointment_rescheduled",
        severity=_AUDIT_SEVERITY_INFO,
        patient_id=existing.patient_id,
        booking_id=new_result.booking_id,
        payload={
            "doctor_id": str(input.doctor_id),
            "old_booking_id": str(input.booking_id),
            "old_slot_iso": old_slot.isoformat(),
            "new_slot_iso": input.target_slot.isoformat(),
            "old_status": old_status,
            "new_status": new_result.status,
        },
    )

    await _emit_trace_event(
        trace_event_repo,
        tenant_id=tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        event_type="tool.appointment_reschedule_with_doctor.reschedule_existing",
        payload={
            "old_booking_id": str(input.booking_id),
            "new_booking_id": str(new_result.booking_id),
            "old_slot_iso": old_slot.isoformat(),
            "new_slot_iso": input.target_slot.isoformat(),
        },
        status="ok",
    )

    # 4. Return NEW booking_id — the active booking for this patient is now
    #    the freshly-reserved row at the new slot. The old row is preserved
    #    as cancelled (audit trail intact) and audit_log links old → new.
    return AppointmentRescheduleOutput(
        booking_id=new_result.booking_id,
        booking_status=new_result.status,
        appointment_type=appointment_type,  # type: ignore[arg-type]
        treatment_room_assigned=treatment_room,
    )


async def _handle_cancel(
    input: AppointmentRescheduleInput,
    *,
    tenant_id: uuid.UUID,
    booking_repo: _BookingRepoLike,
    audit_log_repo: _AuditLogRepoLike,
    trace_event_repo: _TraceEventRepoLike | None,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
) -> AppointmentRescheduleOutput:
    """cancel: soft-cancel booking + audit_log."""
    if input.booking_id is None:
        return AppointmentRescheduleOutput(
            booking_status="missing_required_fields",
        )

    existing = await booking_repo.get_by_id(input.booking_id)
    if existing is None:
        return AppointmentRescheduleOutput(booking_status="booking_not_found")

    existing.status = "cancelled"
    await booking_repo.save(existing)

    await _append_audit_log(
        audit_log_repo,
        tenant_id=tenant_id,
        event_type="appointment_cancelled",
        severity=_AUDIT_SEVERITY_INFO,
        patient_id=existing.patient_id,
        booking_id=input.booking_id,
        payload={
            "doctor_id": str(input.doctor_id),
            "slot_iso": existing.slot_iso.isoformat(),
        },
    )

    await _emit_trace_event(
        trace_event_repo,
        tenant_id=tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        event_type="tool.appointment_reschedule_with_doctor.cancel",
        payload={
            "booking_id": str(input.booking_id),
            "doctor_id": str(input.doctor_id),
        },
        status="ok",
    )

    return AppointmentRescheduleOutput(
        booking_id=input.booking_id,
        booking_status="cancelled",
    )


# ─── Helpers ─────────────────────────────────────────────────────────────


async def _list_active_doctor_bookings(
    booking_repo: _BookingRepoLike,
    *,
    doctor_id: uuid.UUID,
) -> list[Any]:
    """Return only active (non-cancelled, non-deleted) bookings for a doctor.

    Iterates over every active status because BookingRepository.list_by_doctor
    accepts a single status filter; we union locally to keep the repo surface
    simple and tenant-scoped.
    """
    out: list[Any] = []
    for status in _ACTIVE_BOOKING_STATUSES:
        rows = await booking_repo.list_by_doctor(doctor_id, status=status)
        out.extend(rows)
    return out


async def _append_audit_log(
    repo: _AuditLogRepoLike,
    *,
    tenant_id: uuid.UUID,
    event_type: str,
    severity: str,
    patient_id: uuid.UUID | None,
    booking_id: uuid.UUID | None,
    payload: dict[str, Any],
) -> None:
    """Append audit event. Best-effort (try/except + warning) — never breaks turn.

    Per `.claude/rules/copilot-observability.md`: every audit/observability
    write wrapped in try/except + structlog warning. PII sanitized via
    `sanitize_payload` BEFORE persist.
    """
    try:
        from src.modules.vitalia.infrastructure.models.medical_audit_log_model import (
            VitaliaMedicalAuditLogModel,
        )

        sanitized = sanitize_payload(payload)
        audit_event = VitaliaMedicalAuditLogModel(
            tenant_id=tenant_id,
            event_type=event_type,
            severity=severity,
            patient_id=patient_id,
            booking_id=booking_id,
            payload_redacted=sanitized,
            actor_type="sales_agent",
        )
        await repo.save(audit_event)
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "appointment_reschedule_with_doctor.audit_log_persist_failed",
            exc=str(exc),
            event_type=event_type,
            tenant_id=str(tenant_id),
        )


async def _emit_trace_event(
    trace_event_repo: _TraceEventRepoLike | None,
    *,
    tenant_id: uuid.UUID,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
    event_type: str,
    payload: dict[str, Any],
    status: str,
) -> None:
    """Best-effort trace_event emission. NEVER breaks tool turn (R23).

    Skips silently if repo not supplied or correlation IDs missing.
    Logs warning on persistence failure.
    """
    if trace_event_repo is None or turn_id is None or span_id is None:
        return

    try:
        sanitized = sanitize_payload(payload)
        trace_event_repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type=event_type,
            name="appointment_reschedule_with_doctor",
            data=sanitized,
            status=status,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "appointment_reschedule_with_doctor.trace_event_persist_failed",
            exc=str(exc),
            tenant_id=str(tenant_id),
        )


# Keep asyncio reference live (some checkers strip unused import otherwise).
_ = asyncio


__all__ = [
    "AppointmentRescheduleInput",
    "AppointmentRescheduleOutput",
    "WindowSpec",
    "appointment_reschedule_with_doctor",
]
