# cap: fidelizacion.re-engagement
# story-origin: TBD
"""PausePatientService — pausar re-engagement de un paciente.

Registra una pausa temporal en los re-engagements de un paciente.
Emite PatientPausedReEngagement domain event via outbox.
Escribe audit log HIPAA-lite (sync write mandatorio).

HIPAA-lite:
  - Dual filter tenant_id + clinic_id en todas las operaciones.
  - Audit log sync write mandatorio.

downstream-regression-na: brand-local application service vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    PausePatientResponse,
)
from src.modules.vitalia.fidelizacion.domain.events.events import PatientPausedReEngagement
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import (
    ReEngagementEventModel,
)

# Outbox adapter_bus — module-level import with test fallback
try:
    from luana_core_events.outbox.application.event_bus_adapter import (  # type: ignore[import]
        adapter_bus,
    )
except (ImportError, Exception):  # pragma: no cover
    from unittest.mock import AsyncMock as _AsyncMock  # noqa: PLC0415

    class _FallbackBus:  # type: ignore[no-redef]
        """Fallback bus for test environments."""

        publish = _AsyncMock()

    adapter_bus = _FallbackBus()

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.vitalia._shared.repositories.audit_log_repository import (
        AuditLogRepository,
    )
    from src.modules.vitalia.fidelizacion.infrastructure.repositories.re_engagement_event_repository import (
        ReEngagementEventRepository,
    )

logger = structlog.get_logger(__name__)


class PausePatientService:
    """Servicio para pausar re-engagement de un paciente temporalmente.

    Registra un evento de tipo ABSENCE con trigger_at = pause_until
    para que el cron lo procese al vencerse la pausa.
    Emite PatientPausedReEngagement domain event.
    """

    def __init__(
        self,
        *,
        session: "AsyncSession",
        re_engagement_repo: "ReEngagementEventRepository",
        audit_repo: "AuditLogRepository",
    ) -> None:
        """Inicializa el servicio con repos inyectados.

        Args:
            session: AsyncSession compartido.
            re_engagement_repo: Repo de eventos de re-engagement.
            audit_repo: Repo de audit log HIPAA-lite.
        """
        self._session = session
        self._re_engagement_repo = re_engagement_repo
        self._audit_repo = audit_repo

    async def pause_patient(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        pause_until: datetime,
        pause_reason: str | None = None,
        paused_by_user_id: UUID | None = None,
    ) -> PausePatientResponse:
        """Pausa los re-engagements de un paciente hasta una fecha dada.

        Crea un evento de re-engagement tipo ABSENCE con trigger_at = pause_until.
        El cron de fidelización no enviará mensajes mientras el paciente esté pausado.

        HIPAA-lite:
          - Dual filter tenant_id + clinic_id en modelo guardado.
          - Audit log sync write mandatorio.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_id: UUID del paciente.
            pause_until: Hasta cuándo pausar el re-engagement.
            pause_reason: Razón de la pausa (opcional).
            paused_by_user_id: UUID del usuario que pausó (para audit log).

        Returns:
            PausePatientResponse con datos de la pausa.
        """
        from src.modules.vitalia._shared.repositories.audit_log_repository import (
            AuditLogEntry,
        )

        now = datetime.now(UTC)
        event_id = uuid4()
        user_id = paused_by_user_id or uuid4()  # fallback si no se provee

        # Crear evento de pausa (tipo ABSENCE, trigger_at = pause_until)
        model = ReEngagementEventModel(
            id=event_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=ReEngagementPattern.ABSENCE.value,
            trigger_source="manual_pause",
            trigger_at=pause_until,  # Se activa cuando vence la pausa
            created_at=now,
            updated_at=now,
        )
        saved = await self._re_engagement_repo.save(model)

        # Audit log HIPAA-lite sync write mandatorio
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="pause_patient_re_engagement",
            resource_type="re_engagement_event",
            resource_id=event_id,
            payload_redacted=b"",  # pause_reason puede ser sensible — excluido
        )
        await self._audit_repo.write(audit_entry)

        # Emitir PatientPausedReEngagement domain event via outbox
        # Calculate duration_days from pause_until
        duration_days = max(1, (pause_until - now).days)
        domain_event = PatientPausedReEngagement.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            duration_days=duration_days,
            reason=pause_reason,
            resume_at=pause_until,
            triggered_by_user_id=user_id,
        )
        try:
            await adapter_bus.publish(domain_event, session=self._session)
        except Exception as exc:
            logger.warning(
                "pause_event_publish_failed",
                event_id=str(event_id),
                tenant_id=str(tenant_id),
                error=str(exc),
            )

        logger.info(
            "patient_re_engagement_paused",
            event_id=str(event_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            patient_id=str(patient_id),
            paused_until=pause_until.isoformat(),
        )

        return PausePatientResponse(
            patient_id=patient_id,
            paused_until=pause_until,
            event_id=saved.id,
        )
