# cap: scheduling.mateo-agenda
"""Vitalia Scheduling — Availability API Router (T-BE-3).

3 endpoints per 03-arch-be.md § 7:
  POST /api/v1/scheduling/availability/check       — check 4-state availability
  POST /api/v1/scheduling/availability/free-doctors — list free doctors for slot
  GET  /api/v1/scheduling/availability/day-strip   — paint working+busy blocks

PHI contract:
  - Availability data carries NO patient PHI (only scheduling metadata).
  - conflict_label: time string only ("se solapa con 10:15") — never patient name.
  - doctor_label: professional display name — not patient data.
  - day-strip: start/end times + block kind only — no names, no patient IDs.

HIPAA-lite (hipaa-lite.md):
  - Dual filter: tenant_id + clinic_id MANDATORY (X-Tenant-ID + X-Clinic-ID headers).
  - RBAC: SCHEDULING_PHI_ROLES (same as agenda_router — availability is scheduling-scoped).
  - response_model= on every endpoint (arch test enforces — pii-sanitisation.md).
  - NO PHI in URL params — doctor_id and date are scheduling identifiers, not PHI.
  - Cross-clinic → 403. Cross-tenant → 404 (HIPAA: don't confirm existence).

Architecture:
  - Thin router: validate DTO → call service → map exception → HTTPException.
  - No business logic in api/ (backend-ddd.md).
  - AvailabilityCheckService injected with AvailabilityQueryRepository (port pattern).

03-arch-be.md § 7.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.scheduling.api.dtos.availability_dtos import (
    AvailabilityCheckRequest,
    AvailabilityCheckResponse,
    DayBlockItem,
    DayStripResponse,
    FreeDoctorItem,
    FreeDoctorsRequest,
    FreeDoctorsResponse,
    ServiceDayDoctor,
    ServiceDayResponse,
)
from src.modules.vitalia.scheduling.api.rbac import SCHEDULING_PHI_ROLES
from src.modules.vitalia.scheduling.application.services.availability_check_service import (
    AvailabilityCheckService,
)

logger = structlog.get_logger()

router = APIRouter(tags=["scheduling-availability"])


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


async def _get_db() -> AsyncSession:
    """Async DB session (read-only for availability — no audit write needed here).

    Availability endpoints read scheduling metadata only (no PHI).
    Uses committing session for consistency with other scheduling routes.
    """
    from src.db import get_async_session_committing  # noqa: PLC0415

    async for session in get_async_session_committing():
        yield session


def _build_service(db: AsyncSession) -> AvailabilityCheckService:
    """Build AvailabilityCheckService with the query repository (D-B pattern)."""
    from src.modules.vitalia.scheduling.infrastructure.repositories.availability_query_repository import (  # noqa: PLC0415
        AvailabilityQueryRepository,
    )

    repo = AvailabilityQueryRepository(session=db)
    return AvailabilityCheckService(port=repo)


def _rbac_check(user_role: str) -> None:
    """Raise 403 if user_role not in SCHEDULING_PHI_ROLES."""
    if user_role not in SCHEDULING_PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "PHI_RBAC_DENIED",
                "message": "Acceso no autorizado a datos de disponibilidad.",
            },
        )


# ---------------------------------------------------------------------------
# POST /availability/check
# ---------------------------------------------------------------------------


@router.post(
    "/availability/check",
    response_model=AvailabilityCheckResponse,
    summary="Verificar disponibilidad de un médico en un slot",
    description=(
        "Devuelve el estado de disponibilidad (available|busy|out_of_hours|no_schedule) "
        "para el médico y slot solicitado. "
        "La respuesta NO contiene PHI — solo metadata de agenda."
    ),
)
async def check_availability(
    request: AvailabilityCheckRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID", default=""),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> AvailabilityCheckResponse:
    """POST /availability/check — 4-state availability matrix.

    Gherkin: SC-sin-horario, SC-fuera-horario, SC-solape, SC-disponibilidad-falla.
    HIPAA-lite: dual filter enforced at service+repo layer.
    PHI: response carries NO patient data (conflict_label = time string only).
    """
    _rbac_check(user_role)

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    service = _build_service(db)
    result = await service.check(
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=request.doctor_id,
        start=request.start,
        duration_minutes=request.duration_minutes,
    )

    logger.info(
        "availability_check",
        tenant_id=str(tid),
        clinic_id=str(cid),
        doctor_id=str(request.doctor_id),
        status=result.status,
    )

    return AvailabilityCheckResponse(
        status=result.status,
        conflict_label=result.conflict_label,
        conflict_start=result.conflict_start,
    )


# ---------------------------------------------------------------------------
# POST /availability/free-doctors
# ---------------------------------------------------------------------------


@router.post(
    "/availability/free-doctors",
    response_model=FreeDoctorsResponse,
    summary="Listar médicos disponibles en un slot",
    description=(
        "Devuelve la lista de médicos activos disponibles para el slot solicitado. "
        "Solo retorna médicos en estado AVAILABLE (sin solapamiento, dentro de horario). "
        "Sin PHI — doctor_label es nombre profesional, no datos de paciente."
    ),
)
async def list_free_doctors(
    request: FreeDoctorsRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID", default=""),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> FreeDoctorsResponse:
    """POST /availability/free-doctors — doctors available for a slot.

    Gherkin: SC-reasignar, SC-reasignar-vacio.
    Dual filter enforced at service layer (tenant_id + clinic_id in port calls).
    """
    _rbac_check(user_role)

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    service = _build_service(db)
    items = await service.free_doctors(
        tenant_id=tid,
        clinic_id=cid,
        start=request.start,
        duration_minutes=request.duration_minutes,
    )

    logger.info(
        "availability_free_doctors",
        tenant_id=str(tid),
        clinic_id=str(cid),
        free_count=len(items),
    )

    return FreeDoctorsResponse(
        doctors=[FreeDoctorItem(doctor_id=item.doctor_id, doctor_label=item.doctor_label) for item in items],
        count=len(items),
    )


# ---------------------------------------------------------------------------
# GET /availability/day-strip
# ---------------------------------------------------------------------------


@router.get(
    "/availability/day-strip",
    response_model=DayStripResponse,
    summary="Vista de franjas del día — working_hours + busy blocks",
    description=(
        "Devuelve las franjas del día para un médico: bloques de horario laboral "
        "y bloques ocupados (citas confirmadas/pendientes). "
        "Sin PHI — los bloques contienen solo start/end y tipo, sin datos de paciente."
    ),
)
async def get_day_strip(
    doctor_id: UUID = Query(..., description="ID del médico"),
    strip_date: str = Query(alias="date", description="Fecha YYYY-MM-DD (UTC)"),
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID", default=""),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> DayStripResponse:
    """GET /availability/day-strip — visual time strip for new appointment picker.

    Gherkin: SC-mini-vista.
    Returns working_hours blocks + busy blocks merged into a sorted list.
    No PHI: busy blocks carry only [start, end) times.
    """
    _rbac_check(user_role)

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    try:
        req_date = date.fromisoformat(strip_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "INVALID_DATE", "message": "Formato de fecha inválido. Use YYYY-MM-DD."},
        )

    from src.modules.vitalia.scheduling.infrastructure.repositories.availability_query_repository import (  # noqa: PLC0415
        AvailabilityQueryRepository,
    )

    repo = AvailabilityQueryRepository(session=db)

    working_hours = await repo.get_working_hours(
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=doctor_id,
        day=req_date,
    )
    busy_ranges = await repo.get_busy_ranges(
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=doctor_id,
        day=req_date,
    )

    # Merge into sorted blocks — working_hours first, then busy
    blocks: list[DayBlockItem] = []
    for w in working_hours:
        blocks.append(DayBlockItem(kind="working_hours", start=w.start, end=w.end))
    for b in busy_ranges:
        blocks.append(DayBlockItem(kind="busy", start=b.start, end=b.end))

    # Sort chronologically for FE rendering
    blocks.sort(key=lambda bl: bl.start)

    logger.debug(
        "availability_day_strip",
        tenant_id=str(tid),
        clinic_id=str(cid),
        doctor_id=str(doctor_id),
        date=str(req_date),
        working_blocks=len(working_hours),
        busy_blocks=len(busy_ranges),
    )

    return DayStripResponse(
        doctor_id=doctor_id,
        date=req_date,
        blocks=blocks,
    )


# ---------------------------------------------------------------------------
# GET /availability/service-day (T-D1)
# ---------------------------------------------------------------------------


@router.get(
    "/availability/service-day",
    response_model=ServiceDayResponse,
    summary="Vista del día de TODOS los médicos de un servicio",
    description=(
        "Devuelve las franjas del día (working_hours + busy) de cada médico "
        "vinculado al servicio (offer). Sin vínculos → todos los médicos activos de la clínica. "
        "Read-only, sin PHI — los bloques contienen solo tipo + start/end."
    ),
)
async def get_service_day(
    service_id: UUID = Query(..., alias="serviceId", description="ID del servicio (offer)"),
    strip_date: str = Query(alias="date", description="Fecha YYYY-MM-DD (UTC)"),
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID", default=""),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> ServiceDayResponse:
    """GET /availability/service-day — day availability of every doctor of a service.

    Read-only composition (T-D1): resolves service→doctors and reuses the existing
    working/busy readers. No audit write (no PHI mutation). Dual filter enforced at
    repo layer — cross-clinic/cross-tenant doctors excluded.
    """
    _rbac_check(user_role)

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    try:
        req_date = date.fromisoformat(strip_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "INVALID_DATE", "message": "Formato de fecha inválido. Use YYYY-MM-DD."},
        )

    service = _build_service(db)
    doctors = await service.service_day(
        tenant_id=tid,
        clinic_id=cid,
        offer_id=service_id,
        day=req_date,
    )

    logger.info(
        "availability_service_day",
        tenant_id=str(tid),
        clinic_id=str(cid),
        service_id=str(service_id),
        date=str(req_date),
        doctor_count=len(doctors),
    )

    return ServiceDayResponse(
        service_id=service_id,
        date=req_date,
        doctors=[
            ServiceDayDoctor(
                doctor_id=d.doctor_id,
                doctor_label=d.doctor_label,
                blocks=[DayBlockItem(kind=bl.kind, start=bl.start, end=bl.end) for bl in d.blocks],
            )
            for d in doctors
        ],
    )
