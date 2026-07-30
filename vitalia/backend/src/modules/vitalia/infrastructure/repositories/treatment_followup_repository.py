# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Async repository — VitaliaTreatmentFollowupModel.

All queries filter by tenant_id (mandatory, per tenant-isolation.md).
Soft deletes: deleted_at IS NULL filter on reads.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.treatment_followup_model import (
    VitaliaTreatmentFollowupModel,
)

logger = structlog.get_logger()


class TreatmentFollowupRepository:
    """Tenant-scoped async repository for VitaliaTreatmentFollowupModel."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_by_id(self, followup_id: uuid.UUID) -> VitaliaTreatmentFollowupModel | None:
        """Return followup by ID for this tenant, or None if not found / deleted."""
        stmt = select(VitaliaTreatmentFollowupModel).where(
            VitaliaTreatmentFollowupModel.id == followup_id,
            VitaliaTreatmentFollowupModel.tenant_id == self._tenant_id,
            VitaliaTreatmentFollowupModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_booking_id(self, booking_id: uuid.UUID) -> VitaliaTreatmentFollowupModel | None:
        """Return the followup associated with a booking, if any."""
        stmt = select(VitaliaTreatmentFollowupModel).where(
            VitaliaTreatmentFollowupModel.tenant_id == self._tenant_id,
            VitaliaTreatmentFollowupModel.booking_id == booking_id,
            VitaliaTreatmentFollowupModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_patient(
        self,
        patient_id: uuid.UUID,
        *,
        current_step: str | None = None,
    ) -> list[VitaliaTreatmentFollowupModel]:
        """List active followups for a patient within this tenant."""
        conditions = [
            VitaliaTreatmentFollowupModel.tenant_id == self._tenant_id,
            VitaliaTreatmentFollowupModel.patient_id == patient_id,
            VitaliaTreatmentFollowupModel.deleted_at.is_(None),
        ]
        if current_step is not None:
            conditions.append(VitaliaTreatmentFollowupModel.current_step == current_step)

        stmt = (
            select(VitaliaTreatmentFollowupModel)
            .where(*conditions)
            .order_by(VitaliaTreatmentFollowupModel.started_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_due(
        self,
        *,
        at_or_before: datetime,
    ) -> list[VitaliaTreatmentFollowupModel]:
        """List followups due for cron tick (next_scheduled_at <= at_or_before)."""
        stmt = (
            select(VitaliaTreatmentFollowupModel)
            .where(
                VitaliaTreatmentFollowupModel.tenant_id == self._tenant_id,
                VitaliaTreatmentFollowupModel.next_scheduled_at.isnot(None),
                VitaliaTreatmentFollowupModel.next_scheduled_at <= at_or_before,
                VitaliaTreatmentFollowupModel.deleted_at.is_(None),
            )
            .order_by(VitaliaTreatmentFollowupModel.next_scheduled_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, followup: VitaliaTreatmentFollowupModel) -> None:
        """Persist a new or updated treatment followup model."""
        self._session.add(followup)
        await self._session.flush()
        logger.info(
            "treatment_followup_saved",
            followup_id=str(followup.id),
            tenant_id=str(self._tenant_id),
            current_step=followup.current_step,
        )

    async def soft_delete(self, followup_id: uuid.UUID) -> bool:
        """Soft-delete a followup by setting deleted_at = now()."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(VitaliaTreatmentFollowupModel)
            .where(
                VitaliaTreatmentFollowupModel.id == followup_id,
                VitaliaTreatmentFollowupModel.tenant_id == self._tenant_id,
                VitaliaTreatmentFollowupModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
