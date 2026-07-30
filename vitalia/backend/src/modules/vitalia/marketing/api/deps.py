# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""FastAPI dependencies for the vitalia marketing API.

Provides:
  - TenantIdHeader / ClinicIdHeader — typed Annotated header aliases
  - verify_role() — dependency factory for RBAC enforcement (raises HTTP 403)
  - idempotency_key_dep() — dependency that reads Idempotency-Key header (raises HTTP 422)
  - get_clinic_context_async() — resolves Bearer JWT to ClinicContext via DB role (raises HTTP 401)

HIPAA-lite:
  - All marketing endpoints require X-Tenant-ID + X-Clinic-ID (dual filter).
  - Role enforcement uses DB role from user_tenants table (Slice 2: async_resolve).
  - Marketing data is NOT PHI — roles allowed: doctor/nurse/admin_clinic/recepcion
    for reads; admin_clinic/owner_clinic for mutations.

Slice 2 changes:
  - get_clinic_context() replaced with get_clinic_context_async() using async_resolve.
  - verify_role() updated to use async_resolve.

downstream-regression-na: brand-local marketing API deps (vitalia-only)
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session
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

# ---------------------------------------------------------------------------
# Header type aliases — used on all marketing endpoints
# ---------------------------------------------------------------------------

TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]
ClinicIdHeader = Annotated[str, Header(alias="X-Clinic-ID")]
AuthorizationHeader = Annotated[str, Header(alias="Authorization")]
IdempotencyKeyHeader = Annotated[str | None, Header(alias="Idempotency-Key")] = None


def _build_resolver() -> ClinicResolver:
    """Construct a ClinicResolver with the Clerk JWT decoder."""
    return ClinicResolver(decoder=ClerkJwtDecoder())


async def get_clinic_context_async(
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ClinicContext:
    """Resolve Bearer token to ClinicContext via DB role (Slice 2 async path).

    Raises:
        HTTPException(401): Token missing, invalid, or user not found in DB.
        HTTPException(403): User has no active role in this tenant.
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
        raise HTTPException(
            status_code=401,
            detail="Token de autorización requerido.",
        )
    except JwtDecodeError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado.",
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado.",
        )
    except RoleNotFoundError:
        raise HTTPException(
            status_code=403,
            detail="El usuario no tiene un rol activo en este tenant.",
        )
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Identificadores de tenant o clínica inválidos.",
        )


# Backward-compat alias (routes.py uses get_clinic_context_async directly)
# Keeping the original sync name as a pointer to the async version for any
# test that might reference it by name.
get_clinic_context = get_clinic_context_async  # noqa: E305 — alias for compat


def verify_role(*allowed_roles: str):
    """Dependency factory — returns a FastAPI dependency that enforces role membership.

    Usage:
        @router.get("/foo", dependencies=[Depends(verify_role("admin_clinic"))])

    Args:
        *allowed_roles: Roles allowed to access the endpoint.

    Returns:
        An async dependency function that raises HTTP 403 when the caller role
        is not in the allowed set.
    """

    async def _check(
        ctx: Annotated[ClinicContext, Depends(get_clinic_context_async)],
    ) -> None:
        """Inner dependency — checks role from resolved ClinicContext."""
        if ctx.role not in allowed_roles:
            logger.warning(
                "marketing_api.role_denied",
                role=ctx.role,
                allowed=list(allowed_roles),
            )
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Acceso no autorizado. Tu rol '{ctx.role}' no tiene permisos "
                    f"para esta acción. Se requiere uno de: {list(allowed_roles)}."
                ),
            )

    return _check


def require_idempotency_key(idempotency_key: IdempotencyKeyHeader) -> str:
    """Dependency that enforces the Idempotency-Key header is present.

    Args:
        idempotency_key: Optional header value — raises 422 if missing.

    Returns:
        The idempotency key string.

    Raises:
        HTTPException(422): When Idempotency-Key header is absent.
    """
    if not idempotency_key:
        raise HTTPException(
            status_code=422,
            detail="El encabezado 'Idempotency-Key' es obligatorio para esta operación.",
        )
    return idempotency_key
