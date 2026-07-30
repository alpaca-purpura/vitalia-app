# cap: clinics.clinics-brand-extension
# story-origin: TBD
"""Vitalia Clinic repository — concrete implementation with HIPAA dual filter.

Every method takes (tenant_id, ...) as first filter AND clinic_id as second
filter where applicable. This enforces the hipaa-lite.md invariant:
  ".where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id)"

All queries exclude soft-deleted rows (deleted_at IS NULL).
Uses SQLA 2.0 select() idiom — no session.query().
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.clinics.domain.clinic import Clinic
from src.modules.vitalia.clinics.infrastructure.models.clinic_model import ClinicModel


class ClinicRepository:
    """Async repository for Clinic entities.

    Enforces:
      - tenant_id filter on EVERY query (hipaa-lite.md § Tenant isolation refuerzo)
      - deleted_at IS NULL (soft-delete only)
      - SQLA 2.0 select() idiom
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize ClinicRepository with async session."""
        self.db = db

    async def get_by_id(self, tenant_id: UUID, clinic_id: UUID) -> Clinic | None:
        """Retrieve clinic by (tenant_id, clinic_id) — HIPAA dual filter mandatory.

        Args:
            tenant_id: Tenant context (outer filter).
            clinic_id: Clinic primary key (inner filter).

        Returns:
            Clinic entity or None if not found / soft-deleted.
        """
        result = await self.db.execute(
            select(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.id == clinic_id)
            .where(ClinicModel.deleted_at.is_(None))
        )
        model = result.scalars().first()
        return Clinic.model_validate(model) if model else None

    async def get_by_slug(self, tenant_id: UUID, slug: str) -> Clinic | None:
        """Retrieve clinic by (tenant_id, slug).

        Args:
            tenant_id: Tenant context filter.
            slug: URL-safe clinic slug.

        Returns:
            Clinic entity or None.
        """
        result = await self.db.execute(
            select(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.slug == slug)
            .where(ClinicModel.deleted_at.is_(None))
        )
        model = result.scalars().first()
        return Clinic.model_validate(model) if model else None

    async def get_by_slug_public(self, slug: str) -> Clinic | None:
        """Retrieve an active clinic by slug for public endpoints.

        Used ONLY by the unauthenticated public doctors endpoint
        (/api/public/clinic/{slug}/doctors). Does NOT require tenant_id
        because the slug is the public-facing identifier (no PHI exposed).

        Returns only is_active=True clinics (deactivated clinics are hidden from public).

        Args:
            slug: URL-safe clinic slug (public-facing identifier).

        Returns:
            Clinic entity or None if not found / inactive / soft-deleted.
        """
        result = await self.db.execute(
            select(ClinicModel)
            .where(ClinicModel.slug == slug)
            .where(ClinicModel.is_active.is_(True))
            .where(ClinicModel.deleted_at.is_(None))
        )
        model = result.scalars().first()
        return Clinic.model_validate(model) if model else None

    async def list_by_tenant(self, tenant_id: UUID, *, active_only: bool = True) -> list[Clinic]:
        """List all clinics for a tenant.

        Args:
            tenant_id: Tenant context filter.
            active_only: If True, only return is_active=True clinics.

        Returns:
            List of Clinic entities ordered by created_at DESC.
        """
        stmt = (
            select(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.deleted_at.is_(None))
            .order_by(ClinicModel.created_at.desc())
        )
        if active_only:
            stmt = stmt.where(ClinicModel.is_active.is_(True))

        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [Clinic.model_validate(m) for m in models]

    async def create(self, clinic: Clinic) -> Clinic:
        """Persist a new Clinic entity.

        Args:
            clinic: Clinic domain entity to persist.

        Returns:
            Persisted Clinic with DB-generated timestamps.
        """
        model = ClinicModel(
            id=clinic.id,
            tenant_id=clinic.tenant_id,
            name=clinic.name,
            slug=clinic.slug,
            country=clinic.country,
            timezone=clinic.timezone,
            plan_tier=clinic.plan_tier,
            is_active=clinic.is_active,
            onboarding_completed=clinic.onboarding_completed,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return Clinic.model_validate(model)

    async def get_active_for_tenant(self, tenant_id: UUID) -> Clinic | None:
        """Return the first active, non-deleted clinic for a tenant.

        In Vitalia MVP (single-clinic-per-tenant), there is at most one active
        clinic per tenant. Returns the first ordered by created_at ASC.

        Args:
            tenant_id: Tenant context filter.

        Returns:
            Clinic entity or None if no active clinic exists.
        """
        result = await self.db.execute(
            select(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.is_active.is_(True))
            .where(ClinicModel.deleted_at.is_(None))
            .order_by(ClinicModel.created_at.asc())
            .limit(1)
        )
        model = result.scalars().first()
        return Clinic.model_validate(model) if model else None

    async def update_account(
        self,
        tenant_id: UUID,
        clinic_id: UUID,
        **fields: object,
    ) -> Clinic:
        """Update account fields for a clinic.

        Performs a targeted UPDATE of only the provided fields, then re-fetches
        the updated row to return a fresh Clinic entity.

        Args:
            tenant_id: Tenant context filter (dual filter).
            clinic_id: Clinic to update.
            **fields: Field names and new values to update.

        Returns:
            Updated Clinic entity.

        Raises:
            ClinicNotFoundError: If clinic not found or belongs to different tenant.
        """
        from sqlalchemy import func, update  # noqa: PLC0415

        from src.modules.vitalia.clinics.domain.exceptions import (  # noqa: PLC0415
            ClinicNotFoundError,
        )

        # Always touch updated_at
        update_values = {**fields, "updated_at": func.now()}

        await self.db.execute(
            update(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.id == clinic_id)
            .where(ClinicModel.deleted_at.is_(None))
            .values(**update_values)
        )
        # NOTE: commit() removed — caller owns the unit-of-work (Option A fix C9-1).
        # When called from account_router._get_db (get_async_session_committing),
        # the commit happens once on clean return, atomically with
        # update_specialties + audit_writer.write(). A flush is needed so the
        # re-fetch below sees the updated values within the same transaction.
        await self.db.flush()

        # Re-fetch to return fresh entity
        result = await self.db.execute(
            select(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.id == clinic_id)
            .where(ClinicModel.deleted_at.is_(None))
        )
        model = result.scalars().first()
        if model is None:
            raise ClinicNotFoundError(tenant_id=tenant_id, clinic_id=clinic_id)
        return Clinic.model_validate(model)

    async def soft_delete(self, tenant_id: UUID, clinic_id: UUID) -> bool:
        """Soft-delete a clinic by setting deleted_at = NOW().

        Args:
            tenant_id: Tenant context filter.
            clinic_id: Clinic to soft-delete.

        Returns:
            True if deleted, False if not found or already deleted.
        """
        from sqlalchemy import func, update  # noqa: PLC0415

        result = await self.db.execute(
            update(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.id == clinic_id)
            .where(ClinicModel.deleted_at.is_(None))
            .values(deleted_at=func.now())
        )
        await self.db.commit()
        return (result.rowcount or 0) > 0
