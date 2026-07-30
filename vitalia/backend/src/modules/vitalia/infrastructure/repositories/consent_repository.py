# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Async repository — VitaliaConsentRecordModel.

All queries filter by tenant_id (mandatory, per tenant-isolation.md).
Consent records have NO deleted_at (legal immutability preserved).
Status lifecycle: pending_signature → signed / expired / revoked.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.consent_record_model import (
    VitaliaConsentRecordModel,
)

logger = structlog.get_logger()


class ConsentRepository:
    """Tenant-scoped async repository for VitaliaConsentRecordModel.

    Consent records are legally immutable — no soft delete (no deleted_at column).
    Use status='revoked' to logically disable a consent.
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_by_id(self, consent_id: uuid.UUID) -> VitaliaConsentRecordModel | None:
        """Return consent record by ID for this tenant.

        Note: No deleted_at filter — consent records are legally immutable.
        Returns records in any status (including revoked/expired).
        """
        stmt = select(VitaliaConsentRecordModel).where(
            VitaliaConsentRecordModel.id == consent_id,
            VitaliaConsentRecordModel.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_by_booking(self, booking_id: uuid.UUID) -> VitaliaConsentRecordModel | None:
        """Return the pending_signature consent for a booking, if any."""
        stmt = select(VitaliaConsentRecordModel).where(
            VitaliaConsentRecordModel.tenant_id == self._tenant_id,
            VitaliaConsentRecordModel.booking_id == booking_id,
            VitaliaConsentRecordModel.status == "pending_signature",
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_patient(
        self,
        patient_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> list[VitaliaConsentRecordModel]:
        """List consent records for a patient within this tenant."""
        conditions = [
            VitaliaConsentRecordModel.tenant_id == self._tenant_id,
            VitaliaConsentRecordModel.patient_id == patient_id,
        ]
        if status is not None:
            conditions.append(VitaliaConsentRecordModel.status == status)

        stmt = (
            select(VitaliaConsentRecordModel).where(*conditions).order_by(VitaliaConsentRecordModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, consent: VitaliaConsentRecordModel) -> None:
        """Persist a new or updated consent record."""
        self._session.add(consent)
        await self._session.flush()
        logger.info(
            "consent_record_saved",
            consent_id=str(consent.id),
            tenant_id=str(self._tenant_id),
            status=consent.status,
        )

    async def mark_signed(
        self,
        consent_id: uuid.UUID,
        *,
        signed_name: str,
        signed_ip: str,
        signed_user_agent: str,
        signed_at: datetime,
        signature_method: str,
    ) -> bool:
        """Update consent record to status=signed with signature evidence.

        Returns True if the row was found and updated.
        """
        stmt = (
            update(VitaliaConsentRecordModel)
            .where(
                VitaliaConsentRecordModel.id == consent_id,
                VitaliaConsentRecordModel.tenant_id == self._tenant_id,
                VitaliaConsentRecordModel.status == "pending_signature",
            )
            .values(
                status="signed",
                signed_name=signed_name,
                signed_ip=signed_ip,
                signed_user_agent=signed_user_agent,
                signed_at=signed_at,
                signature_method=signature_method,
            )
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        updated = result.rowcount > 0
        if updated:
            logger.info(
                "consent_signed",
                consent_id=str(consent_id),
                tenant_id=str(self._tenant_id),
            )
        return updated

    async def mark_expired(self, consent_id: uuid.UUID) -> bool:
        """Transition consent to expired status."""
        stmt = (
            update(VitaliaConsentRecordModel)
            .where(
                VitaliaConsentRecordModel.id == consent_id,
                VitaliaConsentRecordModel.tenant_id == self._tenant_id,
            )
            .values(status="expired")
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
