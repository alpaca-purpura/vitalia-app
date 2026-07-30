# cap: iam.iam-scaffold-slice-1
# story-origin: estabilizar-harness-e2e-lisa-marca
"""User resolver — public IAM app service: clerk_id → users.id UUID.

Public entry point (no `_` prefix) so cross-module consumers (e.g. brand_studio
marca_router) can resolve an audit actor from a Clerk userId WITHOUT touching the
private `ClinicResolver._resolve_user_uuid` (DDD boundary) and WITHOUT requiring
the ClerkJwtDecoder (this is a header-trust path, not a JWT path).

Origin: estabilizar-harness-e2e-lisa-marca / T-3 sub-bug #2b. The marca_router is
header-trust (X-User-ID + X-User-Role headers, no JWT). With T-2 the FE sends the
real Clerk userId (string "user_2abc...", not a UUID) as X-User-ID. The audit
actor must be the IAM users.id UUID (audit_writer CASTs actor AS uuid). This
resolver performs the canonical lookup `users.id WHERE users.clerk_id == clerk_id`
— the same query as ClinicResolver._resolve_user_uuid (clinic_resolver.py:164),
exposed publicly for the header-trust consumer.

DDD note: brand_studio importing this module is a sanctioned cross-module read
(public app service, not internals). `iam` is NOT in brand_studio's
CROSS_MODULE_FORBIDDEN_PATTERNS (test_brand_studio_module_ddd.py).
"""

from __future__ import annotations

from uuid import UUID

import structlog
from luana_core_iam.infrastructure.models.user_model import UserModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.iam.application.services.clinic_resolver import UserNotFoundError

logger = structlog.get_logger()


async def resolve_user_uuid_from_clerk_id(session: AsyncSession, clerk_id: str) -> UUID:
    """Resolve a Clerk userId string to the IAM users.id UUID.

    Public app service — the canonical lookup `users.id WHERE clerk_id == clerk_id`,
    without requiring a JWT decode. Consumed cross-module by brand_studio to resolve
    the audit actor from the X-User-ID header value.

    Args:
        session: AsyncSession for the DB query.
        clerk_id: Clerk userId string (e.g. "user_2abcDEF...").

    Returns:
        users.id UUID.

    Raises:
        UserNotFoundError: If no user matches this Clerk ID.
    """
    stmt = select(UserModel.id).where(UserModel.clerk_id == clerk_id)
    result = await session.execute(stmt)
    user_uuid: UUID | None = result.scalar_one_or_none()

    if user_uuid is None:
        logger.warning("iam.user_resolver.user_not_found", clerk_id=clerk_id)
        raise UserNotFoundError(f"No se encontró el usuario con Clerk ID '{clerk_id}'.")

    return user_uuid
