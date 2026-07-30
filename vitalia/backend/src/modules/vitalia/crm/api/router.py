# cap: crm.crm-consent-optout
# story-origin: TBD
"""Vitalia CRM API router — patients, leads, and conversations endpoints.

API layer — thin: validate headers → resolve auth → call service → map exceptions → response.
No business logic here.

Endpoints:
  GET    /api/v1/crm/patients/{patient_id}                       — PHI gated (doctor/nurse/admin_clinic)
  PATCH  /api/v1/crm/patients/{patient_id}                       — PHI write gated
  POST   /api/v1/crm/patients/{patient_id}/opt-out               — admin_clinic only (consent_endpoints.py)
  PATCH  /api/v1/crm/patients/{patient_id}/marketing-opt-in      — doctor/nurse/admin_clinic (consent_endpoints.py)
  GET    /api/v1/crm/leads                                        — all authenticated roles (T-inbox-be-5)
  GET    /api/v1/crm/leads/{lead_id}                             — all authenticated roles
  POST   /api/v1/crm/leads                                        — all authenticated roles (T-inbox-be-5)
  PATCH  /api/v1/crm/leads/{lead_id}                             — all authenticated roles (T-inbox-be-5)
  GET    /api/v1/crm/conversations                                — PHI gated (T-inbox-be-5)
  GET    /api/v1/crm/conversations/{conv_id}                     — PHI gated (T-inbox-be-5)

response_model= is MANDATORY on every endpoint (PII gate + arch fitness).
redirect_slashes=False is set on the FastAPI *app* in main.py, NOT here.
PHIAccessDeniedError → HTTP 403 (mapped in exception handler below).

Slice 2 changes:
  - async_resolve() migration: all PHI endpoints use DB-sourced role.
  - Real PatientRepository wired via Depends(get_async_session_committing).
  - Real LeadRepository wired via Depends(get_async_session_committing).
  - AsyncMock() inline blocks REMOVED from all runtime paths.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session_committing
from src.modules.vitalia._shared.auth.rbac import PHIAccessDeniedError
from src.modules.vitalia._shared.encryption.kek_client import KEKClient
from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogRepository,
)
from src.modules.vitalia.crm.api.consent_endpoints import router as consent_router
from src.modules.vitalia.crm.application.dto.board_dto import BoardResponse
from src.modules.vitalia.crm.application.dto.conversation_detail_dto import (
    ConversationDetailConversation,
    ConversationDetailMessage,
    ConversationDetailResponse,
)
from src.modules.vitalia.crm.application.dto.frozen_dto import (
    DiagnoseResponse,
    FrozenListResponse,
    ReactivateRequest,
)
from src.modules.vitalia.crm.application.dto.lead_detail_dto import LeadDetailResponse
from src.modules.vitalia.crm.application.dto.lead_dto import (
    LeadCreateRequest,
    LeadListResponse,
    LeadResponse,
    LeadUpdateRequest,
)
from src.modules.vitalia.crm.application.dto.patient_dto import (
    PatientInlineCreateRequest,
    PatientInlineCreateResponse,
    PatientPatchRequest,
    PatientResponse,
    PatientSearchResponse,
)
from src.modules.vitalia.crm.application.dto.transition_dto import (
    StageTransitionRequest,
    StageTransitionResponse,
    TimelineResponse,
)
from src.modules.vitalia.crm.application.services.funnel_service import FunnelService
from src.modules.vitalia.crm.application.services.lead_service import (
    LeadNotFoundError,
    LeadService,
)
from src.modules.vitalia.crm.application.services.patient_service import PatientService
from src.modules.vitalia.crm.domain.exceptions import (
    InvalidTransitionError,
    ManualReservadoForbiddenError,
    ReasonRequiredError,
    StaleStateError,
)
from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
    ConversationRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.lead_activity_repository import (
    LeadActivityRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
    LeadRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.lead_stage_transition_repository import (
    LeadStageTransitionRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
    MessageRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
    PatientRepository,
)
from src.modules.vitalia.iam.application.services.clinic_resolver import (
    ClinicContext,
    ClinicResolver,
    MissingAuthHeaderError,
    RoleNotFoundError,
    UserNotFoundError,
)
from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
    ClerkJwtDecoder,
    JwtDecodeError,
)
from src.modules.vitalia.inbox.application.dto.conversation_list_dto import (
    ConversationListItem,
    ConversationListResponse,
)

logger = structlog.get_logger()

router = APIRouter(tags=["crm"])

# Mount consent endpoints (opt-out + marketing-opt-in)
router.include_router(consent_router)

# Header type aliases
AuthorizationHeader = Annotated[str, Header(alias="Authorization")]
TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]
ClinicIdHeader = Annotated[str, Header(alias="X-Clinic-ID")]
OptionalClinicIdHeader = Annotated[str | None, Header(alias="X-Clinic-ID")]


def _get_resolver() -> ClinicResolver:
    """Create a ClinicResolver with the default JWT decoder."""
    return ClinicResolver(decoder=ClerkJwtDecoder())


async def _resolve_context_async(
    authorization: str,
    x_tenant_id: str,
    x_clinic_id: str,
    session: AsyncSession,
) -> ClinicContext:
    """Parse authorization header and resolve clinic context via DB role.

    Slice 2 path: uses async_resolve() to get role from DB.
    Use for PHI endpoints that require dual filter (tenant + clinic).

    Raises:
        HTTPException(401): Token missing, invalid, or user not found in DB.
        HTTPException(403): User has no active role in this tenant.
    """
    token = authorization.removeprefix("Bearer ").strip()
    resolver = _get_resolver()
    try:
        return await resolver.async_resolve(
            token=token,
            session=session,
            tenant_id_str=x_tenant_id,
            clinic_id_str=x_clinic_id,
        )
    except MissingAuthHeaderError:
        raise HTTPException(status_code=401, detail="Token de autorización requerido.")
    except JwtDecodeError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    except UserNotFoundError:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")
    except RoleNotFoundError:
        raise HTTPException(status_code=403, detail="El usuario no tiene un rol activo en este tenant.")
    except ValueError:
        raise HTTPException(status_code=422, detail="Identificadores de tenant o clínica inválidos.")


def _resolve_context_sync(authorization: str, x_tenant_id: str) -> ClinicContext:
    """Parse authorization header and resolve clinic context (non-PHI, sync).

    For non-PHI lead endpoints: token validation + tenant_id from header.
    Clinic_id is not required (leads are tenant-scoped only, not clinic-scoped).
    Uses sync resolve() which reads tenant_id from header (not JWT for real tokens).

    Raises:
        HTTPException(401): Token missing or invalid.
    """
    token = authorization.removeprefix("Bearer ").strip()
    resolver = _get_resolver()
    try:
        # Decode token to validate it. For real JWTs: tenant_id/clinic_id empty from JWT.
        # We supply tenant_id from header for tenant isolation.
        ctx = resolver.resolve(token)
        # For real JWTs, tenant_id in ctx is UUID(int=0) from the empty payload field.
        # We must use x_tenant_id from the header as the authoritative tenant_id.
        from uuid import UUID  # noqa: PLC0415

        return ClinicContext(
            user_id=ctx.user_id,
            tenant_id=UUID(x_tenant_id),
            clinic_id=ctx.clinic_id,  # UUID(int=0) for real JWTs — unused in lead queries
            role=ctx.role,  # empty for real JWTs; stub path has role from token
            email=ctx.email,
            name=ctx.name,
        )
    except MissingAuthHeaderError:
        raise HTTPException(status_code=401, detail="Token de autorización requerido.")
    except JwtDecodeError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    except ValueError:
        raise HTTPException(status_code=422, detail="Identificadores de tenant inválidos.")


# ---------------------------------------------------------------------------
# Patient endpoints — PHI gated
# ---------------------------------------------------------------------------


@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> PatientResponse:
    """Retrieve a patient by ID — PHI access gated by RBAC.

    Allowed roles: doctor, nurse, admin_clinic.
    Marketing/receptionist/patient roles → 403.

    Args:
        patient_id: Patient UUID (path param).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (required — dual PHI filter).
        session: Async DB session (injected by FastAPI DI).

    Returns:
        PatientResponse with allowlisted fields.

    Raises:
        401: Invalid/missing token.
        403: Role not permitted to access PHI.
        404: Patient not found.
    """
    ctx = await _resolve_context_async(authorization, x_tenant_id, x_clinic_id, session)

    audit_repo = AuditLogRepository(session=session)
    patient_repo = PatientRepository(session=session, audit_repo=audit_repo, kek=KEKClient.from_env())
    service = PatientService(patient_repo=patient_repo, audit_repo=audit_repo)

    try:
        patient = await service.get_by_id(
            patient_id=patient_id,
            tenant_id=ctx.tenant_id,
            clinic_id=UUID(x_clinic_id),
            user_id=UUID(ctx.user_id) if len(ctx.user_id) == 36 else UUID(int=0),
            user_role=ctx.role,
        )
    except PHIAccessDeniedError:
        logger.warning(
            "crm.get_patient.access_denied",
            role=ctx.role,
            patient_id=str(patient_id),
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para acceder a información clínica.",
        )

    if patient is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    return PatientResponse(
        id=patient.id,
        tenant_id=patient.tenant_id,
        clinic_id=patient.clinic_id,
        name=patient.name,
        email=patient.email,
        phone=patient.phone,
        marketing_opt_out_at=patient.marketing_opt_out_at,
        created_at=patient.created_at,
    )


@router.post("/patients", response_model=PatientInlineCreateResponse, status_code=201)
async def create_patient_inline(
    body: PatientInlineCreateRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> PatientInlineCreateResponse:
    """Create a minimal patient record inline during nueva-cita flow.

    PHI transmitted in POST body ONLY — NEVER in URL params.
    Dual filter: tenant_id + clinic_id required.
    RN-9: if phone already exists → returns existing patient with is_duplicate=True.

    Allowed roles: doctor, nurse, admin_clinic.

    Args:
        body: PatientInlineCreateRequest (name, phone?, email?, channel, note?).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (required — dual PHI filter).
        session: Async DB session.

    Returns:
        PatientInlineCreateResponse with masked fields (name_masked, phone_masked).
        HTTP 201 Created on new patient. HTTP 200 when is_duplicate=True.

    Raises:
        401: Invalid/missing token.
        403: Role not permitted to create PHI records.
        422: Invalid request body.
    """
    ctx = await _resolve_context_async(authorization, x_tenant_id, x_clinic_id, session)

    audit_repo = AuditLogRepository(session=session)
    patient_repo = PatientRepository(session=session, audit_repo=audit_repo, kek=KEKClient.from_env())
    service = PatientService(patient_repo=patient_repo, audit_repo=audit_repo)

    try:
        result = await service.create_minimal(
            tenant_id=ctx.tenant_id,
            clinic_id=UUID(x_clinic_id),
            user_id=UUID(ctx.user_id) if len(ctx.user_id) == 36 else UUID(int=0),
            name=body.name,
            phone=body.phone,
            email=body.email,
            channel=body.channel,
            note=body.note,
        )
    except PHIAccessDeniedError:
        logger.warning(
            "crm.create_patient.access_denied",
            role=ctx.role,
            tenant_id=x_tenant_id,
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para crear pacientes.",
        )

    return result


@router.get("/patients", response_model=PatientSearchResponse)
async def search_patients(
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    q: str = Query(default="", max_length=100, description="Typeahead query"),
    cursor: UUID | None = Query(default=None, description="Pagination cursor (patient UUID)"),
    limit: int = Query(default=20, ge=1, le=50, description="Page size"),
) -> PatientSearchResponse:
    """Typeahead patient search for nueva-cita picker.

    PHI NEVER in URL — q= is generic search term, not name/dni/phone directly.
    Results are always masked (name_masked, phone_masked) — raw PHI never returned.
    Cursor-based pagination for 1500+ row datasets.

    Dual filter: tenant_id + clinic_id required.
    Allowed roles: doctor, nurse, admin_clinic.

    Args:
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header.
        session: Async DB session.
        q: Typeahead search term (applied to decrypted name).
        cursor: Optional pagination cursor.
        limit: Page size (1-50, default 20).

    Returns:
        PatientSearchResponse with masked items + next_cursor + total_approx.

    Raises:
        401: Invalid/missing token.
        403: Role not permitted to search PHI.
    """
    ctx = await _resolve_context_async(authorization, x_tenant_id, x_clinic_id, session)

    audit_repo = AuditLogRepository(session=session)
    patient_repo = PatientRepository(session=session, audit_repo=audit_repo, kek=KEKClient.from_env())
    service = PatientService(patient_repo=patient_repo, audit_repo=audit_repo)

    try:
        return await service.search(
            tenant_id=ctx.tenant_id,
            clinic_id=UUID(x_clinic_id),
            user_id=UUID(ctx.user_id) if len(ctx.user_id) == 36 else UUID(int=0),
            q=q,
            cursor=cursor,
            limit=limit,
        )
    except PHIAccessDeniedError:
        logger.warning(
            "crm.search_patients.access_denied",
            role=ctx.role,
            tenant_id=x_tenant_id,
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para buscar pacientes.",
        )


@router.patch("/patients/{patient_id}", response_model=PatientResponse)
async def patch_patient(
    patient_id: UUID,
    body: PatientPatchRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> PatientResponse:
    """Update allowed patient fields — PHI write gated by RBAC.

    Allowed roles: doctor, nurse, admin_clinic.

    Args:
        patient_id: Patient UUID (path param).
        body: Fields to update.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header.
        session: Async DB session (injected by FastAPI DI).

    Returns:
        Updated PatientResponse.

    Raises:
        401: Invalid/missing token.
        403: Role not permitted to write PHI.
        404: Patient not found.
    """
    ctx = await _resolve_context_async(authorization, x_tenant_id, x_clinic_id, session)

    audit_repo = AuditLogRepository(session=session)
    patient_repo = PatientRepository(session=session, audit_repo=audit_repo, kek=KEKClient.from_env())
    service = PatientService(patient_repo=patient_repo, audit_repo=audit_repo)

    updates = {k: v for k, v in body.model_dump().items() if v is not None}

    try:
        await service.update(
            patient_id=patient_id,
            tenant_id=ctx.tenant_id,
            clinic_id=UUID(x_clinic_id),
            user_id=UUID(ctx.user_id) if len(ctx.user_id) == 36 else UUID(int=0),
            user_role=ctx.role,
            updates=updates,
        )
    except PHIAccessDeniedError:
        logger.warning(
            "crm.patch_patient.access_denied",
            role=ctx.role,
            patient_id=str(patient_id),
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para modificar información clínica.",
        )

    # Fetch updated patient to return
    patient = await service.get_by_id(
        patient_id=patient_id,
        tenant_id=ctx.tenant_id,
        clinic_id=UUID(x_clinic_id),
        user_id=UUID(ctx.user_id) if len(ctx.user_id) == 36 else UUID(int=0),
        user_role=ctx.role,
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    return PatientResponse(
        id=patient.id,
        tenant_id=patient.tenant_id,
        clinic_id=patient.clinic_id,
        name=patient.name,
        email=patient.email,
        phone=patient.phone,
        marketing_opt_out_at=patient.marketing_opt_out_at,
        created_at=patient.created_at,
    )


# opt-out endpoint moved to consent_endpoints.py (PatientConsentService)
# router.include_router(consent_router) above mounts it at the same path.

# ---------------------------------------------------------------------------
# Lead endpoints — non-PHI, all authenticated roles
# ---------------------------------------------------------------------------


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> LeadResponse:
    """Retrieve a lead by ID — accessible to all authenticated roles.

    Lead is not PHI — no clinic_id dual filter required.
    X-Clinic-ID header is optional for this endpoint.

    Args:
        lead_id: Lead UUID (path param).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session (injected by FastAPI DI).
        x_clinic_id: Optional Clinic ID (not required for non-PHI).

    Returns:
        LeadResponse.

    Raises:
        401: Invalid/missing token.
        404: Lead not found.
    """
    # Non-PHI leads: use sync resolve (role not needed for leads) or a minimal async resolve
    # For simplicity and correctness, use async_resolve with x_clinic_id fallback
    ctx = _resolve_context_sync(authorization, x_tenant_id)

    lead_repo = LeadRepository(session=session, kek=KEKClient.from_env())
    service = LeadService(lead_repo=lead_repo)

    lead = await service.get_by_id(
        lead_id=lead_id,
        tenant_id=ctx.tenant_id,
    )

    if lead is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

    return LeadResponse(
        id=lead.id,
        tenant_id=lead.tenant_id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=lead.status,
        created_at=lead.created_at,
    )


# ---------------------------------------------------------------------------
# Lead endpoints — T-inbox-be-5 extension (non-PHI, all authenticated roles)
# ---------------------------------------------------------------------------


@router.get("/leads", response_model=LeadListResponse)
async def list_leads(
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
    status: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LeadListResponse:
    """List leads for the inbox — all authenticated roles.

    Lead is not PHI — no clinic_id dual filter required.

    Args:
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session (injected by FastAPI DI).
        x_clinic_id: Optional Clinic ID (not required for non-PHI).
        status: Optional status filter.
        source: Optional source filter.
        limit: Page size (default 20, max 100).
        offset: Page offset.

    Returns:
        LeadListResponse (paginated).

    Raises:
        401: Invalid/missing token.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)

    lead_repo = LeadRepository(session=session, kek=KEKClient.from_env())
    service = LeadService(lead_repo=lead_repo)

    leads, total = await service.list_for_inbox(
        tenant_id=ctx.tenant_id,
        status=status,
        source=source,
        limit=limit,
        offset=offset,
    )

    items = [
        LeadResponse(
            id=lead.id,
            tenant_id=lead.tenant_id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            source=lead.source,
            status=lead.status,
            created_at=lead.created_at,
        )
        for lead in leads
    ]
    return LeadListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/leads", response_model=LeadResponse, status_code=201)
async def create_lead(
    body: LeadCreateRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> LeadResponse:
    """Create a new lead — all authenticated roles.

    Lead is not PHI — no clinic_id required.

    Args:
        body: LeadCreateRequest.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session (injected by FastAPI DI).
        x_clinic_id: Optional Clinic ID (not required for non-PHI).

    Returns:
        LeadResponse (201 Created).

    Raises:
        401: Invalid/missing token.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)

    lead_repo = LeadRepository(session=session, kek=KEKClient.from_env())
    service = LeadService(lead_repo=lead_repo)

    lead = await service.create(
        tenant_id=ctx.tenant_id,
        name=body.name,
        email=body.email,
        phone=body.phone,
        source=body.source,
        status=body.status,
        notes=body.notes,
        marketing_opt_in=body.marketing_opt_in,
        stage=body.stage,
        channel=body.channel,
        service_interest=body.service_interest,
        # body.tags aceptado en el DTO pero NO persistido (sin columna en vitalia_leads)
        estimated_value=body.estimated_value,
        currency=body.currency,
    )

    return LeadResponse(
        id=lead.id,
        tenant_id=lead.tenant_id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=lead.status,
        created_at=lead.created_at,
    )


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    body: LeadUpdateRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> LeadResponse:
    """Update allowed lead fields — all authenticated roles.

    Lead is not PHI — no clinic_id required.

    Args:
        lead_id: Lead UUID (path param).
        body: LeadUpdateRequest (all fields optional).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session (injected by FastAPI DI).
        x_clinic_id: Optional Clinic ID.

    Returns:
        LeadResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        404: Lead not found.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)

    lead_repo = LeadRepository(session=session, kek=KEKClient.from_env())
    service = LeadService(lead_repo=lead_repo)

    updates = {k: v for k, v in body.model_dump().items() if v is not None}

    try:
        await service.update(
            lead_id=lead_id,
            tenant_id=ctx.tenant_id,
            updates=updates,
        )
    except LeadNotFoundError:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

    lead = await service.get_by_id(
        lead_id=lead_id,
        tenant_id=ctx.tenant_id,
    )
    if lead is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

    return LeadResponse(
        id=lead.id,
        tenant_id=lead.tenant_id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=lead.status,
        created_at=lead.created_at,
    )


# ---------------------------------------------------------------------------
# Funnel service builder (DI helper)
# ---------------------------------------------------------------------------


def _build_funnel_service(session: AsyncSession) -> FunnelService:
    """Build FunnelService with all dependencies wired.

    Separated from endpoints to allow patching in tests.
    """
    from src.modules.vitalia._shared.telemetry.growth_studio_emitter import (  # noqa: PLC0415
        GrowthStudioEmitter,
    )

    lead_repo = LeadRepository(session=session, kek=KEKClient.from_env())
    transition_repo = LeadStageTransitionRepository(session=session)
    activity_repo = LeadActivityRepository(session=session)
    emitter = GrowthStudioEmitter(session=session)

    # event_bus: use luana_core_events OutboxEventBus if available, else stub
    try:
        from luana_core_events.outbox.adapter_bus import OutboxEventBus  # noqa: PLC0415

        event_bus = OutboxEventBus(session=session)
    except ImportError:
        # Stub for tests / environments where outbox is not wired yet
        class _StubBus:
            async def publish(self, event: dict) -> None:  # noqa: ANN001
                logger.debug("outbox_event_stub", event_type=event.get("event_type"))

        event_bus = _StubBus()

    return FunnelService(
        lead_repo=lead_repo,
        transition_repo=transition_repo,
        activity_repo=activity_repo,
        emitter=emitter,
        event_bus=event_bus,
    )


# ---------------------------------------------------------------------------
# Funnel board endpoints — T-BE-2 (vitalia-fase2-adrian-embudo)
# ---------------------------------------------------------------------------


@router.get("/board", response_model=BoardResponse)
async def get_board(
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
    sort: str | None = Query(default=None),
) -> BoardResponse:
    """Get funnel board with HOT_BOARD_STAGES columns + KPI strip.

    Non-PHI lead data. All authenticated roles can access.
    Board shows only active stages (interesado/calificando/consulta/plan + reservado).
    Frozen leads and decidio_no → GET /crm/frozen.

    Args:
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session.
        x_clinic_id: Optional clinic ID (not required for non-PHI leads).
        sort: Sort mode (stage_age_desc | score_desc | value_desc | activity_desc).

    Returns:
        BoardResponse (200 OK).

    Raises:
        401: Invalid/missing token.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)
    service = _build_funnel_service(session)

    result = await service.get_board(
        tenant_id=ctx.tenant_id,
        stage_filter=None,
        sort=sort or "stage_age_desc",
    )
    return result


@router.patch("/leads/{lead_id}/stage", response_model=StageTransitionResponse)
async def patch_lead_stage(
    lead_id: UUID,
    body: StageTransitionRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> StageTransitionResponse:
    """Transition a lead's funnel stage with optimistic lock + audit trail.

    SC-2: invalid transition → 422 {detail, allowed_next}.
    SC-4: lead not found → 404 (no info leak cross-tenant).
    SC-5: version conflict → 409 Conflict.
    RN-4: manual reservado → 403 Forbidden.
    RN-4.1: reason persisted in transition + emits outbox event for T-AG-1.

    Args:
        lead_id: Lead UUID (path param).
        body: StageTransitionRequest.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session.
        x_clinic_id: Optional clinic ID.

    Returns:
        StageTransitionResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Manual reservado attempt (RN-4).
        404: Lead not found (cross-tenant or deleted).
        409: Optimistic lock conflict (SC-5).
        422: Invalid stage transition (SC-2) — body includes allowed_next list.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)
    service = _build_funnel_service(session)

    actor_user_id: UUID | None = None
    try:
        if len(ctx.user_id) == 36:
            actor_user_id = UUID(ctx.user_id)
    except ValueError:
        pass

    try:
        result = await service.transition_stage(
            lead_id=lead_id,
            tenant_id=ctx.tenant_id,
            to_stage=body.to_stage,
            version=body.version,
            reason=body.reason,
            triggered_by=body.triggered_by,
            actor_user_id=actor_user_id,
        )
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": f"Transición inválida: {exc.from_stage} → {exc.to_stage}.",
                "allowed_next": exc.allowed_next,
            },
        ) from exc
    except ManualReservadoForbiddenError as exc:
        raise HTTPException(
            status_code=403,
            detail="La etapa 'Reservado' solo puede establecerse mediante confirmación de pago.",
        ) from exc
    except ReasonRequiredError as exc:
        raise HTTPException(
            status_code=400,
            detail="Se requiere una razón para este cambio de etapa.",
        ) from exc
    except StaleStateError as exc:
        raise HTTPException(
            status_code=409,
            detail="Conflicto de versión: el prospecto fue modificado simultáneamente. Recarga y reintenta.",
        ) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

    return result


@router.get("/leads/{lead_id}/detail", response_model=LeadDetailResponse)
async def get_lead_detail(
    lead_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> LeadDetailResponse:
    """Get full lead detail for workspace Resumen tab.

    PHI firewall: no clinical fields (RN-2). Historial tab = separate endpoint.
    Includes: lead record + glass-box score breakdown + autonomy info.

    Args:
        lead_id: Lead UUID.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session.
        x_clinic_id: Optional clinic ID.

    Returns:
        LeadDetailResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        404: Lead not found.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)
    service = _build_funnel_service(session)

    result = await service.get_lead_detail(
        lead_id=lead_id,
        tenant_id=ctx.tenant_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
    return result


@router.get("/leads/{lead_id}/transitions", response_model=TimelineResponse)
async def get_lead_transitions(
    lead_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> TimelineResponse:
    """Get commercial activity timeline for lead Historial tab.

    PHI firewall: NON-PHI commercial micro-log only (RN-2).
    Clinical data stays in PHI-gated Inbox.

    Args:
        lead_id: Lead UUID.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session.
        x_clinic_id: Optional clinic ID.

    Returns:
        TimelineResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        404: Lead not found.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)
    service = _build_funnel_service(session)

    result = await service.get_timeline(
        lead_id=lead_id,
        tenant_id=ctx.tenant_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
    return result


@router.get("/frozen", response_model=FrozenListResponse)
async def get_frozen_leads(
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> FrozenListResponse:
    """Get frozen leads + decidio_no leads for Recuperar sub-tab.

    Returns two lists:
    - recien_congelados: leads with is_frozen=True
    - decidio_no: leads with stage=decidio_no

    Args:
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session.
        x_clinic_id: Optional clinic ID.

    Returns:
        FrozenListResponse (200 OK).

    Raises:
        401: Invalid/missing token.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)
    service = _build_funnel_service(session)

    return await service.get_frozen_list(tenant_id=ctx.tenant_id)


@router.post("/leads/{lead_id}/diagnose", response_model=DiagnoseResponse)
async def diagnose_lead(
    lead_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> DiagnoseResponse:
    """Diagnose a frozen lead and return reactivation recommendation.

    Deterministic rules (no ML). Based on frozen_reason + stage + buying signals.

    Args:
        lead_id: Lead UUID.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session.
        x_clinic_id: Optional clinic ID.

    Returns:
        DiagnoseResponse with recommendation_es + suggested_action.

    Raises:
        401: Invalid/missing token.
        404: Lead not found.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)
    service = _build_funnel_service(session)

    result = await service.diagnose(lead_id=lead_id, tenant_id=ctx.tenant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
    return result


@router.post("/leads/{lead_id}/reactivate", response_model=LeadResponse)
async def reactivate_lead(
    lead_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
    body: ReactivateRequest | None = None,
) -> LeadResponse:
    """Reactivate a frozen lead — clear frozen state.

    Records a reactivation activity in the commercial micro-log.

    Args:
        lead_id: Lead UUID.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session.
        x_clinic_id: Optional clinic ID.
        body: Optional reactivation context (NON-PHI objective).

    Returns:
        Updated LeadResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        404: Lead not found.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)
    service = _build_funnel_service(session)

    lead = await service.reactivate(
        lead_id=lead_id,
        tenant_id=ctx.tenant_id,
        objective=body.objective if body else None,
    )
    if lead is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

    from src.modules.vitalia.crm.application.services.funnel_service import _lead_to_response  # noqa: PLC0415

    return _lead_to_response(lead)


@router.post("/leads/{lead_id}/reservado-side-effect", response_model=LeadResponse)
async def reservado_side_effect_stub(
    lead_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    x_clinic_id: OptionalClinicIdHeader = None,
) -> LeadResponse:
    """Stub for reservado side-effect webhook (payment confirmation).

    RN-5: reservado stage can ONLY be set via this webhook (not manual drag/dropdown).
    Currently stubbed via MSW for this story — real payment integration in future story.
    Idempotent: if deposit_status already 'received', returns current lead unchanged.

    Args:
        lead_id: Lead UUID.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        session: Async DB session.
        x_clinic_id: Optional clinic ID.

    Returns:
        LeadResponse (200 OK — stub always succeeds or 404 if not found).

    Raises:
        401: Invalid/missing token.
        404: Lead not found.
    """
    ctx = _resolve_context_sync(authorization, x_tenant_id)

    lead_repo = LeadRepository(session=session, kek=KEKClient.from_env())
    lead = await lead_repo.get_by_id(lead_id, tenant_id=ctx.tenant_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")

    logger.info(
        "reservado_side_effect_stub",
        lead_id=str(lead_id),
        tenant_id=str(ctx.tenant_id),
        deposit_status=lead.deposit_status,
    )

    # Stub: return current lead (real webhook logic in future story)
    return LeadResponse(
        id=lead.id,
        tenant_id=lead.tenant_id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=lead.status,
        created_at=lead.created_at,
        stage=lead.stage,
        score=lead.score,
        temperature=lead.temperature,
        operated_by=lead.operated_by,
        channel=lead.channel,
        estimated_value=lead.estimated_value,
        currency=lead.currency,
        service_interest=lead.service_interest,
        buying_signals=list(lead.buying_signals),
        stage_entered_at=lead.stage_entered_at,
        is_frozen=lead.is_frozen,
        frozen_reason=lead.frozen_reason,
        deposit_status=lead.deposit_status,
        version=lead.version,
    )


# ---------------------------------------------------------------------------
# Conversation list + detail — T-inbox-be-5 extension (PHI gated)
# ---------------------------------------------------------------------------

_PHI_ROLES = frozenset({"doctor", "nurse", "admin_clinic"})

# Commercial inbox triage (Chris 2026-06-04): the conversation list/thread is the
# operator's tool (front desk + owner), not strict clinical PHI. Owner + receptionist
# may list/open conversations. Patient clinical PHI (medical record, ContactSidebar
# reveal — patient_service) stays gated to _PHI_ROLES.
_INBOX_OPERATOR_ROLES = _PHI_ROLES | frozenset({"owner", "receptionist"})


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
    status: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    handler_mode: str | None = Query(default=None),
    help_needed: bool | None = Query(default=None),
    unread_media: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ConversationListResponse:
    """List inbox conversations — PHI gated.

    Dual PHI filter: tenant_id + clinic_id required.
    Returns paginated ConversationListResponse.

    Args:
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter — mandatory).
        session: Async DB session (injected by FastAPI DI).
        status: Optional status filter.
        channel: Optional channel filter.
        handler_mode: Optional handler_mode filter.
        help_needed: Optional help_needed filter.
        unread_media: Optional unread_media filter.
        limit: Page size.
        offset: Page offset.

    Returns:
        ConversationListResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted to access PHI conversations.
    """
    ctx = await _resolve_context_async(authorization, x_tenant_id, x_clinic_id, session)

    if ctx.role not in _INBOX_OPERATOR_ROLES:
        logger.warning(
            "crm.list_conversations.access_denied",
            role=ctx.role,
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para ver la bandeja.",
        )

    repo = ConversationRepository(session=session)
    rows = await repo.list_for_inbox(
        tenant_id=ctx.tenant_id,
        clinic_id=ctx.clinic_id,
        status=status,
        channel=channel,
        handler_mode=handler_mode,
        limit=limit,
        offset=offset,
    )
    items = [ConversationListItem.model_validate(row) for row in rows]
    # NOTE: total is the page count (no separate COUNT query yet — fine for MVP page sizes).
    return ConversationListResponse(
        items=items,
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/conversations/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conv_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> ConversationDetailResponse:
    """Get the compound conversation detail (thread) — PHI gated.

    Returns the full compound the inbox thread consumes:
    ``{ conversation, lead, messages, action_receipts, tools_state }``
    (FE ``ConversationDetail``). Dual PHI filter: tenant_id + clinic_id.

    Args:
        conv_id: Conversation UUID.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter — mandatory).
        session: Async DB session (injected by FastAPI DI).

    Returns:
        ConversationDetailResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted.
        404: Conversation not found.
    """
    ctx = await _resolve_context_async(authorization, x_tenant_id, x_clinic_id, session)

    if ctx.role not in _INBOX_OPERATOR_ROLES:
        logger.warning(
            "crm.get_conversation_detail.access_denied",
            role=ctx.role,
            conv_id=str(conv_id),
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para ver esta conversación.",
        )

    conv_repo = ConversationRepository(session=session)
    conv = await conv_repo.get_by_id(id=conv_id, tenant_id=ctx.tenant_id, scope_id=ctx.clinic_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    # Messages (dual-filter, chronological)
    msg_repo = MessageRepository(session=session)
    raw_messages = await msg_repo.list_for_conversation(
        conversation_id=conv_id,
        tenant_id=ctx.tenant_id,
        clinic_id=ctx.clinic_id,
        limit=50,
    )
    messages = [ConversationDetailMessage.model_validate(m) for m in raw_messages]

    # Lead (decrypted PHI name/email/phone — single tenant filter; Lead is the contact)
    lead_response: LeadResponse | None = None
    if conv.lead_id is not None:
        lead_repo = LeadRepository(session=session, kek=KEKClient.from_env())
        lead = await lead_repo.get_by_id(conv.lead_id, tenant_id=ctx.tenant_id)
        if lead is not None:
            lead_response = LeadResponse(
                id=lead.id,
                tenant_id=lead.tenant_id,
                name=lead.name,
                email=lead.email,
                phone=lead.phone,
                source=lead.source,
                status=lead.status,
                created_at=lead.created_at,
                stage=lead.stage,
                score=lead.score,
                temperature=lead.temperature,
                operated_by=lead.operated_by,
                channel=lead.channel,
                estimated_value=lead.estimated_value,
                currency=lead.currency,
                service_interest=lead.service_interest,
                buying_signals=lead.buying_signals,
                stage_entered_at=lead.stage_entered_at,
                is_frozen=lead.is_frozen,
                frozen_reason=lead.frozen_reason,
                deposit_status=lead.deposit_status,
                version=lead.version,
            )

    return ConversationDetailResponse(
        conversation=ConversationDetailConversation.model_validate(conv),
        lead=lead_response,
        messages=messages,
        action_receipts=[],
        tools_state=None,
    )
