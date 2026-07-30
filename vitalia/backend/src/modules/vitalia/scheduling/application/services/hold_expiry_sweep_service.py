# cap: scheduling.mateo-agenda
"""HoldExpirySweepService — release expired appointment holds (SC-10 / V-FN-10).

Idempotent sweep job:
1. list_expired_holds(tenant_id, now) → [appointment_id, ...]
2. For each expired hold:
   a. get_slot_id_for_appointment(appointment_id) → slot_id
   b. cancel_appointment(appointment_id) → status=expired
   c. mark_slot_confirmed(slot_id, confirmed=False) → slot free
   d. emit activity event to inbox (NON-PHI)
3. Returns count of released holds.

Coordinates with engine verify_pending_bookings (no duplication):
- Engine worker reconciles provider hold status (external booking provider side)
- This sweep covers the BRAND-LOCAL lane (vitalia_appointment_clinic_map holds
  created by proactivo_adrian flow) — orthogonal, no overlap.

Per 03-arch § 7 + vitalia-fase2-adrian-canal-inbound T-BE-2 SC-10.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.application.ports.scheduling_hold_port import SchedulingHoldPort

logger = structlog.get_logger()

__all__ = ["HoldExpirySweepService"]


class HoldExpirySweepService:
    """Application service: idempotent hold expiry sweep.

    Called by ARQ worker (hold_expiry_sweep_job) on a schedule.
    Also usable directly in tests (no ARQ dependency here).
    """

    def __init__(
        self,
        *,
        hold_port: SchedulingHoldPort,
        appointment_repo: Any,
        audit_writer: Any,
        activity_emitter: Any,
    ) -> None:
        """Initialize HoldExpirySweepService.

        Args:
            hold_port: SchedulingHoldPort implementation.
            appointment_repo: Repo with cancel_appointment() + get_slot_id_for_appointment().
            audit_writer: AsyncAuditWriter — sync write (HIPAA).
            activity_emitter: Activity emitter for inbox glass-box (NON-PHI).
        """
        self._port = hold_port
        self._appointments = appointment_repo
        self._audit = audit_writer
        self._activity = activity_emitter

    async def sweep_expired(
        self,
        *,
        tenant_id: UUID,
        now: datetime,
    ) -> int:
        """Release all expired holds for a tenant.

        Idempotent: if list_expired_holds returns empty, does nothing.

        Args:
            tenant_id: Root tenant UUID (sweep is per-tenant).
            now: Current UTC datetime.

        Returns:
            Count of released holds.
        """
        expired: list[UUID] = await self._port.list_expired_holds(
            tenant_id=tenant_id,
            now=now,
        )

        if not expired:
            return 0

        released = 0
        for appointment_id in expired:
            try:
                await self._release_one(
                    tenant_id=tenant_id,
                    appointment_id=appointment_id,
                )
                released += 1
            except Exception:  # noqa: BLE001
                logger.exception(
                    "hold_expiry_sweep_single_failed",
                    appointment_id=str(appointment_id),
                    tenant_id=str(tenant_id),
                )
                # Continue with next — idempotent: partial success is fine

        logger.info(
            "hold_expiry_sweep_complete",
            tenant_id=str(tenant_id),
            released=released,
            total_expired=len(expired),
        )

        return released

    async def _release_one(
        self,
        *,
        tenant_id: UUID,
        appointment_id: UUID,
    ) -> None:
        """Release a single expired hold.

        a. Lookup slot_id for appointment
        b. Cancel appointment (status → expired)
        c. Release slot (has_confirmed_appointment=False)
        d. Emit activity event (NON-PHI)
        """
        # a. Find the slot linked to this appointment
        slot_id: UUID | None = await self._appointments.get_slot_id_for_appointment(
            appointment_id=appointment_id,
            tenant_id=tenant_id,
        )

        # b. Cancel appointment (soft status change, no hard delete)
        await self._appointments.cancel_appointment(
            appointment_id=appointment_id,
            tenant_id=tenant_id,
            reason="hold_expired",
        )

        # c. Release availability slot (only if we know the slot_id)
        if slot_id is not None:
            # ponytail: clinic_id not required here because slot_id is globally unique
            # per vitalia_availability_slots (UUID PK) and we have tenant_id for filter.
            # The port accepts clinic_id=None for sweep context (set to zero UUID sentinel).
            from uuid import UUID as _UUID  # noqa: PLC0415

            _ZERO = _UUID("00000000-0000-0000-0000-000000000000")
            await self._port.mark_slot_confirmed(
                tenant_id=tenant_id,
                clinic_id=_ZERO,  # sentinel: bypass clinic filter for sweep
                slot_id=slot_id,
                confirmed=False,
            )

        # d. Activity event for inbox (NON-PHI — only IDs)
        await self._activity.emit(
            tenant_id=tenant_id,
            event_type="hold_expired",
            entity_id=appointment_id,
            props={"reason": "hold_ttl_elapsed"},
        )
