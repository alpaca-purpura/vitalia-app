# cap: scheduling.mateo-agenda
"""SchedulingHoldPort — abstract interface for slot hold + sweep operations.

Implements the port pattern (DDD Inside-Out):
- Domain defines the contract (this ABC)
- Infrastructure implements it (SchedulingHoldRepository)
- Application consumes it (SchedulingHoldService, HoldExpirySweepService)

Dual filter: EVERY method receives tenant_id + clinic_id (hipaa-lite.md).

Per 03-arch § 6 + vitalia-fase2-adrian-canal-inbound T-BE-2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

__all__ = ["SchedulingHoldPort"]


class SchedulingHoldPort(ABC):
    """Abstract port for availability slot hold operations.

    Implementations:
    - vitalia/.../scheduling/infrastructure/repositories/scheduling_hold_repository.py

    All methods are async and dual-filtered (tenant_id + clinic_id).
    """

    @abstractmethod
    async def mark_slot_confirmed(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        slot_id: UUID,
        confirmed: bool,
    ) -> None:
        """Set has_confirmed_appointment on vitalia_availability_slots.

        Args:
            tenant_id: Root tenant UUID (dual filter).
            clinic_id: Clinic UUID (dual filter).
            slot_id: UUID of the vitalia_availability_slots row.
            confirmed: True = appointment booked; False = hold released.
        """

    @abstractmethod
    async def set_hold(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        status: str,
        expires_at: datetime,
    ) -> None:
        """Set hold_status + hold_expires_at on vitalia_appointment_clinic_map.

        Args:
            tenant_id: Root tenant UUID (dual filter).
            clinic_id: Clinic UUID (dual filter).
            appointment_id: UUID of the appointment (PK of clinic_map).
            status: Hold status string. Valid: 'hold_pending_payment' | 'confirmed' | 'expired'.
            expires_at: UTC datetime when the hold expires.
        """

    @abstractmethod
    async def list_expired_holds(
        self,
        *,
        tenant_id: UUID,
        now: datetime,
    ) -> list[UUID]:
        """Return appointment_ids where hold has expired (not yet released).

        Filters: hold_status='hold_pending_payment' AND hold_expires_at <= now.
        Dual filter by tenant_id only (sweep is per-tenant, all clinics).

        Args:
            tenant_id: Root tenant UUID.
            now: Current UTC datetime (for expiry comparison).

        Returns:
            List of appointment UUIDs whose holds are expired.
        """
