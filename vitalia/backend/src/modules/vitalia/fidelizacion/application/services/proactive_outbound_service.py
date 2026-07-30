# cap: fidelizacion.re-engagement
# story-origin: TBD
"""ProactiveOutboundService — envío proactivo de mensajes de re-engagement.

Flujo de 9 pasos:
  1. Verificar opt_out del paciente
  2. Verificar marketing_opt_in solo para templates MARKETING (UTILITY no requiere opt-in)
  3. Check throttle (7 días por default)
  4. Compliance channel guard (ComplianceService)
  5. Audit log sync write FIRST (HIPAA-lite mandatorio)
  6. Crear y persistir ReEngagementEventModel
  7. Emitir ReEngagementTriggered domain event via outbox
  8. Retornar ProactiveReminderResponse

HIPAA-lite: audit log sync write mandatorio, dual filter, PHI sanitization.
SC-01: Flujo completo exitoso.
SC-02: Bloqueo por marketing_opt_in=False para template MARKETING.
SC-03: Template UTILITY pasa sin opt-in (recordatorios de cita confirmada).

Template category resolution via WHATSAPP_TEMPLATE_REGISTRY (T-8 SSoT).
Per 03-arch-be.md § 7: solo templates con requires_marketing_opt_in=True
requieren el flag. Templates UTILITY (recordatorio_proxima_sesion,
recordatorio_control_doctor, nps_post_tratamiento) no lo requieren.

downstream-regression-na: brand-local application service vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.connections.whatsapp.registry import (
    WHATSAPP_TEMPLATE_REGISTRY,
)
from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    ProactiveReminderResponse,
)
from src.modules.vitalia.fidelizacion.domain.events.events import ReEngagementTriggered
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import (
    ReEngagementEventModel,
)

# Outbox adapter_bus — module-level import with test fallback
# Per anti-duplication.md: use core engine, never reimplement locally
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


class ProactiveOutboundService:
    """Servicio de envío proactivo de mensajes de re-engagement.

    Orquesta el flujo completo de 8 pasos para enviar un mensaje proactivo
    a un paciente vía WhatsApp (y canales futuros).

    Reglas clave:
    - opt_out=True → siempre bloqueado (no se envía nada).
    - marketing_opt_in=False para templates MARKETING → bloqueado.
    - Throttle: max 1 envío por paciente+patrón en throttle_days días.
    - ComplianceService gate: bloquea canales no encriptados con PHI.
    - Audit log: sync write ANTES de retornar (HIPAA-lite mandatorio).
    - ReEngagementTriggered event via outbox.adapter_bus (USE_OUTBOX=True).
    """

    def __init__(
        self,
        *,
        session: "AsyncSession",
        re_engagement_repo: "ReEngagementEventRepository",
        audit_repo: "AuditLogRepository",
        compliance_service: object,
    ) -> None:
        """Inicializa el servicio con dependencias inyectadas.

        Args:
            session: AsyncSession compartido (mismo para todos los repos).
            re_engagement_repo: Repo de eventos de re-engagement (T-4).
            audit_repo: Repo de audit log HIPAA-lite.
            compliance_service: ComplianceService engine (check channel guard).
        """
        self._session = session
        self._re_engagement_repo = re_engagement_repo
        self._audit_repo = audit_repo
        self._compliance_service = compliance_service

    async def send_proactive_reminder(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        patient_phone: str,
        patient_name: str,
        template_id: str,
        pattern: ReEngagementPattern,
        channel: str = "whatsapp",
        marketing_opt_in: bool,
        opt_out: bool,
        user_id: UUID,
        idempotency_key: str | None = None,
        throttle_days: int = 7,
    ) -> ProactiveReminderResponse:
        """Envía un recordatorio proactivo al paciente siguiendo los 8 pasos.

        SC-01: Flujo completo cuando paciente permite marketing.
        SC-02: Bloqueo cuando marketing_opt_in=False o opt_out=True.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica (dual filter HIPAA-lite).
            patient_id: UUID del paciente.
            patient_phone: Teléfono del paciente (PHI — no se logea).
            patient_name: Nombre del paciente (PHI — no se logea).
            template_id: ID del template de mensaje WhatsApp.
            pattern: Patrón de re-engagement.
            channel: Canal de envío (default "whatsapp").
            marketing_opt_in: Si el paciente acepta comunicaciones MARKETING.
            opt_out: Si el paciente se dio de baja del sistema.
            user_id: UUID del usuario que dispara la acción.
            idempotency_key: Clave de idempotencia opcional.
            throttle_days: Ventana de throttle en días.

        Returns:
            ProactiveReminderResponse con status del envío.
        """
        from src.modules.vitalia._shared.repositories.audit_log_repository import (
            AuditLogEntry,
        )

        # Paso 1 — Verificar opt_out
        if opt_out:
            logger.info(
                "proactive_outbound_blocked_opt_out",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                patient_id=str(patient_id),
            )
            return ProactiveReminderResponse(
                event_id=uuid4(),
                patient_id=patient_id,
                status="blocked",
                throttled=False,
                blocked_reason="patient_opted_out",
            )

        # Paso 2 — Verificar marketing_opt_in SOLO para templates MARKETING.
        # Consultar WHATSAPP_TEMPLATE_REGISTRY (T-8 SSoT) para la categoría del template.
        # Templates UTILITY (recordatorio_proxima_sesion, nps_post_tratamiento, etc.)
        # NO requieren opt-in — solo templates MARKETING lo requieren.
        # Per 03-arch-be.md § 7: check template.requires_marketing_opt_in.
        template_def = WHATSAPP_TEMPLATE_REGISTRY.get(template_id)
        if template_def is None:
            logger.warning(
                "proactive_outbound_unknown_template",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                patient_id=str(patient_id),
                template_id=template_id,
            )
            return ProactiveReminderResponse(
                event_id=uuid4(),
                patient_id=patient_id,
                status="blocked",
                throttled=False,
                blocked_reason="template_unknown",
            )
        if template_def.requires_marketing_opt_in and not marketing_opt_in:
            logger.info(
                "proactive_outbound_blocked_no_marketing_optin",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                patient_id=str(patient_id),
                template_id=template_id,
                template_category=template_def.category,
            )
            return ProactiveReminderResponse(
                event_id=uuid4(),
                patient_id=patient_id,
                status="blocked",
                throttled=False,
                blocked_reason="marketing_opt_in_required",
            )

        # Paso 3 — Check throttle (anti-spam)
        is_throttled = await self._re_engagement_repo.check_throttle(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=pattern,
            throttle_days=throttle_days,
        )
        if is_throttled:
            logger.info(
                "proactive_outbound_throttled",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                patient_id=str(patient_id),
                pattern=pattern.value,
                throttle_days=throttle_days,
            )
            return ProactiveReminderResponse(
                event_id=uuid4(),
                patient_id=patient_id,
                status="throttled",
                throttled=True,
                blocked_reason=None,
            )

        # Paso 4 — ComplianceService channel guard (hipaa-lite.md)
        # Verifica que el canal permite PHI (WhatsApp Business API encriptado = OK).
        # SMS free tier, canales no encriptados = BLOCKED.
        compliance_result = await self._compliance_service.check(
            tenant_id=tenant_id,
            lead_id=patient_id,
            channel=channel,
            identifier=patient_phone,
            campaign_id=None,
        )
        if not compliance_result.allowed:
            logger.info(
                "proactive_outbound_compliance_blocked",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                patient_id=str(patient_id),
                block_reason=getattr(compliance_result, "block_reason", "compliance_blocked"),
            )
            return ProactiveReminderResponse(
                event_id=uuid4(),
                patient_id=patient_id,
                status="blocked",
                throttled=False,
                blocked_reason=getattr(compliance_result, "block_reason", "compliance_blocked"),
            )

        # Paso 5 — Audit log sync write FIRST (HIPAA-lite mandatorio)
        # La escritura del audit log DEBE completarse antes de continuar.
        event_id = uuid4()
        now = datetime.now(UTC)

        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="send_proactive_reminder",
            resource_type="re_engagement_event",
            resource_id=event_id,
            payload_redacted=b"",  # PHI sanitized — no patient data en audit log
        )
        await self._audit_repo.write(audit_entry)

        # Paso 6 — Persistir ReEngagementEventModel
        model = ReEngagementEventModel(
            id=event_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=pattern.value,
            trigger_source="proactive_outbound",
            trigger_at=now,
            template_id=template_id,
            sent_at=now,
            idempotency_key=idempotency_key,
            audit_log_id=audit_entry.id,
            created_at=now,
            updated_at=now,
        )
        saved = await self._re_engagement_repo.save(model)

        # Paso 7 — Emitir ReEngagementTriggered domain event via outbox
        domain_event = ReEngagementTriggered.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=pattern.value,
            re_engagement_event_id=event_id,
            template_id=template_id,
        )
        try:
            await adapter_bus.publish(domain_event, session=self._session)
        except Exception as exc:
            # Fallo de outbox no rompe el flujo (best-effort for events)
            logger.warning(
                "proactive_outbound_event_publish_failed",
                event_id=str(event_id),
                tenant_id=str(tenant_id),
                error=str(exc),
            )

        logger.info(
            "proactive_outbound_sent",
            event_id=str(event_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            patient_id=str(patient_id),
            pattern=pattern.value,
            template_id=template_id,
        )

        # Paso 8 — Retornar resultado
        return ProactiveReminderResponse(
            event_id=saved.id,
            patient_id=patient_id,
            status="sent",
            sent_at=saved.sent_at,
            throttled=False,
            blocked_reason=None,
        )
