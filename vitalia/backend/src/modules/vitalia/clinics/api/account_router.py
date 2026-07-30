# cap: configuracion.cuenta
"""Vitalia Clinic Account router — FastAPI thin layer.

Routes (prefix /api/v1/clinics/account — registered in main.py):
  GET  /                     — get clinic account data (all authenticated roles)
  PATCH /                    — update clinic account (admin_clinic only)
  GET  /specialties-catalog  — get specialty catalog for clinic's country
  GET  /dpo                  — get DPO (Responsable tratamiento) reference

Architecture rules:
  - response_model= is MANDATORY on all routes (arch test enforces)
  - X-Tenant-ID + X-User-ID headers required on all routes
  - X-User-Role header required for PATCH (RBAC)
  - No business logic in router — delegate to ClinicAccountService
  - Map domain exceptions → HTTPException (ClinicNotFoundError→404,
    PermissionError→403, FiscalIdValidationError→422)
  - FastAPI(redirect_slashes=False) in main.py (enforced globally)
"""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Header, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.catalogs.specialty_catalog import (
    SpecialtyValidationError,
)
from src.modules.vitalia._shared.validation.fiscal_id_validator import (
    FiscalIdValidationError,
)
from src.modules.vitalia.clinics.api.dtos import (
    ClinicAccountPatchRequest,
    ClinicAccountResponse,
    DpoReferenceResponse,
    SpecialtyCatalogResponse,
)
from src.modules.vitalia.clinics.application.clinic_account_service import (
    ClinicAccountService,
)
from src.modules.vitalia.clinics.domain.exceptions import ClinicNotFoundError
from src.modules.vitalia.iam.application.services.clinic_resolver import UserNotFoundError
from src.modules.vitalia.iam.application.services.user_resolver import (
    resolve_user_uuid_from_clerk_id,
)

logger = structlog.get_logger()

router = APIRouter(tags=["account"])


async def _resolve_audit_actor(session: AsyncSession, user_id_header: str) -> UUID:
    """Resolve X-User-ID (UUID directo o Clerk userId 'user_xxx') a users.id UUID.

    Patrón marca_router (memoria audit-actor-must-be-authenticated-uuid): el FE
    manda el Clerk userId real; el BE lo resuelve a IAM users.id para el audit log.
    """
    try:
        return UUID(user_id_header)
    except ValueError:
        pass
    try:
        return await resolve_user_uuid_from_clerk_id(session, user_id_header)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Invalid user_id") from exc


# ---------------------------------------------------------------------------
# DB session dependency
# ---------------------------------------------------------------------------


async def _get_db() -> AsyncSession:  # type: ignore[return]
    """Async DB session dependency — uses committing generator.

    Switched from get_async_session to get_async_session_committing (Option A fix
    for C9-1): the PATCH /account/ endpoint writes clinic fields + specialties +
    a mandatory HIPAA-lite audit row. get_async_session never commits
    (caller-owned) so the audit INSERT was rolled back at session close even
    though the two repo commits had already persisted the business data.

    get_async_session_committing commits on clean return and rolls back on any
    exception — guaranteeing the audit row (and all three writes) are atomic.

    Mirror: marca_router.py:144 uses the same pattern for identical reasons.
    """
    from src.db import get_async_session_committing  # noqa: PLC0415

    async for session in get_async_session_committing():
        yield session


# ---------------------------------------------------------------------------
# Service factory (injectable / testable)
# ---------------------------------------------------------------------------


async def get_clinic_account_service(
    db: AsyncSession = Depends(_get_db),
) -> ClinicAccountService:
    """Build ClinicAccountService with its dependencies."""
    from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter  # noqa: PLC0415
    from src.modules.vitalia.clinics.infrastructure.repositories.clinic_config_repository import (  # noqa: PLC0415
        ClinicConfigRepository,
    )
    from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (  # noqa: PLC0415
        ClinicRepository,
    )

    clinic_repo = ClinicRepository(db)
    config_repo = ClinicConfigRepository(db)
    audit_writer = AsyncAuditWriter(session=db)
    return ClinicAccountService(
        clinic_repo=clinic_repo,
        config_repo=config_repo,
        audit_writer=audit_writer,
    )


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


@router.get("/", response_model=ClinicAccountResponse)
async def get_account(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    service: ClinicAccountService = Depends(get_clinic_account_service),
) -> ClinicAccountResponse:
    """Get clinic account data for the authenticated tenant.

    Returns clinic identity, fiscal info, locale prefs, and primary specialties.
    Read-only — any authenticated user can view.

    Args:
        tenant_id: Tenant from X-Tenant-ID header.
        user_id: User from X-User-ID header.
        service: Injected ClinicAccountService.

    Returns:
        ClinicAccountResponse with all account fields.

    Raises:
        404: Clinic not found for tenant.
    """
    try:
        return await service.get_account(tenant_id=UUID(tenant_id))
    except ClinicNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la clínica para este tenant",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# PATCH /
# ---------------------------------------------------------------------------


@router.patch("/", response_model=ClinicAccountResponse)
async def patch_account(
    patch_request: ClinicAccountPatchRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    service: ClinicAccountService = Depends(get_clinic_account_service),
    db: AsyncSession = Depends(_get_db),
) -> ClinicAccountResponse:
    """Partially update clinic account data.

    Requires admin_clinic role (X-User-Role: admin_clinic).
    Validates fiscal_id format for known countries.
    Writes SYNC audit log pre-response.

    Args:
        patch_request: Partial update request body.
        tenant_id: Tenant from X-Tenant-ID header.
        user_id: User from X-User-ID header.
        user_role: Role from X-User-Role header.
        service: Injected ClinicAccountService.

    Returns:
        Updated ClinicAccountResponse.

    Raises:
        403: Insufficient role (not admin_clinic).
        404: Clinic not found.
        422: Invalid fiscal_id format.
    """
    try:
        actor_uuid = await _resolve_audit_actor(db, user_id)
        return await service.patch_account(
            tenant_id=UUID(tenant_id),
            user_id=actor_uuid,
            patch=patch_request,
            user_role=user_role,
            from_ip=None,  # IP extraction requires Request injection; simplified for now
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ClinicNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la clínica para este tenant",
        )
    except FiscalIdValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"field": exc.field, "message": exc.message},
        )
    except SpecialtyValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"field": exc.field, "message": exc.message},
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# GET /specialties-catalog
# ---------------------------------------------------------------------------


@router.get("/specialties-catalog", response_model=SpecialtyCatalogResponse)
async def get_specialties_catalog(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    service: ClinicAccountService = Depends(get_clinic_account_service),
) -> SpecialtyCatalogResponse:
    """Get specialty catalog for the clinic's country.

    Returns available specialty options used in the primary_specialties selector.
    Country is determined by the clinic's country field.

    Args:
        tenant_id: Tenant from X-Tenant-ID header.
        user_id: User from X-User-ID header.
        service: Injected ClinicAccountService.

    Returns:
        SpecialtyCatalogResponse with country + specialties list.

    Raises:
        404: Clinic not found.
    """
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        # service.get_specialties_catalog now returns (country, entries) — single
        # get_active_for_tenant query. Eliminates the prior double-call (C9-4).
        country, entries = await service.get_specialties_catalog(tenant_id=tenant_uuid)
        return SpecialtyCatalogResponse(
            country=country,
            specialties=[{"id": e.id, "name": e.name, "tier": e.tier} for e in entries],
        )
    except ClinicNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la clínica para este tenant",
        )


# ---------------------------------------------------------------------------
# GET /dpo
# ---------------------------------------------------------------------------


@router.get("/dpo", response_model=DpoReferenceResponse)
async def get_dpo(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
    service: ClinicAccountService = Depends(get_clinic_account_service),
) -> DpoReferenceResponse:
    """Get DPO (Responsable de tratamiento) reference for the tenant.

    Returns the configured DPO info, or empty state (configured=False)
    when no DPO has been set. Required for HIPAA-lite compliance:
    each tenant must declare a Responsable de tratamiento per their
    jurisdiction (Ley 25.326 AR, LFPDPPP MX, Ley 1581 CO, etc.).

    Args:
        tenant_id: Tenant from X-Tenant-ID header.
        user_id: User from X-User-ID header.
        service: Injected ClinicAccountService.

    Returns:
        DpoReferenceResponse (configured=True with data, or configured=False empty state).
    """
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    dpo = await service.get_dpo(tenant_id=tenant_uuid)
    if dpo is None:
        return DpoReferenceResponse(configured=False)
    return DpoReferenceResponse(
        configured=True,
        name=dpo.get("name"),
        email=dpo.get("email"),
        phone=dpo.get("phone"),
        role=dpo.get("role"),
        jurisdiction=dpo.get("jurisdiction"),
    )
