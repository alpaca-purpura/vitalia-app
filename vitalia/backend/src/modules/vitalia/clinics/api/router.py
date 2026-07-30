# cap: clinics.clinics-brand-extension
# story-origin: TBD
"""Vitalia Clinics API router — FastAPI thin layer.

Routes:
  GET  /                — list clinics for tenant
  POST /                — create new clinic
  GET  /{clinic_id}     — get clinic by id (dual filter)

Architecture rules:
  - response_model= is MANDATORY on all routes (arch test enforces)
  - X-Tenant-ID header is required (tenant isolation)
  - No business logic in router — delegate to ClinicService
  - Map domain exceptions (ValueError → 409 Conflict, NotFound → 404)
  - FastAPI(redirect_slashes=False) in main.py (enforced globally)
"""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Header, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.clinics.api.dtos import (
    ClinicCreateRequest,
    ClinicListResponse,
    ClinicResponse,
)
from src.modules.vitalia.clinics.application.clinic_service import ClinicService

logger = structlog.get_logger()

router = APIRouter(tags=["clinics"])


async def _get_db() -> AsyncSession:
    """Async DB session dependency (injected by FastAPI DI)."""
    from src.db import get_async_session  # noqa: PLC0415

    async for session in get_async_session():
        yield session


@router.get("/", response_model=ClinicListResponse)
async def list_clinics(
    tenant_id: str = Header(alias="X-Tenant-ID"),
    db: AsyncSession = Depends(_get_db),
) -> ClinicListResponse:
    """List all active clinics for a tenant.

    Returns all non-soft-deleted, active clinics belonging to the tenant
    identified by X-Tenant-ID header.
    """
    service = ClinicService(db)
    clinics = await service.list_clinics(UUID(tenant_id))
    return ClinicListResponse(clinics=[ClinicResponse.model_validate(c) for c in clinics], total=len(clinics))


@router.post("/", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic(
    request: ClinicCreateRequest,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    db: AsyncSession = Depends(_get_db),
) -> ClinicResponse:
    """Create a new clinic for a tenant.

    Creates clinic in vitalia_clinic_branches table.
    Returns 409 if slug already exists for this tenant.
    """
    service = ClinicService(db)
    try:
        clinic = await service.create_clinic(
            tenant_id=UUID(tenant_id),
            name=request.name,
            slug=request.slug,
            country=request.country,
            timezone=request.timezone,
            plan_tier=request.plan_tier,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "slug_conflict", "message": str(exc)},
        ) from exc

    return ClinicResponse.model_validate(clinic)


@router.get("/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(
    clinic_id: UUID,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    db: AsyncSession = Depends(_get_db),
) -> ClinicResponse:
    """Get a clinic by ID with HIPAA dual filter.

    Enforces tenant_id + clinic_id dual filter — cross-tenant access
    returns 404 (not 403) to avoid information leakage.
    """
    service = ClinicService(db)
    clinic = await service.get_clinic(UUID(tenant_id), clinic_id)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "clinic_not_found", "message": "Clínica no encontrada."},
        )
    return ClinicResponse.model_validate(clinic)
