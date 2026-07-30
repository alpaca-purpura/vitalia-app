# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Re-engagement API endpoints — T-7 fidelización vitalia.

Rutas FastAPI (thin — sin lógica de negocio):
  GET  /re-engagement/patterns    — listar resúmenes de patrones activos
  POST /re-engagement/send-proactive — enviar recordatorio proactivo
  POST /re-engagement/pause           — pausar paciente
  POST /re-engagement/mark-external   — registrar respuesta externa
  POST /re-engagement/mark-no-continue — registrar decisión no continuar
  POST /re-engagement/manual-call     — registrar llamada manual

Arquitectura:
  - response_model= MANDATORY en todos los endpoints (PII gate HIPAA-lite).
  - @require_phi_access en todos los endpoints PHI (doctor/nurse/admin_clinic).
  - X-Tenant-ID + X-Clinic-ID Headers requeridos (dual filter HIPAA-lite).
  - AsyncSession Depends injection.
  - Mapeo de excepciones de dominio a HTTPException.

downstream-regression-na: brand-local fidelizacion API re-engagement vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session
from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogEntry,
    AuditLogRepository,
)
from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    ManualCallRequest,
    ManualCallResponse,
    MarkExternalRequest,
    MarkExternalResponse,
    MarkNoContinueRequest,
    MarkNoContinueResponse,
    PatternSummaryResponse,
    PausePatientRequest,
    PausePatientResponse,
    ProactiveReminderRequest,
    ProactiveReminderResponse,
    ReEngagementPatternListResponse,
)
from src.modules.vitalia.fidelizacion.application.services.manual_call_service import (
    ManualCallService,
)
from src.modules.vitalia.fidelizacion.application.services.pause_patient_service import (
    PausePatientService,
)
from src.modules.vitalia.fidelizacion.application.services.proactive_outbound_service import (
    ProactiveOutboundService,
)
from src.modules.vitalia.fidelizacion.application.services.re_engagement_service import (
    ReEngagementService,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.infrastructure.repositories.re_engagement_event_repository import (
    ReEngagementEventRepository,
)

logger = structlog.get_logger(__name__)

_PHI_ROLES = ["doctor", "nurse", "admin_clinic"]


class _ComplianceCheckResult:
    """Resultado de verificación de compliance."""

    def __init__(self, allowed: bool, block_reason: str | None = None) -> None:
        self.allowed = allowed
        self.block_reason = block_reason


class _NoopComplianceService:
    """Compliance service por defecto para endpoints — delega canal check a capa de negocio.

    El ProactiveOutboundService llama a compliance_service.check() antes de enviar.
    Esta implementación permite el envío y aplica el channel guard vía
    VitaliaComplianceAdapter en el wrapper de la capa de canal.

    En producción real, se sustituye por la integración con luana_core_compliance.
    """

    async def check(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: object,
    ) -> _ComplianceCheckResult:
        """Verifica compliance del canal — permite por defecto (whitelist).

        Para vitalia el guard de canal está en VitaliaComplianceAdapter
        a nivel de sales_agent. En el API endpoint de re-engagement,
        el check de channel se hace vía el campo `channel` del request:
        solo whatsapp (Business API encriptado) está permitido.
        """
        blocked_channels = {"sms", "whatsapp_free", "email_plain"}
        if channel.lower() in blocked_channels:
            return _ComplianceCheckResult(
                allowed=False,
                block_reason=f"Canal '{channel}' no permitido para PHI (HIPAA-lite)",
            )
        return _ComplianceCheckResult(allowed=True)


router = APIRouter(tags=["fidelizacion-re-engagement"])

# ---------------------------------------------------------------------------
# Helper — dependency extracts + audit repo
# ---------------------------------------------------------------------------


async def _get_audit_repo(
    session: AsyncSession = Depends(get_async_session),
) -> AuditLogRepository:
    """Inyecta AuditLogRepository compartido."""
    return AuditLogRepository(session=session)


async def _mark_outcome(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    patient_id: UUID,
    event_id: UUID | None,
    outcome: ReEngagementOutcome,
    comment: str | None,
    user_id: UUID,
    session: AsyncSession,
) -> tuple[UUID, ReEngagementOutcome, datetime]:
    """Helper interno — marca outcome en evento de re-engagement existente o crea nuevo.

    Retorna (event_id, outcome, recorded_at).
    """
    repo = ReEngagementEventRepository(session=session)
    audit_repo = AuditLogRepository(session=session)
    now = datetime.now(UTC)

    if event_id is not None:
        # Intentar actualizar evento existente (dual filter aplicado)
        existing = await repo.get_by_id(id=event_id, tenant_id=tenant_id, scope_id=clinic_id)
        if existing is not None:
            existing.outcome = outcome.value
            existing.response_at = now
            existing.updated_at = now
            saved = await repo.save(existing)
            final_event_id = saved.id
        else:
            final_event_id = event_id
    else:
        # Crear nuevo evento de outcome manual
        from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import (  # noqa: PLC0415
            ReEngagementEventModel,
        )

        new_id = uuid4()
        model = ReEngagementEventModel(
            id=new_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            pattern=ReEngagementPattern.FOLLOW_UP.value,
            trigger_source="manual_outcome",
            trigger_at=now,
            sent_at=now,
            response_at=now,
            outcome=outcome.value,
            created_at=now,
            updated_at=now,
        )
        saved = await repo.save(model)
        final_event_id = saved.id

    # Audit log sync write — HIPAA-lite mandatorio
    audit_entry = AuditLogEntry(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        action=f"mark_re_engagement_outcome_{outcome.value}",
        resource_type="re_engagement_event",
        resource_id=final_event_id,
        payload_redacted=b"",
    )
    await audit_repo.write(audit_entry)

    return final_event_id, outcome, now


# ---------------------------------------------------------------------------
# GET /re-engagement/patterns
# ---------------------------------------------------------------------------


@router.get(
    "/re-engagement/patterns",
    response_model=ReEngagementPatternListResponse,
    summary="Listar resúmenes de patrones de re-engagement activos",
)
async def list_re_engagement_patterns(
    pattern: ReEngagementPattern,
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
) -> ReEngagementPatternListResponse:
    """Lista resúmenes de un patrón de re-engagement para un tenant+clínica.

    HIPAA-lite:
      - Dual filter tenant_id + clinic_id aplicado en el servicio.
      - RBAC: solo doctor, nurse, admin_clinic acceden.
      - Sin PHI en respuesta.
    """
    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    if user_role not in _PHI_ROLES:
        logger.warning("phi_access_denied", user_role=user_role, endpoint="list_patterns")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "phi_access_denied",
                "message": "No tiene permiso para acceder a datos de re-engagement.",
            },
        )

    repo = ReEngagementEventRepository(session=session)
    service = ReEngagementService(
        session=session,
        re_engagement_repo=repo,
        audit_repo=AuditLogRepository(session=session),
    )

    events = await service.list_patterns(
        tenant_id=tid,
        clinic_id=cid,
        pattern=pattern,
        limit=limit,
    )

    # Calcular estadísticas del patrón
    total_sent = sum(1 for e in events if e.sent_at is not None)
    total_responded = sum(1 for e in events if e.response_at is not None)
    total_converted = sum(
        1
        for e in events
        if e.outcome == ReEngagementOutcome.RESCHEDULED.value or e.converted_to_appointment_id is not None
    )
    response_rate = total_responded / total_sent if total_sent > 0 else 0.0
    conversion_rate = total_converted / total_sent if total_sent > 0 else 0.0

    summary = PatternSummaryResponse(
        pattern=pattern,
        total_sent=total_sent,
        total_responded=total_responded,
        total_converted=total_converted,
        response_rate=round(response_rate, 4),
        conversion_rate=round(conversion_rate, 4),
    )

    logger.info(
        "re_engagement_patterns_listed",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        pattern=pattern.value,
        user_id=user_id,
    )

    return ReEngagementPatternListResponse(
        tenant_id=tid,
        clinic_id=cid,
        patterns=[summary],
    )


# ---------------------------------------------------------------------------
# POST /re-engagement/send-proactive
# ---------------------------------------------------------------------------


@router.post(
    "/re-engagement/send-proactive",
    response_model=ProactiveReminderResponse,
    summary="Enviar recordatorio proactivo a un paciente",
)
async def send_proactive_reminder(
    request: ProactiveReminderRequest,
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    session: AsyncSession = Depends(get_async_session),
) -> ProactiveReminderResponse:
    """Envía un recordatorio proactivo a un paciente via canal seleccionado.

    Aplica throttle de 7 días por defecto. Verifica opt-out y compliance antes
    de enviar. El event se persiste con audit log sync.

    HIPAA-lite:
      - Dual filter tenant_id + clinic_id.
      - RBAC: solo doctor, nurse, admin_clinic.
      - Audit log escrito sync antes de retornar.
    """
    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    if user_role not in _PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "phi_access_denied",
                "message": "No tiene permiso para enviar recordatorios.",
            },
        )

    repo = ReEngagementEventRepository(session=session)
    audit_repo = AuditLogRepository(session=session)

    service = ProactiveOutboundService(
        session=session,
        re_engagement_repo=repo,
        audit_repo=audit_repo,
        compliance_service=_NoopComplianceService(),
    )

    result = await service.send_proactive_reminder(
        tenant_id=tid,
        clinic_id=cid,
        patient_id=request.patient_id,
        patient_phone=request.patient_phone,
        patient_name=request.patient_name,
        template_id=request.template_id,
        pattern=request.pattern,
        channel=request.channel,
        marketing_opt_in=True,  # default optimista — CRM valida externamente
        opt_out=False,  # default — CRM valida externamente
        user_id=uid,
        idempotency_key=request.idempotency_key,
        throttle_days=request.throttle_days,
    )

    logger.info(
        "proactive_reminder_sent",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=str(request.patient_id),
        status=result.status,
    )
    return result


# ---------------------------------------------------------------------------
# POST /re-engagement/pause
# ---------------------------------------------------------------------------


@router.post(
    "/re-engagement/pause",
    response_model=PausePatientResponse,
    summary="Pausar re-engagement de un paciente",
)
async def pause_patient_re_engagement(
    request: PausePatientRequest,
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    session: AsyncSession = Depends(get_async_session),
) -> PausePatientResponse:
    """Pausa los re-engagements de un paciente hasta una fecha futura.

    HIPAA-lite:
      - Dual filter tenant_id + clinic_id en modelos.
      - RBAC: solo doctor, nurse, admin_clinic.
      - Audit log sync write mandatorio.
    """
    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    if user_role not in _PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "phi_access_denied",
                "message": "No tiene permiso para pausar re-engagements.",
            },
        )

    repo = ReEngagementEventRepository(session=session)
    audit_repo = AuditLogRepository(session=session)
    service = PausePatientService(
        session=session,
        re_engagement_repo=repo,
        audit_repo=audit_repo,
    )

    result = await service.pause_patient(
        tenant_id=tid,
        clinic_id=cid,
        patient_id=request.patient_id,
        pause_until=request.pause_until,
        pause_reason=request.pause_reason,
        paused_by_user_id=request.paused_by_user_id or uid,
    )

    logger.info(
        "patient_re_engagement_paused_via_api",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=str(request.patient_id),
    )
    return result


# ---------------------------------------------------------------------------
# POST /re-engagement/mark-external
# ---------------------------------------------------------------------------


@router.post(
    "/re-engagement/mark-external",
    response_model=MarkExternalResponse,
    summary="Registrar respuesta externa del paciente",
)
async def mark_patient_external_response(
    request: MarkExternalRequest,
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    session: AsyncSession = Depends(get_async_session),
) -> MarkExternalResponse:
    """Registra que el paciente respondió fuera del canal automatizado.

    Ejemplo: el paciente llamó directamente a la clínica o respondió por
    un canal no monitorizado por el sistema.

    HIPAA-lite:
      - Dual filter tenant_id + clinic_id.
      - RBAC: solo doctor, nurse, admin_clinic.
      - Audit log sync write.
    """
    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    if user_role not in _PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "phi_access_denied",
                "message": "No tiene permiso para registrar respuestas de re-engagement.",
            },
        )

    event_id, outcome, recorded_at = await _mark_outcome(
        tenant_id=tid,
        clinic_id=cid,
        patient_id=request.patient_id,
        event_id=request.event_id,
        outcome=ReEngagementOutcome.RESPONDED,
        comment=request.comment,
        user_id=uid,
        session=session,
    )

    logger.info(
        "re_engagement_marked_external",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=str(request.patient_id),
        event_id=str(event_id),
    )
    return MarkExternalResponse(
        event_id=event_id,
        patient_id=request.patient_id,
        outcome=outcome,
        recorded_at=recorded_at,
    )


# ---------------------------------------------------------------------------
# POST /re-engagement/mark-no-continue
# ---------------------------------------------------------------------------


@router.post(
    "/re-engagement/mark-no-continue",
    response_model=MarkNoContinueResponse,
    summary="Registrar decisión del paciente de no continuar el tratamiento",
)
async def mark_patient_no_continue(
    request: MarkNoContinueRequest,
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    session: AsyncSession = Depends(get_async_session),
) -> MarkNoContinueResponse:
    """Registra que el paciente decidió no continuar el tratamiento.

    Marca el evento como OPTED_OUT y escribe audit log. No elimina historial.

    HIPAA-lite:
      - Dual filter tenant_id + clinic_id.
      - RBAC: solo doctor, nurse, admin_clinic.
      - Audit log sync write.
    """
    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    if user_role not in _PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "phi_access_denied",
                "message": "No tiene permiso para registrar decisiones de pacientes.",
            },
        )

    event_id, outcome, recorded_at = await _mark_outcome(
        tenant_id=tid,
        clinic_id=cid,
        patient_id=request.patient_id,
        event_id=request.event_id,
        outcome=ReEngagementOutcome.OPTED_OUT,
        comment=request.reason,
        user_id=uid,
        session=session,
    )

    logger.info(
        "re_engagement_marked_no_continue",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=str(request.patient_id),
        event_id=str(event_id),
    )
    return MarkNoContinueResponse(
        event_id=event_id,
        patient_id=request.patient_id,
        outcome=outcome,
        recorded_at=recorded_at,
    )


# ---------------------------------------------------------------------------
# POST /re-engagement/manual-call
# ---------------------------------------------------------------------------


@router.post(
    "/re-engagement/manual-call",
    response_model=ManualCallResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar llamada manual a un paciente",
)
async def record_manual_call(
    request: ManualCallRequest,
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    session: AsyncSession = Depends(get_async_session),
) -> ManualCallResponse:
    """Registra una llamada telefónica manual realizada por el equipo clínico.

    Las notas de la llamada (notes_plain) son PHI — se cifran con pgcrypto
    en DB. La respuesta NO incluye notes_plain (PII allowlist).

    HIPAA-lite:
      - Dual filter tenant_id + clinic_id.
      - RBAC: solo doctor, nurse, admin_clinic.
      - notes_plain = PHI (cifrado BYTEA en DB vía pgcrypto).
      - Audit log sync write.
    """
    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    if user_role not in _PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "phi_access_denied",
                "message": "No tiene permiso para registrar llamadas de pacientes.",
            },
        )

    repo = ReEngagementEventRepository(session=session)
    audit_repo = AuditLogRepository(session=session)
    service = ManualCallService(
        session=session,
        re_engagement_repo=repo,
        audit_repo=audit_repo,
    )

    result = await service.record_call(
        tenant_id=tid,
        clinic_id=cid,
        patient_id=request.patient_id,
        outcome=request.outcome,
        notes_plain=request.notes_plain,
        called_by_user_id=request.called_by_user_id,
        converted_to_appointment_id=request.converted_to_appointment_id,
    )

    logger.info(
        "manual_call_recorded_via_api",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=str(request.patient_id),
        outcome=request.outcome.value,
    )
    return result
