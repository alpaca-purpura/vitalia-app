# cap: scheduling.mateo-agenda
"""SchedulingHoldService — book appointment with hold-status + TTL.

Called by create_appointment_service AFTER the appointment row exists:
1. mark_slot_confirmed(True) — prevents double-booking (hipaa-lite / RN-22)
2. set_hold(hold_pending_payment, now + TTL) — TTL from tenant_config
3. audit sync write (HIPAA: PHI-adjacent write = mandatory log)
4. growth event emit (fire-forget)

TTL: tenant_config.adrian_hold_ttl_minutes (default 30, NEVER hardcoded).

Per 03-arch § 7 + 05-guidelines + vitalia-fase2-adrian-canal-inbound T-BE-2.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.application.ports.scheduling_hold_port import SchedulingHoldPort

logger = structlog.get_logger()

_DEFAULT_HOLD_TTL_MINUTES = 30

__all__ = ["SchedulingHoldService"]


class SchedulingHoldService:
    """Application service: mark slot + set hold with TTL on appointment create.

    Injected into CreateAppointmentService when origin=proactivo_adrian (or any
    origin that requires a hold). For manual creates (Mateo walk_in), the
    hold_service is None and this service is not called.
    """

    def __init__(
        self,
        *,
        hold_port: SchedulingHoldPort,
        audit_writer: Any,
        growth_emitter: Any,
    ) -> None:
        """Initialize SchedulingHoldService.

        Args:
            hold_port: SchedulingHoldPort implementation (repo layer).
            audit_writer: AsyncAuditWriter — sync write (HIPAA mandate).
            growth_emitter: GrowthStudioEmitter — fire-forget telemetry.
        """
        self._port = hold_port
        self._audit = audit_writer
        self._growth = growth_emitter

    async def book_with_hold(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        slot_id: UUID,
        tenant_config: dict[str, Any],
        now: datetime,
    ) -> None:
        """Mark slot confirmed + set hold-pending-payment with TTL.

        Orchestration:
        1. mark_slot_confirmed(True) — atomic lock against double-booking
        2. set_hold(hold_pending_payment, now + TTL) — expiry from tenant_config
        3. audit sync write (HIPAA PHI-adjacent write)
        4. growth event emit (fire-forget)

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            appointment_id: Created appointment UUID (FK into clinic_map).
            slot_id: UUID of vitalia_availability_slots (to mark confirmed).
            tenant_config: Tenant JSONB config dict (reads adrian_hold_ttl_minutes).
            now: Current UTC datetime (for TTL calculation).
        """
        # TTL from config — NEVER hardcoded
        ttl_minutes: int = int(tenant_config.get("adrian_hold_ttl_minutes", _DEFAULT_HOLD_TTL_MINUTES))
        expires_at = now + timedelta(minutes=ttl_minutes)

        # Step 1: Mark availability slot as confirmed (anti double-booking)
        await self._port.mark_slot_confirmed(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            slot_id=slot_id,
            confirmed=True,
        )

        # Step 2: Set hold_pending_payment with TTL on clinic_map
        await self._port.set_hold(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            appointment_id=appointment_id,
            status="hold_pending_payment",
            expires_at=expires_at,
        )

        # Step 3: Audit sync write (HIPAA — PHI-adjacent write)
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=None,  # system action (sweep)
            action="appointment.hold_set",
            resource_type="appointment",
            resource_id=appointment_id,
            payload={
                "status": "hold_pending_payment",
                "ttl_minutes": ttl_minutes,
                # No PHI values in payload
            },
        )

        # Step 4: Growth event (fire-forget)
        await self._growth.emit_event(
            event_type="appointment_hold_set",
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            entity_id=appointment_id,
            user_id=None,
            props={"hold_status": "hold_pending_payment", "ttl_minutes": ttl_minutes},
        )

        logger.info(
            "appointment_hold_set",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            ttl_minutes=ttl_minutes,
        )
