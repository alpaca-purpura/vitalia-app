# cap: iam.iam-scaffold-slice-1
# story-origin: vitalia-iam-slice2-phi-real-auth
"""ClinicResolver — extracts ClinicContext from a JWT token + DB role resolution.

Application layer — orchestrates IAM domain + infrastructure.

Slice 2 changes:
  - async_resolve(token, session, tenant_id_str, clinic_id_str):
      Resolves the role from user_tenants DB (not from token).
      Steps:
        1. Decode token via ClerkJwtDecoder (JWKS real or stub).
        2. Lookup users.id UUID from users.clerk_id == payload["sub"].
        3. Query user_tenants.role WHERE (user_id, tenant_id, is_active=True).
        4. Build ClinicContext with DB role.
  - resolve() (sync) preserved for backward compat (stub path + T-2 migration).
    T-2 consumers will migrate to await async_resolve() when wiring real repos.
  - ClinicContext fields unchanged (consumers read ctx.role etc unchanged).

Per AD-2 (03-arch): query async brand-local consuming engine model UserTenantModel
(import, cero mirror). Engine UserTenantRepository is sync and doesn't fit our
async path — per arch decision we do the query directly here.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog
from luana_core_iam.infrastructure.models.user_model import UserModel
from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
    ClerkJwtDecoder,  # re-exported for callers
)

logger = structlog.get_logger()


class MissingAuthHeaderError(Exception):
    """Raised when no Authorization token is provided."""


class UserNotFoundError(Exception):
    """Raised when the Clerk user_id has no matching record in the users table."""


class RoleNotFoundError(Exception):
    """Raised when user has no active tenant membership with a role."""


@dataclass(frozen=True)
class ClinicContext:
    """Resolved clinic-scoped user context.

    Returned by ClinicResolver after validating the JWT and resolving the role.
    All IDs are typed as UUID to prevent injection of raw strings.
    role: sourced from user_tenants.role (DB) — NOT from the JWT token.
    """

    user_id: str
    tenant_id: UUID
    clinic_id: UUID
    role: str
    email: str | None
    name: str | None


class ClinicResolver:
    """Resolves a bearer token into a ClinicContext.

    Validates the token via ClerkJwtDecoder and resolves the role from DB.

    Two resolution methods:
      - async_resolve(token, session, tenant_id_str, clinic_id_str):
          SLICE 2 path. Resolves role from DB. Use this for PHI endpoints.
      - resolve(token):
          SLICE 1 compat path. Reads role from token (stub only). Used by
          existing callers before T-2 migration. Will raise JwtDecodeError
          for real JWTs since role will be empty.
    """

    def __init__(self, decoder: ClerkJwtDecoder) -> None:
        """Initialize with a JWT decoder.

        Args:
            decoder: ClerkJwtDecoder instance (or mock in tests).
        """
        self._decoder = decoder

    async def async_resolve(
        self,
        token: str | None,
        session: AsyncSession,
        tenant_id_str: str,
        clinic_id_str: str,
    ) -> ClinicContext:
        """Resolve token + DB role into ClinicContext (Slice 2 path).

        Args:
            token: Raw bearer token string (without "Bearer " prefix). May be None.
            session: AsyncSession for DB queries (from get_async_session).
            tenant_id_str: X-Tenant-ID header value (string UUID).
            clinic_id_str: X-Clinic-ID header value (string UUID).

        Returns:
            ClinicContext with DB-sourced role and UUID-typed IDs.

        Raises:
            MissingAuthHeaderError: If token is None or empty.
            JwtDecodeError: If the token cannot be decoded.
            ValueError: If tenant_id_str or clinic_id_str are not valid UUIDs.
            UserNotFoundError: If Clerk sub has no matching user in DB.
            RoleNotFoundError: If user has no active role for this tenant.
        """
        if not token:
            raise MissingAuthHeaderError("Token de autorización requerido.")

        # Step 1: Decode token (JWKS real or stub)
        payload = self._decoder.decode(token)
        clerk_sub = payload.user_id  # Clerk user ID string (e.g. "user_3EQJjxsvx...")

        tenant_uuid = UUID(tenant_id_str)
        clinic_uuid = UUID(clinic_id_str)

        # Step 2: Resolve users.id (UUID) from clerk_id == sub
        user_uuid = await self._resolve_user_uuid(session, clerk_sub)

        # Step 3: Resolve role from user_tenants
        role = await self._resolve_role(session, user_uuid, tenant_uuid)

        logger.info(
            "iam.clinic_resolver.resolved",
            clerk_sub=clerk_sub,
            tenant_id=str(tenant_uuid),
            clinic_id=str(clinic_uuid),
            role=role,
        )

        return ClinicContext(
            user_id=clerk_sub,
            tenant_id=tenant_uuid,
            clinic_id=clinic_uuid,
            role=role,
            email=payload.email,
            name=payload.name,
        )

    async def _resolve_user_uuid(self, session: AsyncSession, clerk_sub: str) -> UUID:
        """Lookup users.id from users.clerk_id == clerk_sub.

        Args:
            session: AsyncSession.
            clerk_sub: Clerk user ID string from payload["sub"].

        Returns:
            users.id UUID.

        Raises:
            UserNotFoundError: If no user matches this Clerk ID.
        """
        stmt = select(UserModel.id).where(UserModel.clerk_id == clerk_sub)
        result = await session.execute(stmt)
        user_uuid: UUID | None = result.scalar_one_or_none()

        if user_uuid is None:
            logger.warning(
                "iam.clinic_resolver.user_not_found",
                clerk_sub=clerk_sub,
            )
            raise UserNotFoundError(f"No se encontró el usuario con Clerk ID '{clerk_sub}'.")

        return user_uuid

    async def _resolve_role(
        self,
        session: AsyncSession,
        user_uuid: UUID,
        tenant_uuid: UUID,
    ) -> str:
        """Query user_tenants.role for (user_id, tenant_id, is_active=True).

        Per AD-2 (03-arch): query async brand-local consuming engine model
        UserTenantModel (import, zero mirror).

        Args:
            session: AsyncSession.
            user_uuid: users.id UUID.
            tenant_uuid: tenant UUID from X-Tenant-ID header.

        Returns:
            Role string (e.g. "doctor", "nurse", "admin_clinic").

        Raises:
            RoleNotFoundError: If user has no active membership in this tenant.
        """
        stmt = (
            select(UserTenantModel.role)
            .where(UserTenantModel.user_id == user_uuid)
            .where(UserTenantModel.tenant_id == tenant_uuid)
            .where(UserTenantModel.is_active.is_(True))
        )
        result = await session.execute(stmt)
        role: str | None = result.scalar_one_or_none()

        if role is None:
            logger.warning(
                "iam.clinic_resolver.role_not_found",
                user_id=str(user_uuid),
                tenant_id=str(tenant_uuid),
            )
            raise RoleNotFoundError("El usuario no tiene un rol activo en este tenant.")

        return role

    def resolve(self, token: str | None) -> ClinicContext:
        """Sync resolve — Slice 1 compat path.

        For stub tokens (VITALIA_AUTH_STUB=1): extracts all fields from the token.
        For real JWTs: the role field will be empty (role resolution requires DB).

        This method is preserved for backward compatibility while T-2 migrates
        all PHI endpoint callers to async_resolve().

        Args:
            token: Raw bearer token string. May be None or empty.

        Returns:
            ClinicContext with fields from token (role from token for stubs only).

        Raises:
            MissingAuthHeaderError: If token is None or empty.
            JwtDecodeError: If the token cannot be decoded.
            ValueError: If tenant_id or clinic_id are not valid UUIDs.
        """
        if not token:
            raise MissingAuthHeaderError("Token de autorización requerido.")

        payload = self._decoder.decode(token)

        # For real JWTs: tenant_id and clinic_id are "" (not in JWT).
        # Callers using resolve() for real tokens must pass headers separately.
        # This path is only correct for stub tokens.
        try:
            tenant_uuid = UUID(payload.tenant_id) if payload.tenant_id else UUID(int=0)
            clinic_uuid = UUID(payload.clinic_id) if payload.clinic_id else UUID(int=0)
        except ValueError:
            raise ValueError(f"Invalid UUID in token: tenant_id='{payload.tenant_id}', clinic_id='{payload.clinic_id}'")

        return ClinicContext(
            user_id=payload.user_id,
            tenant_id=tenant_uuid,
            clinic_id=clinic_uuid,
            role=payload.role,  # For stubs: from token. For real JWTs: empty (T-2 must migrate)
            email=payload.email,
            name=payload.name,
        )
