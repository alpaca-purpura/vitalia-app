# cap: patients.nps-tracking
# story-origin: TBD
"""NPS API endpoints — T-7 fidelización vitalia.

Rutas FastAPI (thin — sin lógica de negocio):
  POST /nps/submit    — paciente registra su score NPS (0-10)
  GET  /nps/summary   — estadísticas NPS agregadas por tenant+clínica+periodo

Arquitectura:
  - response_model= MANDATORY (PII gate HIPAA-lite — comment excluido).
  - POST /nps/submit: accesible por role=patient (no PHI en response).
  - GET /nps/summary: accesible por admin_clinic, doctor, nurse, marketing (stats anónimas).
  - X-Tenant-ID + X-Clinic-ID Headers requeridos (dual filter HIPAA-lite).

downstream-regression-na: brand-local fidelizacion API NPS vitalia
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session
from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.vitalia.fidelizacion.application.dtos.nps_dtos import (
    NPSResponseResponse,
    NPSSubmitRequest,
    NPSSummaryResponse,
)
from src.modules.vitalia.fidelizacion.application.services.nps_service import NPSService
from src.modules.vitalia.fidelizacion.infrastructure.repositories.nps_response_repository import (
    NPSResponseRepository,
)

logger = structlog.get_logger(__name__)

# Roles permitidos para ver resumen NPS (no PHI — stats anónimas)
_NPS_SUMMARY_ROLES = ["doctor", "nurse", "admin_clinic", "marketing"]

router = APIRouter(tags=["fidelizacion-nps"])


# ---------------------------------------------------------------------------
# POST /nps/submit
# ---------------------------------------------------------------------------


@router.post(
    "/nps/submit",
    response_model=NPSResponseResponse,
    summary="Registrar respuesta NPS de un paciente",
)
async def submit_nps_response(
    request: NPSSubmitRequest,
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")] = "patient",
    session: AsyncSession = Depends(get_async_session),
) -> NPSResponseResponse:
    """Registra una respuesta NPS del paciente (score 0-10).

    El campo comment_plain es PHI — se cifra con pgcrypto en DB.
    La respuesta API NO incluye el comentario (PII allowlist HIPAA-lite).
    Se escribe audit log sync antes de retornar.

    Accesible por: patient, doctor, nurse, admin_clinic (cualquier rol puede
    registrar NPS en nombre del paciente — no se expone PHI en la respuesta).

    HIPAA-lite:
      - comment (PHI) excluido del response_model.
      - Audit log sync write mandatorio.
      - Dual filter tenant_id + clinic_id en DB.
    """
    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    nps_repo = NPSResponseRepository(session=session)
    audit_repo = AuditLogRepository(session=session)
    service = NPSService(
        session=session,
        nps_repo=nps_repo,
        audit_repo=audit_repo,
    )

    result = await service.submit(
        tenant_id=tid,
        clinic_id=cid,
        patient_id=request.patient_id,
        score=request.score,
        comment_plain=request.comment_plain,
        appointment_id=request.appointment_id,
        responded_via=request.responded_via,
        user_id=uid,
    )

    logger.info(
        "nps_submitted_via_api",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        patient_id=str(request.patient_id),
        score=request.score,
    )
    return result


# ---------------------------------------------------------------------------
# GET /nps/summary
# ---------------------------------------------------------------------------


@router.get(
    "/nps/summary",
    response_model=NPSSummaryResponse,
    summary="Estadísticas NPS agregadas por tenant+clínica+periodo",
)
async def get_nps_summary(
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
    user_id: Annotated[str, Header(alias="X-User-ID")],
    user_role: Annotated[str, Header(alias="X-User-Role")],
    period_days: int = 30,
    session: AsyncSession = Depends(get_async_session),
) -> NPSSummaryResponse:
    """Retorna estadísticas NPS agregadas para un periodo.

    Accesible por admin_clinic, doctor, nurse y marketing (datos anónimos).
    NO incluye PHI per-patient — solo contadores agregados.

    HIPAA-lite:
      - Dual filter tenant_id + clinic_id.
      - Sin PHI per-patient en respuesta (comment excluido, patient anónimo).
      - Acceso marketing permitido solo a stats anónimas.
    """
    if user_role not in _NPS_SUMMARY_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "access_denied",
                "message": "No tiene permiso para ver el resumen NPS.",
            },
        )

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    nps_repo = NPSResponseRepository(session=session)
    audit_repo = AuditLogRepository(session=session)
    service = NPSService(
        session=session,
        nps_repo=nps_repo,
        audit_repo=audit_repo,
    )

    now = datetime.now(UTC)
    period_start = now - timedelta(days=period_days)

    # Obtener respuestas del periodo (sin PHI — solo para cálculo)
    all_responses = await nps_repo.list_by_period(
        tenant_id=tid,
        clinic_id=cid,
        period_start=period_start,
        period_end=now,
    )

    result = await service.summary(
        tenant_id=tid,
        clinic_id=cid,
        period_start=period_start,
        period_end=now,
        all_responses=all_responses,
    )

    logger.info(
        "nps_summary_retrieved_via_api",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        period_days=period_days,
        user_role=user_role,
    )
    return result
