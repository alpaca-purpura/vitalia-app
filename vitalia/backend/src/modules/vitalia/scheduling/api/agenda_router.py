# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Vitalia Scheduling — Agenda API Router.

5 endpoints per 03-arch § 5:
  GET  /api/v1/scheduling/agenda/grid          — PHI-masked slots (view+date)
  GET  /api/v1/scheduling/agenda/aggregates    — monthly counts (NO PHI)
  GET  /api/v1/scheduling/appointments/{id}    — drawer detail (PHI-masked)
  POST /api/v1/scheduling/appointments         — create appointment
  PATCH /api/v1/scheduling/appointments/{id}/status — status transition

HIPAA-lite obligations (vitalia/.claude/rules/hipaa-lite.md):
  - Dual filter: tenant_id + clinic_id MANDATORY on every PHI query.
  - Audit log sync write BEFORE returning response (mandatory PHI read log).
  - response_model= MANDATORY (PII allowlist enforcement; arch test enforces).
  - PHI NEVER in URL params — ALLOWED_GRID_PARAMS whitelist enforced.
  - X-Clinic-ID header MANDATORY on all routes.
  - require_phi_access(roles=...) dependency on all endpoints.
  - Cross-clinic returns 404 (NOT 403 — HIPAA-lite substrate: don't confirm existence).

Architecture:
  - Thin router: validate DTO → call service → map domain exception → HTTPException.
  - No business logic in api/ (backend-ddd.md).
  - FastAPI(redirect_slashes=False) enforced at main.py level.
  - AsyncSession injected via Depends(_get_db).
  - AsyncAuditWriter + GrowthStudioEmitter created per-request in DI factories.

downstream-regression-na: brand-local scheduling API for vitalia brand
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.scheduling.api.dtos.agenda_dtos import (
    AgendaAggregatesResponseDTO,
    AgendaGridResponseDTO,
    AgendaSlotDTO,
    AppointmentDetailDTO,
    CreateAppointmentRequestDTO,
    PatchAppointmentRequestDTO,
)
from src.modules.vitalia.scheduling.api.rbac import SCHEDULING_PHI_ROLES
from src.modules.vitalia.scheduling.application.services.agenda_grid_service import (
    AgendaGridService,
)
from src.modules.vitalia.scheduling.application.services.appointment_detail_service import (
    AppointmentDetailService,
)
from src.modules.vitalia.scheduling.application.services.appointment_status_service import (
    AppointmentStatusService,
)
from src.modules.vitalia.scheduling.application.services.create_appointment_service import (
    CreateAppointmentService,
)
from src.modules.vitalia.scheduling.domain.exceptions import (
    AppointmentNotFoundError,
    AppointmentOverlapError,
    OutOfWorkingHoursError,
    PastAppointmentError,
)
from src.modules.vitalia.scheduling.infrastructure.repositories.agenda_grid_repository_impl import (
    AgendaGridRepositoryImpl,
)
from src.modules.vitalia.scheduling.infrastructure.repositories.appointment_aggregates_repository import (
    AppointmentAggregatesRepository,
)
from src.modules.vitalia.scheduling.infrastructure.repositories.appointment_detail_repository import (
    AppointmentDetailRepository,
)

logger = structlog.get_logger()

router = APIRouter(tags=["scheduling"])

# ---------------------------------------------------------------------------
# PHI URL param whitelist (arch test test_no_phi_in_url_params.py enforces)
# ---------------------------------------------------------------------------

#: Hard whitelist of accepted query params for GET /agenda/grid.
#: ANY param outside this set is rejected + suspicious_request audit log written.
ALLOWED_GRID_PARAMS: frozenset[str] = frozenset(["view", "date", "preset_filter"])

#: PHI field names that must NEVER appear as URL query param keys.
#: Used by arch test test_no_phi_in_url_params.py ratchet scan.
_PHI_URL_PARAM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"patient_name", re.IGNORECASE),
    re.compile(r"patient_dni", re.IGNORECASE),
    re.compile(r"patient_phone", re.IGNORECASE),
    re.compile(r"patient_email", re.IGNORECASE),
    re.compile(r"\bdni\b", re.IGNORECASE),
    re.compile(r"\bphone\b", re.IGNORECASE),
    re.compile(r"\bname\b", re.IGNORECASE),
    re.compile(r"diagnosis", re.IGNORECASE),
    re.compile(r"medication", re.IGNORECASE),
)

#: PHI roles allowed to access scheduling PHI endpoints (hipaa-lite.md § RBAC).
#: Single source of truth lives in scheduling.api.rbac — re-exported here so every
#: endpoint in this router (and the legacy `ALLOWED_PHI_ROLES` references) stays in
#: sync with notify_router. Includes `owner` (clinic owner) per Chris ratification.
ALLOWED_PHI_ROLES: frozenset[str] = SCHEDULING_PHI_ROLES


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


async def _get_db() -> AsyncSession:
    """Async DB session dependency — COMMITTING unit-of-work.

    Uses ``get_async_session_committing`` (commits on clean return, rolls back on
    error). These scheduling endpoints read PHI and therefore MUST persist a sync
    audit-log row (hipaa-lite.md § Audit log: sync write pre-response). The plain
    ``get_async_session`` never commits → the audit INSERT was flushed-then-rolled-back
    at session close (HTTP 200 with no audit row). Surfaced by live verification in
    vitalia-bugfix-agenda-actor-headers-422 T-2 (same class as the CRM PHI-audit fix).
    """
    from src.db import get_async_session_committing  # noqa: PLC0415

    async for session in get_async_session_committing():
        yield session


def _detect_phi_params(params: dict[str, Any]) -> list[str]:
    """Return list of param keys that look like PHI.

    Used for suspicious_request audit log: captures KEYS only, not VALUES.
    Never logs the actual PHI value.
    """
    phi_keys: list[str] = []
    for key in params:
        for pattern in _PHI_URL_PARAM_PATTERNS:
            if pattern.search(key):
                phi_keys.append(key)
                break
    return phi_keys


async def _write_suspicious_request_audit(
    *,
    db: AsyncSession,
    tenant_id: UUID,
    clinic_id: UUID,
    user_id: UUID,
    request: Request,
    bypass_params: list[str],
) -> None:
    """Write suspicious_request audit log row (PHI param attempted in URL).

    Captures the rejected param keys (NOT values) + client IP + UA.
    Per 03-arch § 5.2: audit row emitted synchronously before rejecting.
    """
    audit = AsyncAuditWriter(session=db)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")

    await audit.write(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        action="suspicious_request",
        resource_type="agenda_grid",
        resource_id=clinic_id,
        payload={
            "path": str(request.url.path),
            "bypass_params": bypass_params,  # keys only — never PHI values
            "user_agent": user_agent,
        },
        from_ip=client_ip,
    )
    # Commit the security audit BEFORE the caller raises HTTP 400: the committing
    # session dependency rolls back on the raised HTTPException, which would otherwise
    # drop this suspicious_request row (the audit MUST survive the rejection).
    await db.commit()


# ---------------------------------------------------------------------------
# GET /api/v1/scheduling/agenda/grid
# ---------------------------------------------------------------------------


@router.get(
    "/agenda/grid",
    response_model=AgendaGridResponseDTO,
    summary="Agenda grid — PHI-masked slots for view+date",
    description=(
        "Returns calendar slots for the requested view and date range. "
        "All PHI fields are masked server-side. "
        "Dual filter tenant_id+clinic_id enforced. "
        "Audit log written synchronously. "
        "PHI params in query string are rejected + suspicious_request audit written."
    ),
)
async def get_agenda_grid(
    request: Request,
    view: str = Query(default="semana", description="Calendar view: dia|semana|mes"),
    date: str = Query(
        default=None,
        description="ISO date YYYY-MM-DD (defaults to today if omitted)",
    ),
    preset_filter: str | None = Query(
        default=None,
        # Valid: hoy|por_confirmar_manana|reagendar_pendientes|no_shows_dia|saldos_pendientes
        description="Optional preset filter key. See AgendaPresetFilter enum.",
    ),
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> AgendaGridResponseDTO:
    """GET /api/v1/scheduling/agenda/grid — PHI-masked agenda slots.

    HIPAA-lite enforcement:
    - RBAC check: user_role must be in ALLOWED_PHI_ROLES (403 if not).
    - PHI param whitelist: any extra query param → suspicious_request audit + 400.
    - Dual filter enforced at repo level (tenant_id + clinic_id).
    - Audit log written sync BEFORE returning.
    - Cross-clinic → empty slots list (dual filter rejects at DB).
    """
    # RBAC check (hipaa-lite.md § Access control)
    if user_role not in ALLOWED_PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "PHI_RBAC_DENIED", "message": "Acceso no autorizado a datos clínicos."},
        )

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    # PHI URL param whitelist check (arch gate: test_no_phi_in_url_params.py)
    all_query_params = dict(request.query_params)
    unknown_params = {k for k in all_query_params if k not in ALLOWED_GRID_PARAMS}
    phi_params = _detect_phi_params(all_query_params)
    suspicious_params = list(unknown_params | set(phi_params))

    if suspicious_params:
        await _write_suspicious_request_audit(
            db=db,
            tenant_id=tid,
            clinic_id=cid,
            user_id=uid,
            request=request,
            bypass_params=suspicious_params,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_QUERY_PARAMS",
                "message": "Parámetros de consulta no permitidos. Solo se aceptan: view, date, preset_filter.",
                "rejected_params": suspicious_params,
            },
        )

    # Compute date range from view + date
    from src.modules.vitalia.scheduling.api._date_utils import compute_date_range  # noqa: PLC0415

    today_str = date or datetime.now(tz=timezone.utc).date().isoformat()
    date_from, date_to = compute_date_range(view=view, date_str=today_str)

    # Build service + call
    audit_writer = AsyncAuditWriter(session=db)
    grid_repo = AgendaGridRepositoryImpl(session=db)
    service = AgendaGridService(repo=grid_repo, audit_writer=audit_writer)

    slots_raw = await service.list_slots(
        tenant_id=tid,
        clinic_id=cid,
        date_from=date_from,
        date_to=date_to,
        user_id=uid,
        preset_filter=preset_filter,
    )

    # Map raw dicts to DTOs
    slots = [
        AgendaSlotDTO(
            appointment_id=UUID(str(s["appointment_id"])),
            patient_id=UUID(str(s["patient_id"])) if s.get("patient_id") else UUID(int=0),
            patient_name_masked=str(s.get("patient_name_masked", "—")),
            start_time=(
                s["start_time"]
                if isinstance(s["start_time"], datetime)
                else datetime.fromisoformat(str(s["start_time"]))
            ),
            end_time=(
                s["end_time"] if isinstance(s["end_time"], datetime) else datetime.fromisoformat(str(s["end_time"]))
            ),
            doctor_id=UUID(str(s["doctor_id"])) if s.get("doctor_id") else UUID(int=0),
            doctor_label=str(s.get("doctor_label", "—")),
            service_label=str(s.get("service_label", "—")),
            appointment_status=str(s.get("appointment_status", "SCHEDULED")),
            payment_status=str(s.get("payment_status", "sin_pago")),
            origin=str(s.get("origin", "walk_in")),
            balance_due_cents=s.get("balance_due_cents"),
            balance_paid_cents=s.get("balance_paid_cents"),
            currency=str(s.get("currency", "PEN")),
        )
        for s in slots_raw
    ]

    logger.info("agenda_grid_served", tenant_id=tenant_id, clinic_id=clinic_id, slot_count=len(slots))

    return AgendaGridResponseDTO(
        view=view,
        date_from=date_from,
        date_to=date_to,
        slots=slots,
        server_time=datetime.now(tz=timezone.utc),
        clinic_id=cid,
        tenant_id=tid,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/scheduling/agenda/aggregates
# ---------------------------------------------------------------------------


@router.get(
    "/agenda/aggregates",
    response_model=AgendaAggregatesResponseDTO,
    summary="Monthly aggregates — slot counts per day (PHI-free)",
    description=(
        "Returns slot counts per calendar day for a given month. "
        "PHI-free: only integer counts. Used by react-window virtualized month grid."
    ),
)
async def get_agenda_aggregates(
    month: str = Query(
        ...,
        description="Target month in YYYY-MM format (e.g. 2026-05)",
        pattern=r"^\d{4}-\d{2}$",
    ),
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> AgendaAggregatesResponseDTO:
    """GET /api/v1/scheduling/agenda/aggregates — monthly slot counts.

    PHI-free: returns only integer counts per day.
    Dual filter tenant_id + clinic_id enforced at repo.
    No audit log required (no PHI exposure).
    """
    if user_role not in ALLOWED_PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "PHI_RBAC_DENIED", "message": "Acceso no autorizado a datos clínicos."},
        )

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)

    try:
        year_str, month_str = month.split("-")
        year = int(year_str)
        month_num = int(month_str)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_MONTH_FORMAT", "message": "Formato de mes inválido. Use YYYY-MM."},
        ) from exc

    agg_repo = AppointmentAggregatesRepository(session=db)
    rows = await agg_repo.count_per_day(
        tenant_id=tid,
        clinic_id=cid,
        year=year,
        month=month_num,
    )

    from src.modules.vitalia.scheduling.api.dtos.agenda_dtos import _DayAggregate  # noqa: PLC0415

    days = [
        _DayAggregate(
            date=str(row.get("slot_date", "")),
            total_slots=int(row.get("slot_count", 0)),
            status_breakdown={},
        )
        for row in rows
    ]

    return AgendaAggregatesResponseDTO(month=month, days=days)


# ---------------------------------------------------------------------------
# GET /api/v1/scheduling/appointments/{appointment_id}
# ---------------------------------------------------------------------------


@router.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentDetailDTO,
    summary="Appointment drawer detail — PHI-masked",
    description=(
        "Returns full PHI-masked appointment detail for the right-side drawer. "
        "Audit log row written synchronously (mandatory PHI read log). "
        "Cross-clinic returns 404 (NOT 403 — HIPAA-lite substrate)."
    ),
)
async def get_appointment_detail(
    appointment_id: UUID,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> AppointmentDetailDTO:
    """GET /api/v1/scheduling/appointments/{appointment_id} — drawer detail.

    HIPAA-lite:
    - Audit log written BEFORE returning (mandatory PHI read log).
    - Even on 404 (cross-clinic attempt), audit is written (suspicious access pattern).
    - Cross-clinic → 404 (NOT 403 — do NOT confirm appointment existence to other clinic).
    """
    if user_role not in ALLOWED_PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "PHI_RBAC_DENIED", "message": "Acceso no autorizado a datos clínicos."},
        )

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    audit_writer = AsyncAuditWriter(session=db)
    detail_repo = AppointmentDetailRepository(session=db)
    service = AppointmentDetailService(repo=detail_repo, audit_writer=audit_writer)

    try:
        detail = await service.get_detail(
            appointment_id=appointment_id,
            tenant_id=tid,
            clinic_id=cid,
            user_id=uid,
        )
    except AppointmentNotFoundError:
        # Cross-clinic or non-existent: return 404, NEVER 403
        # (hipaa-lite.md substrate: don't confirm existence to other clinic)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "APPOINTMENT_NOT_FOUND",
                "message": "Cita no encontrada.",
            },
        )

    return AppointmentDetailDTO.model_validate(detail)


# ---------------------------------------------------------------------------
# POST /api/v1/scheduling/appointments
# ---------------------------------------------------------------------------


@router.post(
    "/appointments",
    response_model=AppointmentDetailDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create appointment (walk-in/telefono/desde paciente existente)",
    description=(
        "Creates an appointment in the engine + brand-local clinic_map (A12). "
        "Audit log written synchronously (mandatory PHI write log). "
        "Growth studio telemetry emitted fire-forget after audit."
    ),
)
async def create_appointment(
    body: CreateAppointmentRequestDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> AppointmentDetailDTO:
    """POST /api/v1/scheduling/appointments — create appointment.

    T-BE-4: patient_id REQUIRED (real CRM patient). origin=walk_in|telefono only.
    Service persists engine appointment + brand-local clinic_map with mirror cols (A12).
    EXCLUDE constraint catches overlap → 409. Availability check → 422 OUT_OF_HOURS.
    Audit log row written sync. Growth telemetry fire-forget.
    """
    if user_role not in ALLOWED_PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "PHI_RBAC_DENIED", "message": "Acceso no autorizado a datos clínicos."},
        )

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    from src.modules.vitalia._shared.telemetry.growth_studio_emitter import (  # noqa: PLC0415
        GrowthStudioEmitter,
    )

    audit_writer = AsyncAuditWriter(session=db)
    growth_emitter = GrowthStudioEmitter(session=db)

    # Combined repo adapter: create + create_clinic_map + get_by_id (A12)
    combined_repo = AgendaGridRepositoryImpl(session=db)
    service = CreateAppointmentService(
        repo=combined_repo,
        audit_writer=audit_writer,
        growth_emitter=growth_emitter,
    )

    try:
        detail = await service.create_appointment(
            tenant_id=tid,
            clinic_id=cid,  # X-Clinic-ID header — HIPAA dual filter + NOT NULL
            offer_id=body.offer_id,  # T-BE-4 bugfix: offer FK (NOT NULL), from FE selectedServiceId
            user_id=uid,
            origin=body.origin,
            patient_id=body.patient_id,
            doctor_id=body.doctor_id,
            service_label=body.service_label,
            start_time=body.start_time,
            end_time=body.end_time,
            notes_internal=body.notes_internal,
            currency_override=body.currency_override,
        )
    except AppointmentOverlapError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "APPOINTMENT_OVERLAP",
                "message": "El horario solicitado se superpone con una cita existente. Selecciona otro horario.",
            },
        )
    except OutOfWorkingHoursError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "OUT_OF_HOURS",
                "message": "El horario solicitado está fuera del horario de atención.",
            },
        )
    except PastAppointmentError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "PAST_APPOINTMENT",
                "message": "No se pueden agendar citas en el pasado.",
            },
        )

    return AppointmentDetailDTO.model_validate(detail)


# ---------------------------------------------------------------------------
# PATCH /api/v1/scheduling/appointments/{appointment_id}/status
# ---------------------------------------------------------------------------


@router.patch(
    "/appointments/{appointment_id}/status",
    response_model=AppointmentDetailDTO,
    summary="Update appointment status (Confirmed/Cancelled/NoShow/Completed)",
    description=(
        "Transitions appointment status with audit log (from→to) and telemetry. "
        "Idempotent: same to_status = no-op. "
        "Cross-clinic → 404 (HIPAA-lite substrate). "
        "Audit log row: action=appointment.status_change, payload={from_status, to_status}."
    ),
)
async def patch_appointment_status(
    appointment_id: UUID,
    body: PatchAppointmentRequestDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    db: AsyncSession = Depends(_get_db),
) -> AppointmentDetailDTO:
    """PATCH /api/v1/scheduling/appointments/{id}/status — status transition.

    HIPAA-lite:
    - Audit log written sync with from_status → to_status payload.
    - Cross-clinic → 404 (not 403).
    - Growth telemetry emitted fire-forget after audit.
    """
    if user_role not in ALLOWED_PHI_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "PHI_RBAC_DENIED", "message": "Acceso no autorizado a datos clínicos."},
        )

    tid = UUID(tenant_id)
    cid = UUID(clinic_id)
    uid = UUID(user_id)

    from src.modules.vitalia._shared.telemetry.growth_studio_emitter import (  # noqa: PLC0415
        GrowthStudioEmitter,
    )

    audit_writer = AsyncAuditWriter(session=db)
    growth_emitter = GrowthStudioEmitter(session=db)
    detail_repo = AppointmentDetailRepository(session=db)
    service = AppointmentStatusService(
        repo=detail_repo,
        audit_writer=audit_writer,
        growth_emitter=growth_emitter,
    )

    try:
        updated = await service.change_status(
            appointment_id=appointment_id,
            tenant_id=tid,
            clinic_id=cid,
            new_status=body.new_status,
            reason=body.reason,
            user_id=uid,
        )
    except AppointmentNotFoundError:
        # Cross-clinic or non-existent: 404 (not 403)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "APPOINTMENT_NOT_FOUND",
                "message": "Cita no encontrada.",
            },
        )

    return AppointmentDetailDTO.model_validate(updated)
