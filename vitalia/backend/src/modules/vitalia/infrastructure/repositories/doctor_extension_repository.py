# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Async repository — VitaliaDoctorExtensionModel.

All queries filter by tenant_id (mandatory, per tenant-isolation.md).
Soft deletes: deleted_at IS NULL filter on reads.
One row per (tenant_id, doctor_id) — unique constraint enforced at DB level.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.doctor_extension_model import (
    VitaliaDoctorExtensionModel,
)

logger = structlog.get_logger()


class DoctorExtensionRepository:
    """Tenant-scoped async repository for VitaliaDoctorExtensionModel."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_by_id(self, extension_id: uuid.UUID) -> VitaliaDoctorExtensionModel | None:
        """Return doctor extension by ID for this tenant."""
        stmt = select(VitaliaDoctorExtensionModel).where(
            VitaliaDoctorExtensionModel.id == extension_id,
            VitaliaDoctorExtensionModel.tenant_id == self._tenant_id,
            VitaliaDoctorExtensionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_doctor_id(self, doctor_id: uuid.UUID) -> VitaliaDoctorExtensionModel | None:
        """Return doctor extension by doctor_id for this tenant.

        Returns None if no extension exists or it has been soft-deleted.
        """
        stmt = select(VitaliaDoctorExtensionModel).where(
            VitaliaDoctorExtensionModel.tenant_id == self._tenant_id,
            VitaliaDoctorExtensionModel.doctor_id == doctor_id,
            VitaliaDoctorExtensionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[VitaliaDoctorExtensionModel]:
        """List all active doctor extensions for this tenant."""
        stmt = (
            select(VitaliaDoctorExtensionModel)
            .where(
                VitaliaDoctorExtensionModel.tenant_id == self._tenant_id,
                VitaliaDoctorExtensionModel.deleted_at.is_(None),
            )
            .order_by(VitaliaDoctorExtensionModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, extension: VitaliaDoctorExtensionModel) -> None:
        """Persist a new or updated doctor extension."""
        self._session.add(extension)
        await self._session.flush()
        logger.info(
            "doctor_extension_saved",
            extension_id=str(extension.id),
            doctor_id=str(extension.doctor_id),
            tenant_id=str(self._tenant_id),
        )

    async def soft_delete(self, extension_id: uuid.UUID) -> bool:
        """Soft-delete a doctor extension by setting deleted_at = now()."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(VitaliaDoctorExtensionModel)
            .where(
                VitaliaDoctorExtensionModel.id == extension_id,
                VitaliaDoctorExtensionModel.tenant_id == self._tenant_id,
                VitaliaDoctorExtensionModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
