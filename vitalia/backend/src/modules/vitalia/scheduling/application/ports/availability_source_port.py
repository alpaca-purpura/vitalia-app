# cap: scheduling.mateo-agenda
"""AvailabilitySourcePort — D-B port pattern (03-arch-be.md § 4).

Protocol that AvailabilityCheckService consumes. Concrete impl lives in
infrastructure/repositories/availability_query_repository.py which reads:
  - vitalia_availability_slots (working hours)
  - vitalia_appointment_clinic_map (busy ranges, status<>CANCELLED)

Why a Protocol instead of ABC:
  - Enables zero-import test doubles (unittest.mock.AsyncMock satisfies any protocol)
  - No concrete coupling in the application layer (DDD rule)
  - Matches existing port patterns in this module (fiscal_emit_port, payment_charge_port)

Every method takes tenant_id + clinic_id (HIPAA-lite dual filter — hipaa-lite.md).
"""

from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID

from src.modules.vitalia.scheduling.domain.availability_check import TimeRange


class AvailabilitySourcePort(Protocol):
    """Read-only port for availability data (D-B pattern — no cross-module import)."""

    async def get_working_hours(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        day: date,
    ) -> list[TimeRange]:
        """Return working-hour windows for a doctor on a given day.

        Returns an empty list when no schedule is configured (→ NO_SCHEDULE).
        Windows are UTC-aware half-open [start, end) ranges.

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).
            doctor_id: Doctor whose availability blocks to read.
            day: Calendar date (UTC).

        Returns:
            List of TimeRange objects (may be empty).
        """
        ...

    async def get_busy_ranges(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        day: date,
    ) -> list[TimeRange]:
        """Return confirmed/pending appointment time ranges for a doctor on a given day.

        Excludes CANCELLED appointments. Ranges are UTC-aware half-open [start, end).

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).
            doctor_id: Doctor whose booked slots to read.
            day: Calendar date (UTC).

        Returns:
            List of TimeRange objects for booked appointments.
        """
        ...

    async def list_active_doctors(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> list[tuple[UUID, str]]:
        """Return (doctor_id, display_name) for all active doctors in a clinic.

        No PHI in result: display_name is professional label ("Dr. García"),
        not patient information.

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).

        Returns:
            List of (UUID, str) tuples for active doctors.
        """
        ...

    async def get_service_day_strips(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        offer_id: UUID,
        day: date,
    ) -> list[tuple[UUID, str, list[TimeRange], list[TimeRange]]]:
        """Return per-doctor working/busy strips for all doctors of a service on a day.

        Resolves the service (offer) to its linked specialists, restricted to the
        clinic-active set (dual filter — cross-clinic/cross-tenant excluded). Falls
        back to all clinic-active doctors when the service has no links.

        No PHI in result: only (doctor_id, professional label, working ranges,
        busy ranges) — never any patient field.

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).
            offer_id: Service (offer) whose specialists to resolve.
            day: Calendar date (UTC).

        Returns:
            List of (doctor_id, label, working_ranges, busy_ranges) tuples.
        """
        ...
