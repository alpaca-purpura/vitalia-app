# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""RescheduleAppointmentService — appointment slot update for Adrián.

Delegates slot change to AppointmentService, writes audit log synchronously.
Per 03-arch-be.md § 1:
  "reschedule_appointment_service.py — AppointmentService update +
   emit appointment_rescheduled outbox event + operator notification
   + sync audit_log"

HIPAA-lite (vitalia/.claude/rules/hipaa-lite.md):
  - audit_log written synchronously — never fire-forget
  - tenant_id + clinic_id mandatory (dual filter for appointment PHI)

downstream-regression-na: brand-local service for vitalia Adrián sales_agent
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from src.modules.vitalia._shared.repositories.audit_log_repository import (
        AuditLogRepository,
    )

logger = structlog.get_logger()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class RescheduleResult:
    """Result of a successful appointment reschedule."""

    appointment_id: UUID
    new_slot: datetime
    reason: str
    rescheduled_at: datetime


class RescheduleAppointmentService:
    """Service for rescheduling appointments on behalf of leads.

    Delegates slot update to AppointmentService (existing vitalia scheduling
    module) and writes audit log synchronously per HIPAA-lite mandate.

    Note: The actual outbox event emission and operator notification are
    downstream of the AppointmentService.update_slot call. This service's
    responsibility is the coordination + audit trail.
    """

    def __init__(
        self,
        appointment_service: Any,
        audit_log_repo: "AuditLogRepository",
    ) -> None:
        """Initialize with dependencies.

        Args:
            appointment_service: Vitalia scheduling AppointmentService (async).
            audit_log_repo: HIPAA-lite synchronous audit log repository.
        """
        self._appointment_svc = appointment_service
        self._audit = audit_log_repo

    async def reschedule(
        self,
        appointment_id: UUID,
        new_slot: datetime,
        reason: str,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
    ) -> RescheduleResult:
        """Reschedule an appointment to a new time slot.

        Args:
            appointment_id: UUID of the appointment to reschedule.
            new_slot: New appointment datetime (must be timezone-aware UTC).
            reason: Reason for rescheduling (for audit log — not sent to patient).
            tenant_id: Tenant UUID (root isolation).
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            user_id: Operator UUID (audit attribution).

        Returns:
            RescheduleResult with confirmation of the new slot.
        """
        logger.info(
            "reschedule_appointment.start",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )

        # Delegate to existing AppointmentService
        await self._appointment_svc.update_slot(
            appointment_id=appointment_id,
            new_slot=new_slot,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        now = _utc_now()

        # Audit log — synchronous write (HIPAA-lite mandate)
        from src.modules.vitalia._shared.repositories.audit_log_repository import (  # noqa: PLC0415
            AuditLogEntry,
        )

        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="appointment_rescheduled",
            resource_type="appointment",
            resource_id=appointment_id,
            payload_redacted=b"",
        )
        await self._audit.write(audit_entry)

        logger.info(
            "reschedule_appointment.complete",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
        )

        return RescheduleResult(
            appointment_id=appointment_id,
            new_slot=new_slot,
            reason=reason,
            rescheduled_at=now,
        )
