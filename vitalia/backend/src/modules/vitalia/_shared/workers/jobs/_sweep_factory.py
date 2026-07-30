# cap: scheduling.mateo-agenda
"""Factory: build HoldExpirySweepService with production dependencies.

Centralized DI wiring for the sweep job and routes (keeps job thin).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.scheduling.application.services.hold_expiry_sweep_service import (
    HoldExpirySweepService,
)
from src.modules.vitalia.scheduling.infrastructure.repositories.scheduling_hold_repository import (
    SchedulingHoldRepository,
)


class _StubActivityEmitter:
    """Minimal activity emitter stub until activity module is wired."""

    async def emit(self, *, tenant_id, event_type, entity_id, props=None) -> None:  # type: ignore[type-arg]
        import structlog  # noqa: PLC0415

        structlog.get_logger().info(
            "activity_event_emitted",
            tenant_id=str(tenant_id),
            event_type=event_type,
            entity_id=str(entity_id),
        )


class _StubAuditWriter:
    """Minimal audit writer stub for sweep context (no PHI in sweep activity)."""

    async def write(  # type: ignore[type-arg]
        self,
        *,
        tenant_id,
        clinic_id=None,
        user_id=None,
        action,
        resource_type,
        resource_id,
        payload=None,
    ) -> None:
        import structlog  # noqa: PLC0415

        structlog.get_logger().info(
            "audit_log_write",
            tenant_id=str(tenant_id),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
        )


class _StubAppointmentRepo:
    """Minimal appointment repo for sweep: cancel + slot lookup.

    ponytail: real implementation defers to an existing scheduling repo method
    once the cancel_appointment path is confirmed. For T-BE-2 the sweep tests
    use mock repos; this stub is the ARQ runtime fallback.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_slot_id_for_appointment(self, *, appointment_id, tenant_id):  # type: ignore[type-arg]
        """Look up the availability_slot linked to an appointment by (doctor_id, slot_iso)."""
        from sqlalchemy import text  # noqa: PLC0415

        result = await self._session.execute(
            text(
                "SELECT vas.id FROM vitalia_availability_slots vas"
                " JOIN vitalia_appointments va ON"
                " va.doctor_id = vas.doctor_id AND va.slot_iso = vas.slot_iso"
                " WHERE va.id = :appointment_id AND va.tenant_id = :tenant_id"
                " LIMIT 1"
            ),
            {
                "appointment_id": str(appointment_id),
                "tenant_id": str(tenant_id),
            },
        )
        row = result.fetchone()
        if row is None:
            return None
        from uuid import UUID  # noqa: PLC0415

        return UUID(str(row[0]))

    async def cancel_appointment(self, *, appointment_id, tenant_id, reason="hold_expired"):  # type: ignore[type-arg]
        """Mark appointment as expired (soft status update)."""
        from sqlalchemy import text  # noqa: PLC0415

        await self._session.execute(
            text(
                "UPDATE vitalia_appointments"
                " SET status = 'EXPIRED', updated_at = NOW()"
                " WHERE id = :appointment_id AND tenant_id = :tenant_id"
                " AND status NOT IN ('COMPLETED', 'CANCELLED', 'EXPIRED')"
            ),
            {
                "appointment_id": str(appointment_id),
                "tenant_id": str(tenant_id),
            },
        )


def build_sweep_service(*, session: AsyncSession) -> HoldExpirySweepService:
    """Build HoldExpirySweepService with real dependencies.

    Args:
        session: AsyncSession (per-request scope).

    Returns:
        HoldExpirySweepService wired with hold port + stubs.
    """
    return HoldExpirySweepService(
        hold_port=SchedulingHoldRepository(session=session),
        appointment_repo=_StubAppointmentRepo(session=session),
        audit_writer=_StubAuditWriter(),
        activity_emitter=_StubActivityEmitter(),
    )
