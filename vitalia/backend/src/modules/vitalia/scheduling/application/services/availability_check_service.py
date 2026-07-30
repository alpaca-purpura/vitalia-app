# cap: scheduling.mateo-agenda
"""AvailabilityCheckService — orchestrates the 4-state availability matrix (T-BE-3).

Business logic per 03-arch-be.md § 6:

  check(doctor_id, start, duration_minutes) →
    working = port.get_working_hours(tenant_id, clinic_id, doctor_id, day)
    if not working: NO_SCHEDULE
    proposed = TimeRange(start, start + duration)
    if not any(w.contains(proposed) for w in working): OUT_OF_HOURS
    busy = port.get_busy_ranges(tenant_id, clinic_id, doctor_id, day)
    conflict = first b in busy where proposed.overlaps(b)
    if conflict: BUSY (conflict_label="se solapa con HH:MM", conflict_start=b.start)
    else: AVAILABLE

  free_doctors(start, duration_minutes) →
    [d for d in active_doctors if check(d, start, duration).status == AVAILABLE]

PHI safety:
  - conflict_label contains ONLY time ("se solapa con 10:15"), never patient name/ID.
  - FreeDoctorItem.doctor_label is professional display name, not patient data.
  - All queries dual-filtered: tenant_id + clinic_id (HIPAA-lite hipaa-lite.md).

No cross-module imports: clinics domain accessed only via AvailabilitySourcePort.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.application.ports.availability_source_port import (
    AvailabilitySourcePort,
)
from src.modules.vitalia.scheduling.domain.availability_check import (
    AvailabilityCheckResult,
    AvailabilityStatus,
    TimeRange,
)

logger = structlog.get_logger()


@dataclass(frozen=True)
class FreeDoctorItem:
    """A doctor confirmed available for the requested slot. No PHI."""

    doctor_id: UUID
    doctor_label: str  # e.g. "Dr. García" — professional display name, NOT patient PHI


@dataclass(frozen=True)
class ServiceDayBlock:
    """One working_hours / busy strip on the service-day timeline. No PHI."""

    kind: str  # "working_hours" | "busy"
    start: datetime
    end: datetime


@dataclass(frozen=True)
class ServiceDayDoctorResult:
    """A doctor's full-day strips for a service. No PHI (professional label only)."""

    doctor_id: UUID
    doctor_label: str
    blocks: list[ServiceDayBlock]


class AvailabilityCheckService:
    """Availability business logic — check a slot, list free doctors.

    Thin orchestration: delegates data reads to AvailabilitySourcePort,
    applies domain rules from TimeRange/AvailabilityStatus (pure domain layer).
    """

    def __init__(self, *, port: AvailabilitySourcePort) -> None:
        """Initialise with injected port (D-B pattern).

        Args:
            port: Any object satisfying AvailabilitySourcePort protocol.
        """
        self._port = port

    async def check(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        start: datetime,
        duration_minutes: int,
    ) -> AvailabilityCheckResult:
        """Check availability for a proposed appointment slot.

        Applies the 4-state matrix (03-arch-be.md § 6 + RN-3/RN-4):
          NO_SCHEDULE → OUT_OF_HOURS → BUSY → AVAILABLE

        Args:
            tenant_id: Tenant (dual filter L1).
            clinic_id: Clinic (dual filter L2 — HIPAA-lite).
            doctor_id: Doctor to check.
            start: Proposed start datetime (UTC-aware).
            duration_minutes: Appointment duration in minutes.

        Returns:
            AvailabilityCheckResult with status + optional conflict info (no PHI).
        """
        day = start.astimezone(timezone.utc).date()
        proposed = TimeRange(
            start=start,
            end=start + timedelta(minutes=duration_minutes),
        )

        working_hours = await self._port.get_working_hours(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            day=day,
        )

        if not working_hours:
            logger.debug(
                "availability_no_schedule",
                doctor_id=str(doctor_id),
                clinic_id=str(clinic_id),
                day=str(day),
            )
            return AvailabilityCheckResult(
                status=AvailabilityStatus.NO_SCHEDULE,
                conflict_label=None,
                conflict_start=None,
            )

        if not any(window.contains(proposed) for window in working_hours):
            return AvailabilityCheckResult(
                status=AvailabilityStatus.OUT_OF_HOURS,
                conflict_label=None,
                conflict_start=None,
            )

        busy_ranges = await self._port.get_busy_ranges(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            day=day,
        )

        for busy in busy_ranges:
            if proposed.overlaps(busy):
                # conflict_label: time only — NO PHI (RN-5)
                local_start = busy.start.astimezone(timezone.utc)
                conflict_label = f"se solapa con {local_start.strftime('%H:%M')}"
                return AvailabilityCheckResult(
                    status=AvailabilityStatus.BUSY,
                    conflict_label=conflict_label,
                    conflict_start=busy.start,
                )

        return AvailabilityCheckResult(
            status=AvailabilityStatus.AVAILABLE,
            conflict_label=None,
            conflict_start=None,
        )

    async def free_doctors(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        start: datetime,
        duration_minutes: int,
    ) -> list[FreeDoctorItem]:
        """Return all active doctors available for the requested slot.

        Iterates active doctors and calls check() for each. O(n) where n =
        active doctors in clinic (typically < 20). No caching — stateless.

        Args:
            tenant_id: Tenant (dual filter L1).
            clinic_id: Clinic (dual filter L2 — HIPAA-lite).
            start: Proposed start datetime (UTC-aware).
            duration_minutes: Appointment duration in minutes.

        Returns:
            List of FreeDoctorItem for AVAILABLE doctors only. May be empty.
        """
        doctors = await self._port.list_active_doctors(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        if not doctors:
            return []

        available: list[FreeDoctorItem] = []
        for doctor_id, doctor_label in doctors:
            result = await self.check(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                doctor_id=doctor_id,
                start=start,
                duration_minutes=duration_minutes,
            )
            if result.status == AvailabilityStatus.AVAILABLE:
                available.append(FreeDoctorItem(doctor_id=doctor_id, doctor_label=doctor_label))

        logger.debug(
            "availability_free_doctors",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            total=len(doctors),
            available=len(available),
        )
        return available

    async def service_day(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        offer_id: UUID,
        day: date,
    ) -> list[ServiceDayDoctorResult]:
        """Return the day's working/busy strips for all doctors of a service.

        Read-only composition (T-D1): delegates to port.get_service_day_strips
        (which reuses get_working_hours + get_busy_ranges), then tags each strip
        with its kind and sorts by start. No PHI — professional label only.

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).
            offer_id: Service (offer) whose specialists to resolve.
            day: Calendar date (UTC).

        Returns:
            List of ServiceDayDoctorResult (may be empty), one per rendered doctor.
        """
        strips = await self._port.get_service_day_strips(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            offer_id=offer_id,
            day=day,
        )

        results: list[ServiceDayDoctorResult] = []
        for doctor_id, label, working, busy in strips:
            blocks = [ServiceDayBlock(kind="working_hours", start=w.start, end=w.end) for w in working]
            blocks += [ServiceDayBlock(kind="busy", start=b.start, end=b.end) for b in busy]
            blocks.sort(key=lambda bl: bl.start)
            results.append(ServiceDayDoctorResult(doctor_id=doctor_id, doctor_label=label, blocks=blocks))

        logger.debug(
            "availability_service_day",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            offer_id=str(offer_id),
            day=str(day),
            doctor_count=len(results),
        )
        return results
