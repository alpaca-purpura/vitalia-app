# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Async repository — VitaliaBookingModel.

All queries filter by tenant_id (mandatory, per tenant-isolation.md).
Soft deletes: deleted_at IS NULL filter on reads; update deleted_at on delete.
Constructor receives tenant_id as a required parameter — no query escapes without it.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.booking_model import VitaliaBookingModel

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

# Statuses that count as "slot occupied" for advisory lock check
_ACTIVE_STATUSES = (
    "pending_payment",
    "awaiting_consent",
    "confirmed_deposit",
    "confirmed_full",
)


class BookingRepository:
    """Tenant-scoped async repository for VitaliaBookingModel.

    tenant_id is injected at construction time; every method enforces isolation
    automatically — callers cannot accidentally omit the filter.
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_by_id(self, booking_id: uuid.UUID) -> VitaliaBookingModel | None:
        """Return booking by ID for this tenant, or None if not found / deleted."""
        stmt = select(VitaliaBookingModel).where(
            VitaliaBookingModel.id == booking_id,
            VitaliaBookingModel.tenant_id == self._tenant_id,
            VitaliaBookingModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_patient(
        self,
        patient_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> list[VitaliaBookingModel]:
        """List active bookings for a patient within this tenant."""
        conditions = [
            VitaliaBookingModel.tenant_id == self._tenant_id,
            VitaliaBookingModel.patient_id == patient_id,
            VitaliaBookingModel.deleted_at.is_(None),
        ]
        if status is not None:
            conditions.append(VitaliaBookingModel.status == status)

        stmt = select(VitaliaBookingModel).where(*conditions).order_by(VitaliaBookingModel.slot_iso.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_doctor(
        self,
        doctor_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> list[VitaliaBookingModel]:
        """List active bookings for a doctor within this tenant."""
        conditions = [
            VitaliaBookingModel.tenant_id == self._tenant_id,
            VitaliaBookingModel.doctor_id == doctor_id,
            VitaliaBookingModel.deleted_at.is_(None),
        ]
        if status is not None:
            conditions.append(VitaliaBookingModel.status == status)

        stmt = select(VitaliaBookingModel).where(*conditions).order_by(VitaliaBookingModel.slot_iso.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_doctor_slot(
        self,
        doctor_id: uuid.UUID,
        slot_iso: datetime,
    ) -> VitaliaBookingModel | None:
        """Return the active booking for (doctor_id, slot_iso) if one exists.

        Used by BookingService advisory lock check pre-creation.
        Only considers non-cancelled, non-deleted bookings as "slot occupied".
        """
        stmt = select(VitaliaBookingModel).where(
            VitaliaBookingModel.tenant_id == self._tenant_id,
            VitaliaBookingModel.doctor_id == doctor_id,
            VitaliaBookingModel.slot_iso == slot_iso,
            VitaliaBookingModel.status.in_(_ACTIVE_STATUSES),
            VitaliaBookingModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, booking: VitaliaBookingModel) -> None:
        """Persist a new or updated booking model.

        For new bookings: session.add() + flush.
        For updates: the model must already be tracked by the session.
        """
        self._session.add(booking)
        await self._session.flush()
        logger.info(
            "booking_saved",
            booking_id=str(booking.id),
            tenant_id=str(self._tenant_id),
            status=booking.status,
        )

    async def soft_delete(self, booking_id: uuid.UUID) -> bool:
        """Soft-delete a booking by setting deleted_at = now().

        Returns True if the row was found and updated, False if not found.
        Only soft-deletes rows belonging to this tenant.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(VitaliaBookingModel)
            .where(
                VitaliaBookingModel.id == booking_id,
                VitaliaBookingModel.tenant_id == self._tenant_id,
                VitaliaBookingModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        updated = result.rowcount > 0
        if updated:
            logger.info(
                "booking_soft_deleted",
                booking_id=str(booking_id),
                tenant_id=str(self._tenant_id),
            )
        return updated
