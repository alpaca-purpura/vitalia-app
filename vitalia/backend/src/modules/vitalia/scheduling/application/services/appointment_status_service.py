# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Appointment Status Service — status transition + audit log + telemetry.

Rule (hipaa-lite.md § Regla cardinal):
  - Dual filter: tenant_id + clinic_id MANDATORY.
  - Audit log sync write with from_status + to_status BEFORE returning.
  - Cross-clinic: repo.get_by_id returns None → AppointmentNotFoundError (404).
  - Growth studio event fired after audit log (fire-forget OK for telemetry).

Usage:
    service = AppointmentStatusService(
        repo=repo,
        audit_writer=audit_writer,
        growth_emitter=growth_emitter,
    )
    await service.change_status(
        appointment_id=appt_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        new_status="CANCELLED",
        reason="Paciente canceló",
        user_id=user_id,
    )
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.domain.exceptions import AppointmentNotFoundError

logger = structlog.get_logger()


class AppointmentStatusService:
    """Application service: change appointment status with audit log + telemetry.

    Thin orchestration: load → audit log (from/to) → persist → emit telemetry.

    PHI obligations (hipaa-lite.md):
    1. Load via dual filter (repo enforces tenant_id + clinic_id).
    2. Audit log written sync with from_status/to_status (transition trace).
    3. Growth studio event emitted after audit (fire-forget).
    4. Cross-clinic returns AppointmentNotFoundError (not data leak).
    """

    def __init__(
        self,
        *,
        repo: Any,
        audit_writer: Any,
        growth_emitter: Any,
    ) -> None:
        """Initialize AppointmentStatusService.

        Args:
            repo: Implements get_by_id(appt_id, tenant_id, clinic_id) and
                  update_status(appt_id, tenant_id, clinic_id, new_status, reason).
            audit_writer: AsyncAuditWriter — sync write before response.
            growth_emitter: GrowthStudioEmitter — fire-forget UX telemetry.
        """
        self._repo = repo
        self._audit = audit_writer
        self._growth = growth_emitter

    async def change_status(
        self,
        *,
        appointment_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        new_status: str,
        reason: str | None,
        user_id: UUID,
    ) -> dict[str, Any]:
        """Change appointment status with audit log and telemetry.

        Args:
            appointment_id: Target appointment UUID.
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID for dual filter.
            new_status: Target status string (CONFIRMED, CANCELLED, NO_SHOW, etc.).
            reason: Optional cancellation / change reason.
            user_id: Actor user UUID.

        Returns:
            Updated appointment detail dict.

        Raises:
            AppointmentNotFoundError: If appointment not found for this
                tenant+clinic scope.
        """
        current = await self._repo.get_by_id(
            appointment_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        if current is None:
            raise AppointmentNotFoundError(
                appointment_id=appointment_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
            )

        from_status = current.get("status", "UNKNOWN")

        # Persist status change
        updated = await self._repo.update_status(
            appointment_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            new_status=new_status,
            reason=reason,
        )

        # T-BE-4: Propagate status to clinic_map mirror column.
        # Required so the EXCLUDE constraint WHERE (status <> 'CANCELLED')
        # allows re-booking after a CANCELLED appointment frees its slot.
        await self._repo.update_clinic_map_status(
            appointment_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            new_status=new_status,
        )

        # Audit log sync write (HIPAA mandate — status change is PHI-adjacent mutation)
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="appointment.status_change",
            resource_type="appointment",
            resource_id=appointment_id,
            payload={
                "from_status": from_status,
                "to_status": new_status,
                "reason": reason,
            },
        )

        # Growth studio telemetry (fire-forget — not mandatory sync like audit_log)
        await self._growth.emit_event(
            event_type=f"appointment_status_{new_status.lower()}",
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            entity_id=appointment_id,
            user_id=user_id,
            props={
                "from_status": from_status,
                "to_status": new_status,
            },
        )

        logger.info(
            "appointment_status_changed",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            from_status=from_status,
            to_status=new_status,
        )

        return updated
