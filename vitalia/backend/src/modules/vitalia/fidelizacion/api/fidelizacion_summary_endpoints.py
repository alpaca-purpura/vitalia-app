# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Fidelización summary + activity stream API endpoints — T-7 vitalia.

Rutas FastAPI (thin — sin lógica de negocio):
  GET /summary          — 5 KPIs del hero dashboard
  GET /activity-stream  — poll 5s para Activity Stream footer

Arquitectura:
  - response_model= MANDATORY (PII gate HIPAA-lite — sin PHI per-patient).
  - @require_phi_access: doctor, nurse, admin_clinic (datos de pacientes).
  - X-Tenant-ID + X-Clinic-ID Headers requeridos (dual filter HIPAA-lite).
  - AsyncSession Depends injection.

downstream-regression-na: brand-local fidelizacion API summary vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session
from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    ActivityStreamItem,
    ActivityStreamResponse,
    FidelizacionSummaryResponse,
)
from src.modules.vitalia.fidelizacion.application.services.nps_service import NPSService
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import (
    ReEngagementEventModel,
)
from src.modules.vitalia.fidelizacion.infrastructure.repositories.nps_response_repository import (
    NPSResponseRepository,
)

logger = structlog.get_logger(__name__)

_PHI_ROLES = ["doctor", "nurse", "admin_clinic"]

router = APIRouter(tags=["fidelizacion-summary"])


# ---------------------------------------------------------------------------
# Helpers internos (testable via patch)
# ---------------------------------------------------------------------------


async def _build_summary(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    session: AsyncSession,
) -> FidelizacionSummaryResponse:
    """Construye el resumen de 5 KPIs de fidelización.

    No incluye PHI per-patient — solo contadores agregados.
    Queries con dual filter tenant_id + clinic_id aplicado.

    Args:
        tenant_id: UUID del tenant.
        clinic_id: UUID de la clínica.
        session: AsyncSession activo.

    Returns:
        FidelizacionSummaryResponse con los 5 KPIs del hero dashboard.
    """
    nps_repo = NPSResponseRepository(session=session)
    audit_repo = AuditLogRepository(session=session)
    now = datetime.now(UTC)
    period_start_30d = now - timedelta(days=30)

    # KPI 1: pacientes activos en seguimiento (eventos enviados sin outcome en 30d)
    stmt_active = (
        select(ReEngagementEventModel)
        .where(ReEngagementEventModel.tenant_id == tenant_id)
        .where(ReEngagementEventModel.clinic_id == clinic_id)
        .where(ReEngagementEventModel.sent_at.is_not(None))
        .where(ReEngagementEventModel.outcome.is_(None))
        .where(ReEngagementEventModel.deleted_at.is_(None))
        .where(ReEngagementEventModel.trigger_at >= period_start_30d)
    )
    result_active = await session.execute(stmt_active)
    active_events = result_active.scalars().all()
    patients_in_followup = len({e.patient_id for e in active_events})

    # KPI 2: pacientes cerca de abandono (eventos con gap_alert triggerado)
    stmt_gap = (
        select(ReEngagementEventModel)
        .where(ReEngagementEventModel.tenant_id == tenant_id)
        .where(ReEngagementEventModel.clinic_id == clinic_id)
        .where(ReEngagementEventModel.pattern == ReEngagementPattern.GAP_MULTI_SESSION.value)
        .where(ReEngagementEventModel.outcome.is_(None))
        .where(ReEngagementEventModel.deleted_at.is_(None))
    )
    result_gap = await session.execute(stmt_gap)
    gap_events = result_gap.scalars().all()
    near_abandonment = len({e.patient_id for e in gap_events})

    # KPI 3: tasa de retorno (convertidos / enviados en 30d)
    stmt_sent = (
        select(ReEngagementEventModel)
        .where(ReEngagementEventModel.tenant_id == tenant_id)
        .where(ReEngagementEventModel.clinic_id == clinic_id)
        .where(ReEngagementEventModel.sent_at.is_not(None))
        .where(ReEngagementEventModel.deleted_at.is_(None))
        .where(ReEngagementEventModel.trigger_at >= period_start_30d)
    )
    result_sent = await session.execute(stmt_sent)
    sent_events = result_sent.scalars().all()
    total_sent = len(sent_events)
    total_converted = sum(
        1
        for e in sent_events
        if e.outcome == ReEngagementOutcome.SCHEDULED.value or e.converted_to_appointment_id is not None
    )
    return_rate = round(total_converted / total_sent, 4) if total_sent > 0 else 0.0

    # KPI 4: re-engagements exitosos en periodo (convertidos a turno)
    re_engaged_count_period = total_converted

    # KPI 5: NPS promedio (últimos 30d)
    nps_responses = await nps_repo.list_by_period(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        period_start=period_start_30d,
        period_end=now,
    )
    nps_average: float | None = None
    if nps_responses:
        nps_svc = NPSService(session=session, nps_repo=nps_repo, audit_repo=audit_repo)
        summary = await nps_svc.summary(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start_30d,
            period_end=now,
            all_responses=nps_responses,
        )
        nps_average = summary.nps_score

    return FidelizacionSummaryResponse(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        snapshot_at=now,
        patients_in_followup=patients_in_followup,
        near_abandonment=near_abandonment,
        return_rate=return_rate,
        re_engaged_count_period=re_engaged_count_period,
        nps_average=nps_average,
    )


async def _build_activity_stream(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    since: datetime | None,
    session: AsyncSession,
) -> ActivityStreamResponse:
    """Construye el Activity Stream de eventos recientes de fidelización.

    Solo metadata de trazabilidad — sin PHI per-patient.
    Retorna eventos de los últimos 5 minutos (o desde 'since').

    Args:
        tenant_id: UUID del tenant.
        clinic_id: UUID de la clínica.
        since: Timestamp desde el cual traer eventos (None = 5 min atrás).
        session: AsyncSession activo.

    Returns:
        ActivityStreamResponse con items recientes sin PHI.
    """
    now = datetime.now(UTC)
    since_ts = since if since is not None else now - timedelta(minutes=5)

    stmt = (
        select(ReEngagementEventModel)
        .where(ReEngagementEventModel.tenant_id == tenant_id)
        .where(ReEngagementEventModel.clinic_id == clinic_id)
        .where(ReEngagementEventModel.updated_at >= since_ts)
        .where(ReEngagementEventModel.deleted_at.is_(None))
        .order_by(ReEngagementEventModel.updated_at.desc())
        .limit(50)
    )
    result = await session.execute(stmt)
    events = result.scalars().all()

    items = [
        ActivityStreamItem(
            event_id=e.id,
            patient_id=e.patient_id,  # UUID — no PHI (no nombre, no DNI)
            event_type=e.pattern,
            description=f"Re-engagement {e.pattern} — outcome: {e.outcome or 'pendiente'}",
            occurred_at=e.updated_at,
            clinic_id=e.clinic_id,
        )
        for e in events
    ]

    return ActivityStreamResponse(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        since=since_ts,
        items=items,
        total=len(items),
    )


# ---------------------------------------------------------------------------
# GET /summary
# ---------------------------------------------------------------------------


@router.get(
    "/summary",
    response_model=FidelizacionSummaryResponse,
    summary="Resumen de 5 KPIs de fidelización (hero dashboard)",
)
async def get_fidelizacion_summary(
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    session: AsyncSession = Depends(get_async_session),
) -> FidelizacionSummaryResponse:
    """Retorna los 5 KPIs del hero dashboard de fidelización.

    KPIs incluidos:
      1. patients_in_followup — pacientes activos en seguimiento
      2. near_abandonment — pacientes con gap alert (cerca de abandono)
      3. return_rate — tasa de retorno (re-engaged / enviados en 30d)
      4. re_engaged_count_period — re-engagements exitosos en 30d
      5. nps_average — NPS promedio últimos 30d (None si sin datos)

    HIPAA-lite:
      - Sin PHI per-patient en respuesta.
      - RBAC: solo doctor, nurse, admin_clinic.
      - Dual filter tenant_id + clinic_id en todas las queries.
    """
    if user_role not in _PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "phi_access_denied",
                "message": "No tiene permiso para ver el resumen de fidelización.",
            },
        )

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    result = await _build_summary(
        tenant_id=tid,
        clinic_id=cid,
        session=session,
    )

    logger.info(
        "fidelizacion_summary_retrieved",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_role=user_role,
    )
    return result


# ---------------------------------------------------------------------------
# GET /activity-stream
# ---------------------------------------------------------------------------


@router.get(
    "/activity-stream",
    response_model=ActivityStreamResponse,
    summary="Activity Stream de eventos recientes de fidelización (poll 5s)",
)
async def get_activity_stream(
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    since: datetime | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> ActivityStreamResponse:
    """Retorna eventos recientes de fidelización para el Activity Stream footer.

    Diseñado para poll cada 5 segundos desde el frontend.
    Solo incluye metadata de trazabilidad — sin PHI per-patient.

    HIPAA-lite:
      - Sin PHI per-patient (UUID de paciente solo — sin nombre, DNI, diagnóstico).
      - RBAC: solo doctor, nurse, admin_clinic.
      - Dual filter tenant_id + clinic_id.
    """
    if user_role not in _PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "phi_access_denied",
                "message": "No tiene permiso para ver el activity stream.",
            },
        )

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    result = await _build_activity_stream(
        tenant_id=tid,
        clinic_id=cid,
        since=since,
        session=session,
    )

    logger.info(
        "activity_stream_polled",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        items_count=result.total,
    )
    return result
