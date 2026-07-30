# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Notify router — POST /api/v1/scheduling/appointments/{id}/notify.

T-8: Template-only WhatsApp notification + ComplianceService guard + audit log.

Architecture rules (03-arch § 5.1 + hipaa-lite.md):
  - template-only enforcement: template_id required, free-text PROHIBITED (Q15).
  - ComplianceService.validate_outbound_message called BEFORE dispatch.
    BlockedChannelError → HTTP 422 Unprocessable Entity.
  - Audit log row written SYNC (pre-response) — HIPAA-lite mandatory.
    action="reminder_sent" (sent) or "reminder_blocked" (blocked).
  - Growth Studio event emitted AFTER audit (fire-forget, non-blocking).
    event_type="reminder_sent" — 1 of 7 critical funnel events per 03-arch § 10.
  - response_model= MANDATORY on all routes (arch test enforces PII gate).
  - X-Tenant-ID + X-Clinic-ID headers required (HIPAA-lite dual filter).
  - RBAC: doctor, nurse, admin_clinic, valeria_assistant.
  - No business logic in this router — delegate to NotifyService.

Register in main.py:
    from src.modules.vitalia.scheduling.api.notify_router import router as notify_router
    app.include_router(notify_router, prefix="/api/v1/scheduling")

downstream-regression-na: brand-local notify router for vitalia scheduling F2-S1
"""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session_committing
from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.compliance.application.compliance_service_adapter import (
    VitaliaComplianceAdapter,
)
from src.modules.vitalia.scheduling.api.dtos.notify_dtos import (
    NotificationSentResponse,
    SendNotificationRequestDTO,
)
from src.modules.vitalia.scheduling.api.rbac import SCHEDULING_PHI_ROLES
from src.modules.vitalia.scheduling.application.services.notify_service import (
    NotifyService,
)
from src.modules.vitalia.scheduling.domain.exceptions import (
    AppointmentNotFoundError,
    FreeTextNotificationError,
    NotificationBlockedError,
)
from src.modules.vitalia.scheduling.infrastructure.repositories.appointment_detail_repository import (
    AppointmentDetailRepository,
)

logger = structlog.get_logger()

router = APIRouter(tags=["scheduling-notify"])

# RBAC roles allowed to send notifications (per hipaa-lite.md § Access control).
# Single source of truth: scheduling.api.rbac.SCHEDULING_PHI_ROLES (includes `owner`).
_PHI_ROLES: frozenset[str] = SCHEDULING_PHI_ROLES


def _make_notify_service(session: AsyncSession) -> NotifyService:
    """Dependency factory: build NotifyService with concrete collaborators.

    Wires:
      - AppointmentDetailRepository (dual-filter HIPAA-lite repo)
      - AsyncAuditWriter (sync audit log writer — mandatory pre-response)
      - VitaliaComplianceAdapter (channel PHI guard)

    Called from FastAPI DI via Depends(). Not called by tests (injected as mock).
    """
    repo = AppointmentDetailRepository(session)
    audit_writer = AsyncAuditWriter(session=session)
    compliance = VitaliaComplianceAdapter()
    return NotifyService(
        repo=repo,
        audit_writer=audit_writer,
        compliance_service=compliance,
    )


@router.post(
    "/appointments/{appointment_id}/notify",
    response_model=NotificationSentResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar recordatorio por WhatsApp — solo plantillas aprobadas",
    description=(
        "Envía una notificación al paciente usando una plantilla pre-aprobada. "
        "Solo template_id es aceptado — el cuerpo libre está prohibido por HIPAA-lite. "
        "ComplianceService valida el canal antes del envío. "
        "Si el canal está bloqueado (PHI en canal no encriptado), retorna 422."
    ),
    tags=["scheduling-notify"],
)
async def send_appointment_reminder(
    appointment_id: UUID = Path(
        ...,
        description="UUID de la cita a notificar. PHI nunca en URL params.",
    ),
    request: SendNotificationRequestDTO = ...,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    # HB-80: committing session — send_notification writes a sync HIPAA-lite audit row.
    session: AsyncSession = Depends(get_async_session_committing),
) -> NotificationSentResponse:
    """POST /api/v1/scheduling/appointments/{appointment_id}/notify.

    Flow:
      1. RBAC check — reject non-PHI roles with 403.
      2. Delegate to NotifyService.send_notification():
           a. Template-only gate (template_id non-empty).
           b. Load appointment (dual filter tenant_id + clinic_id via repo).
           c. ComplianceService.validate_outbound_message (PHI channel guard).
           d. Audit log sync write (HIPAA-lite — pre-response).
           e. Dispatch stub (real channel adapter in F2-Sx channels-integration).
      3. Emit growth_studio_event "reminder_sent" (fire-forget, non-blocking).
      4. Return NotificationSentResponse.

    Error mapping:
      FreeTextNotificationError → 422 (template_id required)
      AppointmentNotFoundError  → 404 (cross-clinic or not found)
      NotificationBlockedError  → 422 (ComplianceService blocked)
      PHI role denied           → 403

    HIPAA-lite obligations:
      - Dual filter: tenant_id + clinic_id on every appointment query (via repo).
      - Audit log written sync pre-response (AsyncAuditWriter).
      - PHI not in response body (response_model=NotificationSentResponse enforces).
      - ComplianceService guard on every send_notification call (no bypass).
    """
    # RBAC: reject non-PHI roles
    if user_role not in _PHI_ROLES:
        logger.warning(
            "phi_access_denied_notify",
            user_role=user_role,
            allowed_roles=sorted(_PHI_ROLES),
            appointment_id=str(appointment_id),
            tenant_id=tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Rol '{user_role}' no tiene acceso a notificaciones PHI. "
                f"Roles permitidos: {', '.join(sorted(_PHI_ROLES))}."
            ),
        )

    # Parse UUIDs from header strings
    try:
        tenant_uuid = UUID(tenant_id)
        clinic_uuid = UUID(clinic_id)
        user_uuid = UUID(user_id)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Header UUID inválido: {exc}",
        ) from exc

    # Build service via DI factory
    notify_service = _make_notify_service(session)

    try:
        await notify_service.send_notification(
            appointment_id=appointment_id,
            tenant_id=tenant_uuid,
            clinic_id=clinic_uuid,
            user_id=user_uuid,
            template_id=request.template_id,
            channel=request.channel,
        )
    except FreeTextNotificationError as exc:
        # template_id empty or whitespace — free-text attempt
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except AppointmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Cita no encontrada para el tenant y clínica indicados. Verifica que la cita pertenece a tu clínica."
            ),
        ) from exc
    except NotificationBlockedError as exc:
        # ComplianceService blocked the channel (PHI on unencrypted channel)
        # Audit row already written by NotifyService (per hipaa-lite.md)
        logger.info(
            "notification_blocked_by_compliance",
            appointment_id=str(appointment_id),
            tenant_id=tenant_id,
            reason=exc.reason,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Notificación bloqueada por cumplimiento: {exc.reason}. "
                "Por seguridad, los resultados se envían solo por canales encriptados."
            ),
        ) from exc

    # Growth Studio event — fire-forget (failures swallowed in emitter)
    # event_type="reminder_sent" per 03-arch § 10 (7 critical events)
    try:
        emitter = GrowthStudioEmitter(session=session)
        await emitter.emit_event(
            event_type="reminder_sent",
            tenant_id=tenant_uuid,
            clinic_id=clinic_uuid,
            entity_id=appointment_id,
            user_id=user_uuid,
            props={
                "template_id": request.template_id,
                "channel": request.channel,
                "locale": request.locale,
            },
        )
    except Exception:  # noqa: BLE001
        # Fire-forget: emitter already swallows internally, but defensive catch here too
        logger.warning(
            "growth_studio_emit_skipped_notify",
            appointment_id=str(appointment_id),
            tenant_id=tenant_id,
        )

    return NotificationSentResponse(
        status="sent",
        template_id=request.template_id,
        channel=request.channel,
    )
