"""Cross-module port for read-only tenant_profile access.

Other bounded contexts (sales_agent, landing, analytics) MUST use these
functions instead of importing from ``tenant_profile/`` directly. This preserves
the DDD boundary: only the port is visible across modules.

Lazy imports inside each function prevent circular imports and keep
``shared/`` dependency-free from any ``modules/`` package at import time.

Consumers:
  - ``sales_agent`` — grounding the agent identity document with business context.
  - ``landing`` — template selection fallback when no preset is declared.
  - ``analytics`` — future segmentation (not yet implemented).

Contracts:
  - :class:`TenantLocationContract` (added 2026-05-17 promotion lift)
    Universal columns brand ``tenants`` tables MUST implement to enable
    locale-aware cron jobs, currency defaults, compliance jurisdiction,
    and analytics regionalization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from luana_core_platform.domain.expert_business_type import ExpertBusinessType


@runtime_checkable
class TenantLocationContract(Protocol):
    """Mandatory columns brand ``tenants`` tables MUST implement.

    Added 2026-05-17 via promotion proposal
    ``docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md``.

    Brand consumers add these columns via local Alembic migrations using
    idempotent ``ADD COLUMN IF NOT EXISTS``. All columns are nullable or
    default-safe to preserve backward compatibility with existing tenants.

    Fields:
        is_onboarded: Wizard completion flag. Default ``False`` for new tenants;
            brand consumers MUST backfill ``TRUE`` for pre-2026-05-17 tenants
            in the same migration that adds the column.
        location_country: ISO 3166-1 alpha-2 country code (e.g. ``"AR"``,
            ``"PE"``, ``"MX"``). ``None`` until tenant declares location during
            onboarding wizard.
        location_city: Free-text city name for analytics regionalization and
            disambiguation. ``None`` until tenant declares.
        timezone: IANA timezone database string (e.g.
            ``"America/Argentina/Buenos_Aires"``, ``"America/Lima"``). ``None``
            until tenant declares; brand cron jobs MUST filter
            ``WHERE timezone IS NOT NULL`` to avoid silent failures.

    Note:
        This is a typing :class:`Protocol`, not a SQLAlchemy model. Each brand
        implements the columns in its own ``tenants`` table via Alembic
        migrations. Cross-module readers consume this contract through helper
        functions in this module (e.g. ``get_tenant_location()``, when added).
    """

    is_onboarded: bool
    location_country: str | None
    location_city: str | None
    timezone: str | None


def get_tenant_business_types(
    db: Session,
    tenant_id: UUID,
) -> tuple[ExpertBusinessType, ...]:
    """Return the tenant's declared business_types, or an empty tuple.

    Args:
        db: Active SQLAlchemy session.
        tenant_id: The tenant to look up.

    Returns:
        Tuple of :class:`ExpertBusinessType` values, or ``()`` when the tenant
        has no declared profile yet (onboarding not completed).
    """
    from luana_core_tenant_profile.infrastructure.repositories.tenant_profile_repository import (
        SqlTenantProfileRepository,
    )

    profile = SqlTenantProfileRepository(db).get_or_none(tenant_id)
    return profile.business_types if profile is not None else ()


def is_tenant_profile_complete(
    db: Session,
    tenant_id: UUID,
) -> bool:
    """Return True when the tenant has completed the business_types onboarding.

    Args:
        db: Active SQLAlchemy session.
        tenant_id: The tenant to look up.

    Returns:
        ``True`` if ``declared_at`` is set and at least one business_type is
        declared. ``False`` otherwise (new tenant, or incomplete onboarding).
    """
    from luana_core_tenant_profile.infrastructure.repositories.tenant_profile_repository import (
        SqlTenantProfileRepository,
    )

    profile = SqlTenantProfileRepository(db).get_or_none(tenant_id)
    return profile.is_complete if profile is not None else False
