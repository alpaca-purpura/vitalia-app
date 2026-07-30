# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-adrian-inbox
"""Growth Studio telemetry ingestion endpoint (FE → BE).

POST /api/telemetry/growth-studio-event

Why this exists (telemetry-404 side-fix, vitalia-fase2-adrian-inbox · Chris option A):
  The FE `mateo/lib/telemetry.ts` POSTs UX/funnel events to
  /api/telemetry/growth-studio-event, but NO router served the path → 404 app-wide
  → the anti-burbuja e2e gate (Critical Rule #37 §3) tripped on any page that fired
  telemetry. This thin endpoint wires the FE ingestion to the existing server-side
  `GrowthStudioEmitter` (fire-forget), tenant-scoped via the SAME `ClinicResolver`
  as the rest of the brand API.

Contract:
  - Auth: tenant-scoped write — requires Authorization (Clerk JWT) + X-Tenant-ID
    + X-Clinic-ID (resolved + verified via ClinicResolver, NOT trusted from body).
  - Body: { event_type, occurred_at?, payload }. `event_type` is a snake_case
    identifier (≤64 chars) — never PHI free-text. `payload` is PHI-sanitized
    server-side by the emitter before insert.
  - Persistence is fire-forget (the emitter swallows its own failures); the tenant
    context is the security boundary, so the endpoint always returns 202 once the
    caller is authenticated.

downstream-regression-na: brand-local vitalia telemetry API (vitalia-only).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session_committing
from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
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

logger = structlog.get_logger()

router = APIRouter(tags=["telemetry"])

# ---------------------------------------------------------------------------
# Header type aliases
# ---------------------------------------------------------------------------

AuthorizationHeader = Annotated[str, Header(alias="Authorization")]
TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]
ClinicIdHeader = Annotated[str, Header(alias="X-Clinic-ID")]


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class GrowthStudioEventRequest(BaseModel):
    """Ingestion body for a single growth-studio telemetry event.

    `event_type` is constrained to a snake_case identifier so PHI cannot ride in
    the event name (free text). `payload` props are PHI-sanitized server-side by
    the emitter before insert.
    """

    model_config = ConfigDict(extra="ignore")

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Snake_case event identifier (e.g. 'agenda_viewed'). No PHI.",
    )
    occurred_at: datetime | None = Field(
        default=None,
        description="Client ISO 8601 timestamp (advisory — server stamps NOW() on insert).",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event metadata (PHI-free; PHI keys are stripped server-side).",
    )


class GrowthStudioEventAccepted(BaseModel):
    """Acknowledgement that the event was accepted for fire-forget ingestion."""

    accepted: bool


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


@router.post("/growth-studio-event", response_model=GrowthStudioEventAccepted, status_code=202)
async def ingest_growth_studio_event(
    body: GrowthStudioEventRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> GrowthStudioEventAccepted:
    """Ingest a single FE telemetry event (fire-forget, tenant-scoped).

    The tenant/clinic are taken from the RESOLVED context (never the body), so a
    spoofed `tenant_id` in `payload` cannot redirect the write. The actor user is
    intentionally NOT derived from the Clerk sub (non-UUID) — telemetry rows are
    anonymous at the user level (emitter `user_id` is nullable).
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    emitter = GrowthStudioEmitter(session=session)
    await emitter.emit_event(
        event_type=body.event_type,
        tenant_id=ctx.tenant_id,
        clinic_id=ctx.clinic_id,
        user_id=None,
        props=body.payload,
    )

    return GrowthStudioEventAccepted(accepted=True)
