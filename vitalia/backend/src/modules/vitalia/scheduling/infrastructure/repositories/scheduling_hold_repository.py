# cap: scheduling.mateo-agenda
"""SchedulingHoldRepository — implements SchedulingHoldPort (T-BE-2 / RN-26).

Writes to:
  - vitalia_availability_slots.has_confirmed_appointment (mark_slot_confirmed)
  - vitalia_appointment_clinic_map.hold_status + hold_expires_at (set_hold)
  - Read from vitalia_appointment_clinic_map (list_expired_holds)

HIPAA-lite dual filter: tenant_id + clinic_id on ALL write queries.
Sweep (list_expired_holds) filters by tenant_id only (all clinics per tenant).

Per 03-arch § 6 + vitalia-fase2-adrian-canal-inbound T-BE-2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.scheduling.application.ports.scheduling_hold_port import SchedulingHoldPort

logger = structlog.get_logger()

__all__ = ["SchedulingHoldRepository"]

# Zero UUID sentinel used by sweep when clinic_id is not needed
_ZERO_UUID = UUID("00000000-0000-0000-0000-000000000000")


class SchedulingHoldRepository(SchedulingHoldPort):
    """Async SQLA 2.0 repository for slot hold operations.

    Implements SchedulingHoldPort.
    Session injected at construction (per-request DI pattern).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize SchedulingHoldRepository.

        Args:
            session: AsyncSession from DI (per-request scope).
        """
        self._session = session

    async def mark_slot_confirmed(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        slot_id: UUID,
        confirmed: bool,
    ) -> None:
        """Update vitalia_availability_slots.has_confirmed_appointment.

        Dual filter: tenant_id + clinic_id (skip clinic filter if sentinel zero UUID —
        used by sweep which operates across all clinics per tenant).

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID or zero UUID sentinel (sweep context).
            slot_id: UUID of the vitalia_availability_slots row.
            confirmed: True = booked; False = released.
        """
        # Use raw SQL UPDATE for simplicity (table not mapped via ORM in scheduling module)
        # clinic_id filter skipped for sweep context (zero UUID sentinel)
        await self._session.execute(
            text(
                "UPDATE vitalia_availability_slots"
                " SET has_confirmed_appointment = :confirmed"
                " WHERE id = :slot_id AND tenant_id = :tenant_id"
                + (" AND clinic_id = :clinic_id" if clinic_id != _ZERO_UUID else "")
            ),
            {
                "confirmed": confirmed,
                "slot_id": str(slot_id),
                "tenant_id": str(tenant_id),
                **({} if clinic_id == _ZERO_UUID else {"clinic_id": str(clinic_id)}),
            },
        )

        logger.info(
            "slot_confirmed_updated",
            slot_id=str(slot_id),
            tenant_id=str(tenant_id),
            confirmed=confirmed,
        )

    async def set_hold(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        status: str,
        expires_at: datetime,
    ) -> None:
        """Update hold_status + hold_expires_at on vitalia_appointment_clinic_map.

        Dual filter: tenant_id + clinic_id (PK is appointment_id, FK binding is per-clinic).

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID.
            appointment_id: UUID (PK of vitalia_appointment_clinic_map).
            status: 'hold_pending_payment' | 'confirmed' | 'expired'.
            expires_at: UTC datetime when hold expires.
        """
        await self._session.execute(
            text(
                "UPDATE vitalia_appointment_clinic_map"
                " SET hold_status = :status, hold_expires_at = :expires_at"
                " WHERE appointment_id = :appointment_id"
                " AND tenant_id = :tenant_id"
                " AND clinic_id = :clinic_id"
            ),
            {
                "status": status,
                "expires_at": expires_at.isoformat(),
                "appointment_id": str(appointment_id),
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
            },
        )

        logger.info(
            "appointment_hold_status_set",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            status=status,
        )

    async def list_expired_holds(
        self,
        *,
        tenant_id: UUID,
        now: datetime,
    ) -> list[UUID]:
        """Return appointment_ids with expired holds (not yet released).

        Filters: hold_status='hold_pending_payment' AND hold_expires_at <= now.
        Per-tenant sweep (all clinics).

        Args:
            tenant_id: Root tenant UUID.
            now: Current UTC datetime (expiry threshold).

        Returns:
            List of appointment UUIDs.
        """
        result = await self._session.execute(
            text(
                "SELECT appointment_id FROM vitalia_appointment_clinic_map"
                " WHERE tenant_id = :tenant_id"
                " AND hold_status = 'hold_pending_payment'"
                " AND hold_expires_at <= :now"
                " AND deleted_at IS NULL"
            ),
            {
                "tenant_id": str(tenant_id),
                "now": now.isoformat(),
            },
        )

        rows = result.fetchall()
        return [UUID(str(row[0])) for row in rows]
