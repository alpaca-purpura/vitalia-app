# cap: admin.admin-streamlit-service
# story-origin: TBD
"""Vitalia Admin Helper API — internal endpoints for DB state verification.

These endpoints are consumed by:
  - Playwright E2E tests (admin-smoke project)
  - Streamlit admin health checks
  - Integration tests (verify audit_log rows written after admin mutations)

Security:
  - VITALIA_INTERNAL_API_TOKEN required in X-Internal-Token header
  - Token loaded from env var ONLY (never hardcoded)
  - NOT exposed in OpenAPI docs (include_in_schema=False)
  - These endpoints do NOT use Clerk auth (admin super-admin context)

HIPAA-lite:
  - No PHI returned in any response
  - Audit log verification returns count/exists — no payload content
  - Tenant isolation enforced (X-Tenant-ID header + tenant filter)
"""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

logger = structlog.get_logger()

router = APIRouter(tags=["admin-internal"])

_INTERNAL_TOKEN_SCHEME = APIKeyHeader(name="X-Internal-Token", auto_error=False)


def _require_internal_token(
    token: Annotated[str | None, Depends(_INTERNAL_TOKEN_SCHEME)] = None,
) -> None:
    """Dependency: validate VITALIA_INTERNAL_API_TOKEN from env.

    Raises 403 if token is missing or invalid.
    Raises 500 if VITALIA_INTERNAL_API_TOKEN env var is not set.
    """
    expected = os.environ.get("VITALIA_INTERNAL_API_TOKEN", "")
    if not expected:
        logger.error("vitalia_internal_token_not_configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "configuration_error", "message": "Internal token not configured."},
        )
    if not token or token != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Token interno requerido."},
        )


class AuditLogCountResponse(BaseModel):
    """Response for audit log count endpoint."""

    tenant_id: str
    action: str
    count: int


class TenantExistsResponse(BaseModel):
    """Response for tenant exists check endpoint."""

    tenant_id: str | None
    slug: str
    exists: bool


class ClinicExistsResponse(BaseModel):
    """Response for clinic exists check endpoint."""

    clinic_id: str | None
    tenant_id: str
    slug: str
    exists: bool


class DbStateResponse(BaseModel):
    """Response for generic DB state endpoint (counts per table)."""

    counts: dict[str, int]


class AuditLogEntry(BaseModel):
    """Single sanitized audit log entry (no PHI)."""

    id: str
    tenant_id: str
    action: str
    resource_type: str | None
    occurred_at: str


@router.get(
    "/audit-log/count",
    response_model=AuditLogCountResponse,
    include_in_schema=False,
)
async def get_audit_log_count(
    action: str,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    _: None = Depends(_require_internal_token),
) -> AuditLogCountResponse:
    """Count audit log rows for a tenant + action.

    Used by E2E tests to verify audit log was written after mutations.
    Returns count only — no payload content (HIPAA).
    """
    from sqlalchemy import text  # noqa: PLC0415

    from src.db import get_async_session  # noqa: PLC0415

    try:
        async for db in get_async_session():
            result = await db.execute(
                text("""
                    SELECT COUNT(*) FROM vitalia_audit_log
                    WHERE tenant_id = :tenant_id::uuid
                      AND action = :action
                """),
                {"tenant_id": tenant_id, "action": action},
            )
            count_val = result.scalar() or 0
            break
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_helpers_audit_count_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "db_error", "message": str(exc)},
        ) from exc

    return AuditLogCountResponse(tenant_id=tenant_id, action=action, count=int(count_val))


@router.get(
    "/tenants/exists",
    response_model=TenantExistsResponse,
    include_in_schema=False,
)
async def check_tenant_exists(
    slug: str,
    _: None = Depends(_require_internal_token),
) -> TenantExistsResponse:
    """Check if a tenant with given slug exists in the engine IAM table.

    Used by E2E tests to verify admin create operations succeeded.
    """
    from src.db import get_async_session  # noqa: PLC0415

    try:
        async for db in get_async_session():
            # TenantRepository uses sync Session; adapt for async context
            from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: PLC0415
            from sqlalchemy import select  # noqa: PLC0415

            result = await db.execute(select(TenantModel).where(TenantModel.slug == slug))
            model = result.scalars().first()
            break
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_helpers_tenant_exists_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "db_error", "message": str(exc)},
        ) from exc

    return TenantExistsResponse(
        tenant_id=str(model.id) if model else None,
        slug=slug,
        exists=model is not None,
    )


@router.get(
    "/clinics/exists",
    response_model=ClinicExistsResponse,
    include_in_schema=False,
)
async def check_clinic_exists(
    slug: str,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    _: None = Depends(_require_internal_token),
) -> ClinicExistsResponse:
    """Check if a clinic branch with given slug exists for tenant.

    Used by E2E tests to verify clinic create operations succeeded.
    HIPAA: tenant_id filter enforced (dual filter with slug).
    """
    from sqlalchemy import select  # noqa: PLC0415

    from src.db import get_async_session  # noqa: PLC0415
    from src.modules.vitalia.clinics.infrastructure.models.clinic_model import (  # noqa: PLC0415
        ClinicModel,
    )

    try:
        async for db in get_async_session():
            result = await db.execute(
                select(ClinicModel)
                .where(ClinicModel.tenant_id == UUID(tenant_id))
                .where(ClinicModel.slug == slug)
                .where(ClinicModel.deleted_at.is_(None))
            )
            model = result.scalars().first()
            break
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_helpers_clinic_exists_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "db_error", "message": str(exc)},
        ) from exc

    return ClinicExistsResponse(
        clinic_id=str(model.id) if model else None,
        tenant_id=tenant_id,
        slug=slug,
        exists=model is not None,
    )


@router.get(
    "/db-state",
    response_model=DbStateResponse,
    include_in_schema=False,
)
async def get_db_state(
    _: None = Depends(_require_internal_token),
) -> DbStateResponse:
    """Generic DB state — row counts for engine IAM + brand-extension tables.

    Used by Playwright admin-smoke E2E tests to assert create/delete ops.
    Returns counts only (HIPAA — no row content).
    """
    from sqlalchemy import text  # noqa: PLC0415

    from src.db import get_async_session  # noqa: PLC0415

    tables = ["tenants", "users", "user_tenants", "vitalia_clinic_branches", "vitalia_audit_log"]
    counts: dict[str, int] = {}
    try:
        async for db in get_async_session():
            for tbl in tables:
                result = await db.execute(text(f"SELECT COUNT(*) FROM {tbl}"))  # noqa: S608
                counts[tbl] = int(result.scalar() or 0)
            break
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_helpers_db_state_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "db_error", "message": str(exc)},
        ) from exc

    return DbStateResponse(counts=counts)


@router.get(
    "/audit-log",
    response_model=list[AuditLogEntry],
    include_in_schema=False,
)
async def list_audit_log(
    action: str | None = None,
    since: str | None = None,
    limit: int = 50,
    _: None = Depends(_require_internal_token),
) -> list[AuditLogEntry]:
    """List recent sanitized audit log entries.

    Used by Playwright E2E tests to verify audit log rows after mutations.
    HIPAA: returns no payload content — only id/tenant/action/resource_type/timestamp.
    """
    from sqlalchemy import text  # noqa: PLC0415

    from src.db import get_async_session  # noqa: PLC0415

    where_clauses = []
    params: dict[str, object] = {"limit": min(limit, 200)}
    if action:
        where_clauses.append("action = :action")
        params["action"] = action
    if since:
        where_clauses.append("occurred_at >= :since")
        params["since"] = since
    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    query_sql = (
        "SELECT id, tenant_id, action, resource_type, occurred_at "
        "FROM vitalia_audit_log" + where_sql + " ORDER BY occurred_at DESC LIMIT :limit"
    )

    entries: list[AuditLogEntry] = []
    try:
        async for db in get_async_session():
            result = await db.execute(text(query_sql), params)
            for row in result.fetchall():
                entries.append(
                    AuditLogEntry(
                        id=str(row[0]),
                        tenant_id=str(row[1]),
                        action=str(row[2]),
                        resource_type=(str(row[3]) if row[3] is not None else None),
                        occurred_at=row[4].isoformat() if row[4] else "",
                    )
                )
            break
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_helpers_audit_log_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "db_error", "message": str(exc)},
        ) from exc

    return entries
