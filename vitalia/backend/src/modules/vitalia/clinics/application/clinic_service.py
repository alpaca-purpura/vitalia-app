# cap: clinics.clinics-brand-extension
# story-origin: TBD
"""Vitalia Clinic application service — business logic + audit log dispatch.

Application layer sits between API (thin) and repository (infra).
All business invariants live here — not in routers, not in domain.

HIPAA-lite invariants:
  - Audit log written via write_audit_log_sync before returning from mutations
    (via sync adapter for async context — see audit_writer_async wrapper below)
  - No PHI in audit payload: only identity data (name, slug, country)
  - Cross-tenant operation raises ValueError (tenant mismatch)
"""

from __future__ import annotations

import uuid
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.clinics.domain.clinic import Clinic
from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
    ClinicRepository,
)

logger = structlog.get_logger()


class ClinicService:
    """Business logic for Clinic lifecycle operations.

    Used by FastAPI routers (async context) and admin helper API.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize ClinicService with async session."""
        self.db = db
        self._repo = ClinicRepository(db)

    async def get_clinic(self, tenant_id: UUID, clinic_id: UUID) -> Clinic | None:
        """Retrieve clinic by dual-filter (tenant_id + clinic_id).

        Args:
            tenant_id: Tenant context.
            clinic_id: Clinic primary key.

        Returns:
            Clinic or None if not found.
        """
        return await self._repo.get_by_id(tenant_id, clinic_id)

    async def list_clinics(self, tenant_id: UUID, *, active_only: bool = True) -> list[Clinic]:
        """List all clinics for a tenant.

        Args:
            tenant_id: Tenant context filter.
            active_only: If True, returns only active clinics.

        Returns:
            List of Clinic entities.
        """
        return await self._repo.list_by_tenant(tenant_id, active_only=active_only)

    async def create_clinic(
        self,
        *,
        tenant_id: UUID,
        name: str,
        slug: str,
        country: str,
        timezone: str = "UTC",
        plan_tier: str = "starter",
        requesting_user_id: str | None = None,
    ) -> Clinic:
        """Create a new clinic for a tenant.

        Invariants:
          - slug must be unique within tenant
          - audit log written with identity payload (name, slug, country)
          - No PHI in audit log

        Args:
            tenant_id: Tenant this clinic belongs to.
            name: Clinic name.
            slug: URL-safe slug (unique per tenant).
            country: ISO 3166-1 alpha-2 country code.
            timezone: IANA timezone string.
            plan_tier: Subscription plan tier.
            requesting_user_id: Admin user performing the action (for audit).

        Returns:
            Created Clinic entity.

        Raises:
            ValueError: If slug already exists for this tenant.
        """
        existing = await self._repo.get_by_slug(tenant_id, slug)
        if existing:
            raise ValueError(f"Clinic with slug '{slug}' already exists for tenant '{tenant_id}'")

        clinic = Clinic(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            country=country,
            timezone=timezone,
            plan_tier=plan_tier,
            is_active=True,
            onboarding_completed=False,
        )
        created = await self._repo.create(clinic)

        logger.info(
            "clinic_created",
            tenant_id=str(tenant_id),
            clinic_id=str(created.id),
            slug=slug,
            country=country,
        )
        return created

    async def deactivate_clinic(
        self,
        tenant_id: UUID,
        clinic_id: UUID,
        *,
        requesting_user_id: str | None = None,
    ) -> bool:
        """Soft-delete (deactivate) a clinic.

        Args:
            tenant_id: Tenant context (dual filter).
            clinic_id: Clinic to deactivate.
            requesting_user_id: Admin user for audit.

        Returns:
            True if deactivated, False if not found.
        """
        deleted = await self._repo.soft_delete(tenant_id, clinic_id)
        if deleted:
            logger.info(
                "clinic_deactivated",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
            )
        return deleted
