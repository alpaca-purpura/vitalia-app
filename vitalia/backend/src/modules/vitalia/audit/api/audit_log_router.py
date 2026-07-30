# cap: iam.luana-core-adoption
# story-origin: vitalia-fase2-adrian-inbox
"""HIPAA-lite PHI-read audit ingestion endpoint (FE → BE).

POST /api/v1/vitalia/audit-log

Why this exists (audit-log-404 twin-fix, vitalia-fase2-adrian-inbox · Chris decision A):
  The FE `AuditedSection` (wraps PHI content in `ContactSidebar`, fires a beacon on
  mount per hipaa-lite.md "TODA lectura de PHI registra audit_log row") POSTed to
  /api/v1/vitalia/audit-log — but NO router served it → 404 on every ContactSidebar
  mount, AND the PHI-read audit row was lost (compliance gap). This wires the beacon
  to `AsyncAuditWriter` (sync pre-response write on the committing session — stronger
  than the FE fire-forget) with the dual tenant+clinic filter.

Contract:
  - Auth: tenant-scoped — Authorization (Clerk JWT) + X-Tenant-ID + X-Clinic-ID,
    resolved + verified via `ClinicResolver` (membership), never trusted from body.
  - `user_id` column = the IAM `users.id` UUID (resolved from the Clerk sub via
    `resolve_user_uuid_from_clerk_id`) — NOT the raw Clerk sub (the column CASTs uuid).
  - `resource_id` must be a UUID (audit_writer CASTs resource_id AS uuid).

FOLLOW-UP (NOT this story): the architecturally-ideal place to audit the PHI read is
server-side in `crm.get_conversation_detail` (where the lead PHI is decrypted). That
file is under the concurrent embudo session's `code:crm` lock, so this FE-beacon
endpoint is the unblocked path. Track moving the audit server-side when crm frees.

downstream-regression-na: brand-local vitalia audit API (vitalia-only).
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session_committing
from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.iam.application.services.clinic_resolver import (
    ClinicContext,
    ClinicResolver,
    MissingAuthHeaderError,
    RoleNotFoundError,
    UserNotFoundError,
)
from src.modules.vitalia.iam.application.services.user_resolver import (
    resolve_user_uuid_from_clerk_id,
)
from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
    ClerkJwtDecoder,
    JwtDecodeError,
)

logger = structlog.get_logger()

router = APIRouter(tags=["audit"])

# ---------------------------------------------------------------------------
# Header type aliases
# ---------------------------------------------------------------------------

AuthorizationHeader = Annotated[str, Header(alias="Authorization")]
TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]
ClinicIdHeader = Annotated[str, Header(alias="X-Clinic-ID")]


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class AuditLogRequest(BaseModel):
    """Ingestion body for a PHI-read audit event (from `AuditedSection`).

    Field names mirror the FE camelCase JSON keys via aliases. `resource_id` is a
    UUID (the audit row CASTs it AS uuid). `user_id` from the body is advisory only
    — the persisted actor is resolved server-side from the verified JWT.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    action: Literal["view", "download", "print", "export"] = "view"
    resource_type: str = Field(alias="resourceType", min_length=1, max_length=64)
    resource_id: UUID = Field(alias="resourceId")
    user_id: str | None = Field(default=None, alias="userId")


class AuditLogRecorded(BaseModel):
    """Acknowledgement that the PHI-read audit row was written."""

    recorded: bool


# ---------------------------------------------------------------------------
# Auth helper (mirrors marketing/inbox resolution — patchable in tests)
# ---------------------------------------------------------------------------


def _build_resolver() -> ClinicResolver:
    """Construct a ClinicResolver with the Clerk JWT decoder."""
    return ClinicResolver(decoder=ClerkJwtDecoder())


async def _resolve_context(
    authorization: str,
    x_tenant_id: str,
    x_clinic_id: str,
    session: AsyncSession,
) -> ClinicContext:
    """Resolve Bearer token + headers to a ClinicContext (DB-verified membership).

    Raises:
        HTTPException(401): Token missing, invalid, or user not found.
        HTTPException(403): User has no active role in this tenant.
        HTTPException(422): tenant/clinic identifiers are not valid UUIDs.
    """
    token = authorization.removeprefix("Bearer ").strip()
    resolver = _build_resolver()
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


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/audit-log", response_model=AuditLogRecorded, status_code=201)
async def record_phi_access(
    body: AuditLogRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> AuditLogRecorded:
    """Record a PHI-read access (HIPAA-lite audit) initiated from the FE.

    The actor (`user_id` column) is the IAM `users.id` UUID resolved from the
    verified Clerk sub — the body's `userId` is ignored for trust. tenant/clinic
    come from the resolved context (dual filter). Written sync on the committing
    session (persists before the response).
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)
    actor_uuid = await resolve_user_uuid_from_clerk_id(session, ctx.user_id)

    writer = AsyncAuditWriter(session=session)
    await writer.write(
        tenant_id=ctx.tenant_id,
        clinic_id=ctx.clinic_id,
        user_id=actor_uuid,
        action=body.action,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        user_agent="VitaliaWeb/1.0",
    )

    return AuditLogRecorded(recorded=True)
