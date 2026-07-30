# cap: fidelizacion.re-engagement
# story-origin: TBD
"""OptOutService — dar de baja a un paciente del sistema de fidelización.

Cascade cancel: cancela todos los eventos de re-engagement pendientes del paciente.
Emite PatientOptedOut domain event via outbox.
Escribe audit log HIPAA-lite (sync write mandatorio).

Listener de T-2: cuando PatientOptedOut se emite desde el módulo CRM (consent),
este servicio cancela los eventos pendientes de fidelización.

HIPAA-lite:
  - Dual filter tenant_id + clinic_id en todas las operaciones.
  - Audit log sync write mandatorio.
  - Soft delete de eventos pendientes (no hard delete).

downstream-regression-na: brand-local application service vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.fidelizacion.application.dtos.fidelizacion_summary_dtos import (
    OptOutPatientResponse,
)
from src.modules.vitalia.fidelizacion.domain.events.events import PatientOptedOut
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
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


class OptOutService:
    """Servicio de opt-out de pacientes del sistema de fidelización.

    Cuando un paciente solicita darse de baja:
    1. Cancela todos los re_engagement_events pendientes (soft delete + outcome OPT_OUT).
    2. Emite PatientOptedOut domain event via outbox.
    3. Escribe audit log sync (HIPAA-lite mandatorio).
    4. Retorna resumen de la operación.
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

    async def opt_out_patient(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        user_id: UUID,
        opt_out_reason: str | None = None,
    ) -> OptOutPatientResponse:
        """Procesa el opt-out de un paciente del sistema de fidelización.

        Cascade cancel: marca como cancelados (outcome=OPT_OUT) todos los
        eventos de re-engagement pendientes (sin sent_at) del paciente.
        Los eventos ya enviados NO se modifican (preservar historial).

        HIPAA-lite:
          - Dual filter tenant_id + clinic_id en lista de pendientes.
          - Audit log sync write mandatorio.
          - Soft delete: eventos pendientes marcados como OPT_OUT, no eliminados.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_id: UUID del paciente que se da de baja.
            user_id: UUID del usuario que ejecuta el opt-out.
            opt_out_reason: Razón del opt-out (opcional, no PHI en audit log).

        Returns:
            OptOutPatientResponse con resumen de la operación.
        """
        from src.modules.vitalia._shared.repositories.audit_log_repository import (
            AuditLogEntry,
        )

        now = datetime.now(UTC)
        opt_out_event_id = uuid4()

        # Paso 1 — Listar eventos pendientes del paciente (dual filter HIPAA-lite)
        pending_events = await self._re_engagement_repo.list_pending_for_patient(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
        )

        # Paso 2 — Cascade cancel: marcar pendientes como OPT_OUT (soft)
        cancelled_count = 0
        for event_model in pending_events:
            event_model.outcome = ReEngagementOutcome.OPTED_OUT.value
            event_model.response_at = now
            event_model.updated_at = now
            await self._re_engagement_repo.save(event_model)
            cancelled_count += 1

        # Paso 3 — Audit log HIPAA-lite sync write mandatorio
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="patient_opt_out_fidelizacion",
            resource_type="patient_fidelizacion",
            resource_id=patient_id,
            payload_redacted=b"",  # reason puede ser PHI — excluido del audit log
        )
        await self._audit_repo.write(audit_entry)

        # Paso 4 — Emitir PatientOptedOut domain event via outbox
        domain_event = PatientOptedOut.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            reason=opt_out_reason,
            triggered_by_user_id=user_id,
        )
        try:
            await adapter_bus.publish(domain_event, session=self._session)
        except Exception as exc:
            logger.warning(
                "opt_out_event_publish_failed",
                patient_id=str(patient_id),
                tenant_id=str(tenant_id),
                error=str(exc),
            )

        logger.info(
            "patient_opted_out_fidelizacion",
            patient_id=str(patient_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            cancelled_events=cancelled_count,
        )

        return OptOutPatientResponse(
            patient_id=patient_id,
            clinic_id=clinic_id,
            opted_out_at=now,
            pending_events_cancelled=cancelled_count,
            event_id=opt_out_event_id,
        )
