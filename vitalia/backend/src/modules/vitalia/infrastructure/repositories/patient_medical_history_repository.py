# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Async repository — VitaliaPatientMedicalHistoryModel + VitaliaPatientDentalHistoryModel.

All queries filter by tenant_id (mandatory, per tenant-isolation.md).
Soft deletes: deleted_at IS NULL filter on reads.

Both history types follow the same SQLA 2.0 pattern; grouped in one file
per § 3.1 DDD layout (mirrors the grouped model file).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.medical_history_model import (
    VitaliaPatientDentalHistoryModel,
    VitaliaPatientMedicalHistoryModel,
)

logger = structlog.get_logger()


class PatientMedicalHistoryRepository:
    """Tenant-scoped async repository for patient medical and dental histories.

    Contains both VitaliaPatientMedicalHistoryModel and
    VitaliaPatientDentalHistoryModel operations. Grouped per arch § 3.1 layout
    (same domain concept: extracted patient history).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ------------------------------------------------------------------ Medical

    async def get_medical_by_id(self, history_id: uuid.UUID) -> VitaliaPatientMedicalHistoryModel | None:
        """Return medical history by ID for this tenant."""
        stmt = select(VitaliaPatientMedicalHistoryModel).where(
            VitaliaPatientMedicalHistoryModel.id == history_id,
            VitaliaPatientMedicalHistoryModel.tenant_id == self._tenant_id,
            VitaliaPatientMedicalHistoryModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_medical_by_patient(self, patient_id: uuid.UUID) -> VitaliaPatientMedicalHistoryModel | None:
        """Return the latest active medical history for a patient."""
        stmt = (
            select(VitaliaPatientMedicalHistoryModel)
            .where(
                VitaliaPatientMedicalHistoryModel.tenant_id == self._tenant_id,
                VitaliaPatientMedicalHistoryModel.patient_id == patient_id,
                VitaliaPatientMedicalHistoryModel.deleted_at.is_(None),
            )
            .order_by(VitaliaPatientMedicalHistoryModel.last_extracted_at.desc().nullslast())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def save_medical(self, history: VitaliaPatientMedicalHistoryModel) -> None:
        """Persist a new or updated patient medical history."""
        self._session.add(history)
        await self._session.flush()
        logger.info(
            "medical_history_saved",
            history_id=str(history.id),
            patient_id=str(history.patient_id),
            tenant_id=str(self._tenant_id),
        )

    async def soft_delete_medical(self, history_id: uuid.UUID) -> bool:
        """Soft-delete a medical history record."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(VitaliaPatientMedicalHistoryModel)
            .where(
                VitaliaPatientMedicalHistoryModel.id == history_id,
                VitaliaPatientMedicalHistoryModel.tenant_id == self._tenant_id,
                VitaliaPatientMedicalHistoryModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    # ------------------------------------------------------------------ Dental

    async def get_dental_by_id(self, history_id: uuid.UUID) -> VitaliaPatientDentalHistoryModel | None:
        """Return dental history by ID for this tenant."""
        stmt = select(VitaliaPatientDentalHistoryModel).where(
            VitaliaPatientDentalHistoryModel.id == history_id,
            VitaliaPatientDentalHistoryModel.tenant_id == self._tenant_id,
            VitaliaPatientDentalHistoryModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_dental_by_patient(self, patient_id: uuid.UUID) -> VitaliaPatientDentalHistoryModel | None:
        """Return the latest active dental history for a patient."""
        stmt = (
            select(VitaliaPatientDentalHistoryModel)
            .where(
                VitaliaPatientDentalHistoryModel.tenant_id == self._tenant_id,
                VitaliaPatientDentalHistoryModel.patient_id == patient_id,
                VitaliaPatientDentalHistoryModel.deleted_at.is_(None),
            )
            .order_by(VitaliaPatientDentalHistoryModel.last_extracted_at.desc().nullslast())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def save_dental(self, history: VitaliaPatientDentalHistoryModel) -> None:
        """Persist a new or updated patient dental history."""
        self._session.add(history)
        await self._session.flush()
        logger.info(
            "dental_history_saved",
            history_id=str(history.id),
            patient_id=str(history.patient_id),
            tenant_id=str(self._tenant_id),
        )

    async def soft_delete_dental(self, history_id: uuid.UUID) -> bool:
        """Soft-delete a dental history record."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(VitaliaPatientDentalHistoryModel)
            .where(
                VitaliaPatientDentalHistoryModel.id == history_id,
                VitaliaPatientDentalHistoryModel.tenant_id == self._tenant_id,
                VitaliaPatientDentalHistoryModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
