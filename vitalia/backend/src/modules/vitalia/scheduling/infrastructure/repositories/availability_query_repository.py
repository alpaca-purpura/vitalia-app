# cap: scheduling.mateo-agenda
"""AvailabilityQueryRepository — concrete implementation of AvailabilitySourcePort.

Data sources:
  get_working_hours → vitalia_availability_slots (slot_date, start_ts, end_ts)
    created by AvailabilityProjectionService from clinics availability blocks.
    Filter: tenant_id + clinic_id + doctor_id + slot_date (dual filter L1+L2).
    Deleted slots excluded (deleted_at IS NULL).

  get_busy_ranges → vitalia_appointment_clinic_map (start_time, end_time, status)
    Mirror columns added by migration 050 (T-BE-2).
    Filter: tenant_id + clinic_id + doctor_id + start_time::date (dual filter).
    Excludes CANCELLED (RN-6 — cancelled slots must not block availability).
    Excludes deleted rows (deleted_at IS NULL).

  list_active_doctors → vitalia_availability_slots DISTINCT doctor_id
    JOIN vitalia_doctors for real first_name/last_name (dual filter, no PHI beyond name).

HIPAA-lite: every query dual-filters tenant_id + clinic_id (hipaa-lite.md).
PHI: NO patient PHI in any query or result here. Availability = scheduling metadata only.

03-arch-be.md § 5 + D-B port pattern.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

import structlog
from sqlalchemy import bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.clinics.infrastructure.models.availability_slot_model import (
    VitaliaAvailabilitySlotModel,
)
from src.modules.vitalia.scheduling.domain.availability_check import TimeRange
from src.modules.vitalia.scheduling.persistence.models.appointment_clinic_map_model import (
    AppointmentClinicMapModel,
)

logger = structlog.get_logger()

# Appointment statuses that block a slot (all except CANCELLED — RN-6)
_BLOCKING_STATUSES: frozenset[str] = frozenset({"SCHEDULED", "CONFIRMED", "COMPLETED", "NO_SHOW"})


class AvailabilityQueryRepository:
    """Read-only implementation of AvailabilitySourcePort.

    All queries use SQLAlchemy 2.0 select() patterns (no session.query()).
    Dual filter applied on every method (tenant_id + clinic_id).
    """

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialise with SQLAlchemy async session.

        Args:
            session: Bound async DB session (injected by FastAPI dependency).
        """
        self._session = session

    async def get_working_hours(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        day: date,
    ) -> list[TimeRange]:
        """Return working-hour windows from vitalia_availability_slots.

        Reads materialized slots projected by AvailabilityProjectionService
        (clinics module). Does NOT import clinics domain directly — consumes
        the pre-projected table (D-B pattern, 03-arch-be.md § 4).

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).
            doctor_id: Doctor whose working blocks to read.
            day: Calendar date to query.

        Returns:
            List of TimeRange objects for working windows. Empty = no schedule.
        """
        stmt = (
            select(
                VitaliaAvailabilitySlotModel.start_ts,
                VitaliaAvailabilitySlotModel.end_ts,
            )
            .where(
                VitaliaAvailabilitySlotModel.tenant_id == tenant_id,
                VitaliaAvailabilitySlotModel.clinic_id == clinic_id,
                VitaliaAvailabilitySlotModel.doctor_id == doctor_id,
                VitaliaAvailabilitySlotModel.slot_date == day,
                VitaliaAvailabilitySlotModel.deleted_at.is_(None),
            )
            .order_by(VitaliaAvailabilitySlotModel.start_ts)
        )

        rows = (await self._session.execute(stmt)).all()

        logger.debug(
            "availability_working_hours_loaded",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            doctor_id=str(doctor_id),
            day=str(day),
            count=len(rows),
        )

        return [TimeRange(start=row.start_ts, end=row.end_ts) for row in rows]

    async def get_busy_ranges(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        day: date,
    ) -> list[TimeRange]:
        """Return booked appointment ranges from vitalia_appointment_clinic_map.

        Uses mirror columns (start_time, end_time, status) added in migration 050.
        Excludes CANCELLED appointments (RN-6: cancelled slots don't block).

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).
            doctor_id: Doctor whose booked slots to read.
            day: Calendar date to query.

        Returns:
            List of TimeRange objects for booked appointments (non-cancelled).
        """
        # Cast start_time::date for day-range query (mirror column is UTC datetime)
        stmt = (
            select(
                AppointmentClinicMapModel.start_time,
                AppointmentClinicMapModel.end_time,
            )
            .where(
                AppointmentClinicMapModel.tenant_id == tenant_id,
                AppointmentClinicMapModel.clinic_id == clinic_id,
                AppointmentClinicMapModel.doctor_id == doctor_id,
                # Filter to the requested calendar day (UTC)
                text("DATE(vitalia_appointment_clinic_map.start_time AT TIME ZONE 'UTC') = :day").bindparams(day=day),
                AppointmentClinicMapModel.status.notin_(["CANCELLED"]),
                AppointmentClinicMapModel.start_time.isnot(None),
                AppointmentClinicMapModel.end_time.isnot(None),
                AppointmentClinicMapModel.deleted_at.is_(None),
            )
            .order_by(AppointmentClinicMapModel.start_time)
        )

        rows = (await self._session.execute(stmt)).all()

        logger.debug(
            "availability_busy_ranges_loaded",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            doctor_id=str(doctor_id),
            day=str(day),
            count=len(rows),
        )

        return [
            TimeRange(start=row.start_time, end=row.end_time)
            for row in rows
            if row.start_time is not None and row.end_time is not None
        ]

    async def list_active_doctors(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> list[tuple[UUID, str]]:
        """Return (doctor_id, label) for doctors with slots in this clinic.

        Queries distinct doctor_ids from vitalia_availability_slots and JOINs
        vitalia_doctors to resolve the real full name.  Dual filter applied on
        BOTH tables (tenant_id + clinic_id — HIPAA-lite).

        Label format: COALESCE(NULLIF(TRIM(CONCAT(first_name, ' ', last_name)), ''),
        'Sin asignar') — matching the pattern used in AgendaGridRepositoryImpl
        (_GRID_PROJECTION L83-84).

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).

        Returns:
            List of (UUID, label_str) tuples with the doctor's real display name.
        """
        stmt = text(
            """
            SELECT
                slot.doctor_id,
                COALESCE(
                    NULLIF(TRIM(CONCAT(doc.first_name, ' ', doc.last_name)), ''),
                    'Sin asignar'
                ) AS doctor_label
            FROM (
                SELECT DISTINCT doctor_id
                FROM vitalia_availability_slots
                WHERE tenant_id = :tenant_id
                  AND clinic_id = :clinic_id
                  AND deleted_at IS NULL
            ) slot
            LEFT JOIN vitalia_doctors doc
                ON doc.id = slot.doctor_id
               AND doc.tenant_id = :tenant_id
               AND doc.deleted_at IS NULL
            ORDER BY doctor_label
            """
        ).bindparams(
            bindparam("tenant_id", value=tenant_id),
            bindparam("clinic_id", value=clinic_id),
        )

        rows = (await self._session.execute(stmt)).all()

        logger.debug(
            "availability_active_doctors_loaded",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            count=len(rows),
        )

        return [(row.doctor_id, row.doctor_label) for row in rows]

    async def get_service_day_strips(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        offer_id: UUID,
        day: date,
    ) -> list[tuple[UUID, str, list[TimeRange], list[TimeRange]]]:
        """Return per-doctor working/busy strips for ALL doctors of a service on a day.

        Composes existing readers — no new free/busy SQL.  The ONLY new query is
        the service→specialist link resolution below.

        Render set = doctors linked to the offer ∩ clinic-active doctors
        (dual-filtered tenant_id + clinic_id via list_active_doctors).  A
        cross-clinic or cross-tenant linked doctor is therefore excluded (no leak).
        When the service has no links, falls back to all clinic-active doctors.

        Args:
            tenant_id: Tenant scope (dual filter L1).
            clinic_id: Clinic scope (dual filter L2 — HIPAA-lite).
            offer_id: Service (offer) whose specialists to resolve.
            day: Calendar date to query.

        Returns:
            List of (doctor_id, label, working_ranges, busy_ranges) tuples,
            ordered by doctor label (from list_active_doctors).
        """
        # Only NEW SQL: resolve service → linked specialists (tenant-scoped, live links).
        link_stmt = text(
            "SELECT doctor_id FROM offer_service_specialist_links "
            "WHERE tenant_id = :tenant_id AND offer_id = :offer_id AND deleted_at IS NULL"
        ).bindparams(
            bindparam("tenant_id", value=tenant_id),
            bindparam("offer_id", value=offer_id),
        )
        linked_ids = {row.doctor_id for row in (await self._session.execute(link_stmt)).all()}

        active = await self.list_active_doctors(tenant_id=tenant_id, clinic_id=clinic_id)
        if linked_ids:
            # intersect preserves label-ordering + dual-filtered labels (cross-clinic excluded)
            render = [(did, label) for did, label in active if did in linked_ids]
        else:
            render = list(active)

        # ponytail: a clinic doctor with zero slots ever isn't in `active` → excluded even if
        #   linked; one with slots only on other days appears with empty strips. Per-day view.
        out: list[tuple[UUID, str, list[TimeRange], list[TimeRange]]] = []
        for doctor_id, label in render:
            working = await self.get_working_hours(
                tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id, day=day
            )
            busy = await self.get_busy_ranges(tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id, day=day)
            out.append((doctor_id, label, working, busy))

        logger.debug(
            "availability_service_day_strips_loaded",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            offer_id=str(offer_id),
            day=str(day),
            doctor_count=len(out),
        )
        return out
