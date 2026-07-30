# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Async repository — VitaliaMedicalAuditLogModel.

All queries filter by tenant_id (mandatory, per tenant-isolation.md).
Medical audit log is IMMUTABLE (append-only, no deleted_at, HIPAA-lite 7-year retention).
No soft_delete method — audit log rows must never be deleted.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.medical_audit_log_model import (
    VitaliaMedicalAuditLogModel,
)

logger = structlog.get_logger()


class MedicalAuditLogRepository:
    """Tenant-scoped async repository for VitaliaMedicalAuditLogModel.

    APPEND-ONLY. No update, no delete. Compliant with HIPAA-lite 7-year retention.
    All writes must sanitize PII via sanitize_payload() before calling save().
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_by_id(self, audit_id: uuid.UUID) -> VitaliaMedicalAuditLogModel | None:
        """Return audit log entry by ID for this tenant."""
        stmt = select(VitaliaMedicalAuditLogModel).where(
            VitaliaMedicalAuditLogModel.id == audit_id,
            VitaliaMedicalAuditLogModel.tenant_id == self._tenant_id,
            # Note: no deleted_at filter — audit log is immutable
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_event_type(
        self,
        event_type: str,
        *,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[VitaliaMedicalAuditLogModel]:
        """List audit events by type for this tenant, ordered by created_at desc."""
        conditions = [
            VitaliaMedicalAuditLogModel.tenant_id == self._tenant_id,
            VitaliaMedicalAuditLogModel.event_type == event_type,
        ]
        if since is not None:
            conditions.append(VitaliaMedicalAuditLogModel.created_at >= since)

        stmt = (
            select(VitaliaMedicalAuditLogModel)
            .where(*conditions)
            .order_by(VitaliaMedicalAuditLogModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_severity(
        self,
        severity: str,
        *,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[VitaliaMedicalAuditLogModel]:
        """List audit events by severity for compliance reporting."""
        conditions = [
            VitaliaMedicalAuditLogModel.tenant_id == self._tenant_id,
            VitaliaMedicalAuditLogModel.severity == severity,
        ]
        if since is not None:
            conditions.append(VitaliaMedicalAuditLogModel.created_at >= since)

        stmt = (
            select(VitaliaMedicalAuditLogModel)
            .where(*conditions)
            .order_by(VitaliaMedicalAuditLogModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_patient(
        self,
        patient_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[VitaliaMedicalAuditLogModel]:
        """List audit events linked to a patient (for patient data export)."""
        stmt = (
            select(VitaliaMedicalAuditLogModel)
            .where(
                VitaliaMedicalAuditLogModel.tenant_id == self._tenant_id,
                VitaliaMedicalAuditLogModel.patient_id == patient_id,
            )
            .order_by(VitaliaMedicalAuditLogModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, audit_event: VitaliaMedicalAuditLogModel) -> None:
        """Append a new audit log entry (INSERT only — never UPDATE/DELETE).

        Caller is responsible for sanitizing PII via sanitize_payload() before
        this method is called. Best-effort writes: caller should wrap in
        try/except + structlog.warning (per ComplianceEventService pattern).
        """
        self._session.add(audit_event)
        await self._session.flush()
        logger.info(
            "medical_audit_log_written",
            audit_id=str(audit_event.id),
            tenant_id=str(self._tenant_id),
            event_type=audit_event.event_type,
            severity=audit_event.severity,
        )
