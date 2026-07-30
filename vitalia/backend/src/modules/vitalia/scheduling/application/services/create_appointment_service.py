# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Create Appointment Service — create engine appointment + brand-local clinic_map.

Rule (03-arch A12 + hipaa-lite.md):
  - Engine `appointments` table has no `clinic_id` column (single-tenant assumption).
  - Brand-local `vitalia_appointment_clinic_map` stores the clinic FK binding.
  - CREATE must persist BOTH: appointment (engine) + clinic_map (brand-local).
  - Audit log sync write BEFORE returning (PHI write = mandatory log).
  - Growth studio event emitted after audit (fire-forget).

Usage:
    service = CreateAppointmentService(
        repo=repo,
        audit_writer=audit_writer,
        growth_emitter=growth_emitter,
    )
    detail = await service.create_appointment(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        origin="walk_in",
        patient_id=patient_id,
        doctor_id=doctor_id,
        service_label="Limpieza dental",
        start_time=start_time,
        end_time=end_time,
    )
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy.exc import IntegrityError

logger = structlog.get_logger()


class CreateAppointmentService:
    """Application service: create an appointment + brand-local clinic_map.

    Orchestration flow (A12):
    1. repo.create() → engine appointment row (returns appointment_id UUID)
    2. repo.create_clinic_map() → vitalia_appointment_clinic_map row (brand-local FK)
    3. [optional] hold_service.book_with_hold() → mark slot + set hold-TTL (RN-26 fix)
    4. audit_writer.write() → HIPAA-lite mandatory sync write
    5. growth_emitter.emit_event() → fire-forget UX telemetry
    6. repo.get_by_id() → load full detail + return

    Both create + create_clinic_map happen in the same service call.
    If clinic_map persistence fails, caller sees exception and appointment
    is considered incomplete (compensating via explicit re-create).

    hold_service is optional: None for Mateo manual creates (walk_in/telefono)
    where no hold-TTL is needed. Present for proactivo_adrian flow (T-BE-2).
    """

    def __init__(
        self,
        *,
        repo: Any,
        audit_writer: Any,
        growth_emitter: Any,
        hold_service: Any = None,
        availability_check_service: Any = None,
    ) -> None:
        """Initialize CreateAppointmentService.

        Args:
            repo: Implements create(), create_clinic_map(), get_by_id().
                  Typically a combined scheduling repo adapter.
            audit_writer: AsyncAuditWriter — sync write before response.
            growth_emitter: GrowthStudioEmitter — fire-forget telemetry.
            hold_service: Optional SchedulingHoldService. If provided, called
                after clinic_map persist to mark slot + set hold-TTL (T-BE-2).
                If None (default), slot marking is skipped (Mateo manual flow).
            availability_check_service: Optional AvailabilityCheckService (T-BE-3).
                When provided, checks working hours pre-insert.
                None = skip check (e.g. proactivo_adrian flow that already validated).
        """
        self._repo = repo
        self._audit = audit_writer
        self._growth = growth_emitter
        self._hold_service = hold_service
        self._avail = availability_check_service

    async def create_appointment(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        offer_id: UUID,
        user_id: UUID,
        origin: str,
        patient_id: UUID,
        doctor_id: UUID,
        service_label: str,
        start_time: datetime,
        end_time: datetime,
        notes_internal: str | None = None,
        currency_override: str | None = None,
        slot_id: UUID | None = None,
        tenant_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create an appointment and its brand-local clinic_map entry.

        Dual persistence (A12):
        - Engine appointment row (vitalia_appointments, includes clinic_id + offer_id).
        - Brand-local clinic_map row (vitalia_appointment_clinic_map).

        T-BE-4 bugfix: clinic_id and offer_id are NOT NULL in vitalia_appointments.
        Both are now required params and threaded into repo.create().

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID — from X-Clinic-ID header (HIPAA dual filter).
                       Also stored in vitalia_appointments (NOT NULL column).
            offer_id: Catalog offer UUID — from FE selectedServiceId (NOT NULL column).
            user_id: Actor user UUID (staff creating the appointment).
            origin: AppointmentOrigin string (walk_in/telefono/proactivo_adrian/portal).
            patient_id: Patient UUID.
            doctor_id: Doctor UUID.
            service_label: Human-readable service description (denorm for display).
            start_time: Appointment start (UTC).
            end_time: Appointment end (UTC).
            notes_internal: Optional internal staff notes (PHI-adjacent — not returned).
            currency_override: Optional ISO currency override for this appointment.
            slot_id: Optional UUID of the vitalia_availability_slots row to mark
                     confirmed (required when hold_service is provided — T-BE-2).
            tenant_config: Optional tenant JSONB config dict (for TTL — T-BE-2).

        Returns:
            Full appointment detail dict (same shape as get_detail).
        """
        # Step 0a (G-round-2): Reject appointments with start_time strictly in the past.
        # Server-side authority guard — the FE cannot be trusted to enforce this.
        # Allow: start_time >= now (including "right now"). Block: start_time < now.
        if start_time < utc_now():
            from src.modules.vitalia.scheduling.domain.exceptions import PastAppointmentError  # noqa: PLC0415

            raise PastAppointmentError()

        # Step 0 (T-BE-4): Pre-insert working hours check (when availability_check_service provided).
        # Skip when None (proactivo_adrian flow, or Mateo flow without svc injected).
        # OUT_OF_HOURS → OutOfWorkingHoursError (HTTP 422). Never pre-check overlap
        # (TOCTOU-unsafe) — the DB EXCLUDE constraint catches that (23P01 → 409).
        if self._avail is not None:
            from src.modules.vitalia.scheduling.domain.availability_check import (  # noqa: PLC0415
                AvailabilityStatus,
            )
            from src.modules.vitalia.scheduling.domain.exceptions import (  # noqa: PLC0415
                OutOfWorkingHoursError,
            )

            duration_minutes = int((end_time - start_time).total_seconds() // 60)
            avail = await self._avail.check(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                doctor_id=doctor_id,
                start=start_time,
                duration_minutes=duration_minutes,
            )
            if avail.status == AvailabilityStatus.OUT_OF_HOURS:
                raise OutOfWorkingHoursError()

        # Step 1: Create engine appointment row.
        # T-BE-4 bugfix: clinic_id + offer_id are NOT NULL in vitalia_appointments.
        # Both must be supplied explicitly — no DEFAULT in schema.
        appointment_id: UUID = await self._repo.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            offer_id=offer_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            service_label=service_label,
            start_time=start_time,
            end_time=end_time,
            origin=origin,
            notes_internal=notes_internal,
            currency_override=currency_override,
        )

        # Step 2: Create brand-local clinic_map row (A12) with mirror cols (T-BE-4).
        # Mirror cols start_time/end_time/status feed the EXCLUDE constraint from migration 050.
        # IntegrityError pgcode=23P01 → AppointmentOverlapError (HTTP 409, TOCTOU-safe).
        try:
            await self._repo.create_clinic_map(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                appointment_id=appointment_id,
                patient_id=patient_id,
                doctor_id=doctor_id,
                service_label=service_label,
                origin=origin,
                currency_override=currency_override,
                start_time=start_time,
                end_time=end_time,
                status="SCHEDULED",
            )
        except IntegrityError as exc:
            orig = getattr(exc, "orig", None)
            pgcode = getattr(orig, "pgcode", None)
            if pgcode == "23P01":
                from src.modules.vitalia.scheduling.domain.exceptions import (  # noqa: PLC0415
                    AppointmentOverlapError,
                )

                raise AppointmentOverlapError(tenant_id=tenant_id, clinic_id=clinic_id) from exc
            raise  # reraise non-EXCLUDE IntegrityErrors

        # Step 2b: Mark availability slot + set hold-TTL (T-BE-2 / RN-26 fix)
        # Only called when hold_service is injected (proactivo_adrian flow).
        # Mateo manual flow (walk_in/telefono) passes hold_service=None → skip.
        if self._hold_service is not None and slot_id is not None:
            import datetime as _dt  # noqa: PLC0415

            _now = _dt.datetime.now(_dt.timezone.utc)
            await self._hold_service.book_with_hold(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                appointment_id=appointment_id,
                slot_id=slot_id,
                tenant_config=tenant_config or {},
                now=_now,
            )

        # Step 3: Audit log sync write (HIPAA mandate — PHI write = mandatory log)
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="appointment.create",
            resource_type="appointment",
            resource_id=appointment_id,
            payload={
                "origin": origin,
                "service_label": service_label,
                # No PHI values in payload (sanitize_payload strips them in audit_writer)
            },
        )

        # Step 4: Growth studio telemetry (fire-forget)
        await self._growth.emit_event(
            event_type="create_appointment",
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            entity_id=appointment_id,
            user_id=user_id,
            props={
                "origin": origin,
            },
        )

        # Step 5: Load + return full detail
        detail = await self._repo.get_by_id(
            appointment_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        logger.info(
            "appointment_created",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            origin=origin,
        )

        return detail
