# cap: fiscal.fiscal-emission-pe
# story-origin: TBD
"""FiscalDocumentRepository — CRUD for fiscal documents (saga compensation).

Charge saga compensation (03-arch A6):
  Payment OK + fiscal emit fail → retry emit standalone.
  FiscalDocument.status: pending → emitted | failed.
  update_status() used by retry mechanism.

HIPAA-lite dual filter: tenant_id + clinic_id on ALL queries.

Per 03-arch § 3.5 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.fiscal.infrastructure.models.fiscal_document_model import (
    FiscalDocumentModel,
)

logger = structlog.get_logger()


class FiscalDocumentRepository:
    """Async CRUD repository for vitalia_fiscal_documents.

    All queries include tenant_id + clinic_id dual filter (HIPAA-lite).
    Fiscal documents follow saga compensation status lifecycle:
      pending → emitted | failed → (retry → emitted)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_payment_id: UUID,
        doc_type: str,
        provider: str,
        doc_number: str | None = None,
        doc_url: str | None = None,
        status: str = "pending",
    ) -> FiscalDocumentModel:
        """Create a new fiscal document record.

        Args:
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).
            appointment_payment_id: FK to vitalia_appointment_payments.id.
            doc_type: FiscalDocType enum value (boleta/factura/cfdi/ticket).
            provider: Provider slug (nubefact_stub/nubefact/afip/sat).
            doc_number: Provider-issued serial (None until emitted).
            doc_url: PDF/XML download link (None until emitted).
            status: Initial status (default "pending").

        Returns:
            Persisted FiscalDocumentModel (flushed, not committed).
        """
        model = FiscalDocumentModel(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            appointment_payment_id=appointment_payment_id,
            doc_type=doc_type,
            provider=provider,
            doc_number=doc_number,
            doc_url=doc_url,
            status=status,
        )
        self._session.add(model)
        await self._session.flush()

        logger.info(
            "fiscal_document_created",
            doc_id=str(model.id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            payment_id=str(appointment_payment_id),
            doc_type=doc_type,
            provider=provider,
        )
        return model

    async def get_by_id(
        self,
        doc_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> FiscalDocumentModel | None:
        """Get fiscal document by ID with dual filter.

        Args:
            doc_id: Fiscal document UUID.
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).

        Returns:
            FiscalDocumentModel or None if not found / not accessible.
        """
        stmt = select(FiscalDocumentModel).where(
            FiscalDocumentModel.id == doc_id,
            FiscalDocumentModel.tenant_id == tenant_id,
            FiscalDocumentModel.clinic_id == clinic_id,
            FiscalDocumentModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_payment_id(
        self,
        payment_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> FiscalDocumentModel | None:
        """Get fiscal document by payment ID with dual filter.

        Used by saga compensation to find existing doc before retry.

        Args:
            payment_id: FK to vitalia_appointment_payments.id.
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).

        Returns:
            Most recent FiscalDocumentModel for the payment, or None.
        """
        stmt = (
            select(FiscalDocumentModel)
            .where(
                FiscalDocumentModel.appointment_payment_id == payment_id,
                FiscalDocumentModel.tenant_id == tenant_id,
                FiscalDocumentModel.clinic_id == clinic_id,
                FiscalDocumentModel.deleted_at.is_(None),
            )
            .order_by(FiscalDocumentModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        doc_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        status: str,
        doc_number: str | None = None,
        doc_url: str | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Update fiscal document status (saga state machine transition).

        Dual filter applied on UPDATE.

        Args:
            doc_id: Fiscal document UUID.
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).
            status: New status ("emitted" or "failed").
            doc_number: Provider-issued serial (set on success).
            doc_url: PDF/XML download URL (set on success).
            error_message: Error detail (set on failure).

        Returns:
            True if document was found and updated, False otherwise.
        """
        values: dict = {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
        if doc_number is not None:
            values["doc_number"] = doc_number
        if doc_url is not None:
            values["doc_url"] = doc_url
        if error_message is not None:
            values["error_message"] = error_message

        stmt = (
            update(FiscalDocumentModel)
            .where(
                FiscalDocumentModel.id == doc_id,
                FiscalDocumentModel.tenant_id == tenant_id,
                FiscalDocumentModel.clinic_id == clinic_id,
                FiscalDocumentModel.deleted_at.is_(None),
            )
            .values(**values)
            .execution_options(synchronize_session=False)
        )
        result = await self._session.execute(stmt)

        logger.info(
            "fiscal_document_status_updated",
            doc_id=str(doc_id),
            status=status,
            tenant_id=str(tenant_id),
        )
        return result.rowcount > 0

    async def list_failed_for_retry(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        limit: int = 100,
    ) -> list[FiscalDocumentModel]:
        """List failed fiscal documents eligible for retry.

        Saga compensation: failed documents can be retried standalone.
        Dual filter applied.

        Args:
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).
            limit: Max records to return.

        Returns:
            List of failed FiscalDocumentModel records.
        """
        stmt = (
            select(FiscalDocumentModel)
            .where(
                FiscalDocumentModel.tenant_id == tenant_id,
                FiscalDocumentModel.clinic_id == clinic_id,
                FiscalDocumentModel.status == "failed",
                FiscalDocumentModel.deleted_at.is_(None),
            )
            .order_by(FiscalDocumentModel.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
