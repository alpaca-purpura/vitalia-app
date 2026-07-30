# cap: scheduling.mateo-agenda
# story-origin: TBD
"""AppointmentPaymentRepository — CRUD + optimistic lock + idempotency.

Optimistic lock pattern (03-arch A7 — SC-5 race condition prevention):
  lock_for_charge() → UPDATE WHERE balance_version == expected
  rowcount == 0 → raise BalanceAlreadyChargedError

Idempotency lookup (03-arch A8):
  find_by_idempotency_key() → SELECT WHERE external_payment_id == key
  Returns prior payment if exists → caller skips duplicate charge

HIPAA-lite dual filter: tenant_id + clinic_id on EVERY query.

Per 03-arch § 3.3 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.scheduling.domain.exceptions import BalanceAlreadyChargedError
from src.modules.vitalia.scheduling.persistence.models.appointment_payment_model import (
    AppointmentPaymentModel,
)

logger = structlog.get_logger()


class AppointmentPaymentRepository:
    """Async CRUD repository for vitalia_appointment_payments.

    Implements optimistic lock (balance_version) and idempotency key lookup.
    All queries include tenant_id + clinic_id dual filter (HIPAA-lite).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        amount: int,
        currency: str,
        method: str,
        external_payment_id: str | None = None,
        fiscal_doc_id: UUID | None = None,
        notes: str | None = None,
        created_by_user_id: UUID | None = None,
    ) -> AppointmentPaymentModel:
        """Create a new payment record.

        Args:
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).
            appointment_id: FK to vitalia_appointments.id.
            amount: Amount in integer cents (smallest currency unit).
            currency: ISO 4217 code (PEN/ARS/MXN/USD — NEVER hardcoded).
            method: PaymentMethod enum value.
            external_payment_id: Client-supplied idempotency key.
            fiscal_doc_id: Optional FK to fiscal document.
            notes: Optional payment notes.
            created_by_user_id: User who created the payment.

        Returns:
            Persisted AppointmentPaymentModel (flushed, not committed).
        """
        model = AppointmentPaymentModel(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            appointment_id=appointment_id,
            amount=amount,
            currency=currency,
            method=method,
            external_payment_id=external_payment_id,
            fiscal_doc_id=fiscal_doc_id,
            notes=notes,
            balance_version=1,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(model)
        await self._session.flush()

        logger.info(
            "payment_created",
            payment_id=str(model.id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            appointment_id=str(appointment_id),
            amount=amount,
            currency=currency,
        )
        return model

    async def get_by_id(
        self,
        payment_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AppointmentPaymentModel | None:
        """Get payment by ID with dual filter.

        Args:
            payment_id: Payment UUID.
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).

        Returns:
            AppointmentPaymentModel or None if not found / not accessible.
        """
        stmt = select(AppointmentPaymentModel).where(
            AppointmentPaymentModel.id == payment_id,
            AppointmentPaymentModel.tenant_id == tenant_id,
            AppointmentPaymentModel.clinic_id == clinic_id,
            AppointmentPaymentModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_idempotency_key(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        idempotency_key: str,
    ) -> AppointmentPaymentModel | None:
        """Lookup payment by idempotency key (external_payment_id).

        Used to detect duplicate charge attempts.
        Dual filter applied: tenant_id + clinic_id.

        Args:
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).
            idempotency_key: Client-supplied UUID string (external_payment_id).

        Returns:
            Prior AppointmentPaymentModel if found, None otherwise.
        """
        stmt = select(AppointmentPaymentModel).where(
            AppointmentPaymentModel.tenant_id == tenant_id,
            AppointmentPaymentModel.clinic_id == clinic_id,
            AppointmentPaymentModel.external_payment_id == idempotency_key,
            AppointmentPaymentModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_for_charge(
        self,
        *,
        payment_id: UUID,
        expected_version: int,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> None:
        """Atomically increment balance_version (optimistic lock).

        UPDATE vitalia_appointment_payments
          SET balance_version = balance_version + 1
          WHERE id = payment_id
            AND tenant_id = tenant_id
            AND clinic_id = clinic_id
            AND balance_version = expected_version

        If rowcount == 0: another request already charged this payment.
        Raises BalanceAlreadyChargedError so caller can re-evaluate via
        idempotency key lookup before returning error to user.

        Args:
            payment_id: Payment UUID to lock.
            expected_version: Version read before charge attempt.
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).

        Raises:
            BalanceAlreadyChargedError: If balance_version has already changed.
        """
        stmt = (
            update(AppointmentPaymentModel)
            .where(
                AppointmentPaymentModel.id == payment_id,
                AppointmentPaymentModel.tenant_id == tenant_id,
                AppointmentPaymentModel.clinic_id == clinic_id,
                AppointmentPaymentModel.balance_version == expected_version,
            )
            .values(balance_version=AppointmentPaymentModel.balance_version + 1)
            .execution_options(synchronize_session=False)
        )
        result = await self._session.execute(stmt)

        if result.rowcount == 0:
            logger.warning(
                "optimistic_lock_stale_version",
                payment_id=str(payment_id),
                expected_version=expected_version,
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
            )
            raise BalanceAlreadyChargedError(
                payment_id=payment_id,
                expected_version=expected_version,
            )

        logger.info(
            "payment_lock_acquired",
            payment_id=str(payment_id),
            expected_version=expected_version,
            new_version=expected_version + 1,
        )

    async def list_by_appointment(
        self,
        *,
        appointment_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> list[AppointmentPaymentModel]:
        """List all non-deleted payments for an appointment.

        Dual filter applied: tenant_id + clinic_id.

        Args:
            appointment_id: Appointment UUID.
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).

        Returns:
            List of AppointmentPaymentModel records.
        """
        stmt = (
            select(AppointmentPaymentModel)
            .where(
                AppointmentPaymentModel.appointment_id == appointment_id,
                AppointmentPaymentModel.tenant_id == tenant_id,
                AppointmentPaymentModel.clinic_id == clinic_id,
                AppointmentPaymentModel.deleted_at.is_(None),
            )
            .order_by(AppointmentPaymentModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(
        self,
        payment_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> bool:
        """Soft-delete a payment record (financial records: never hard delete).

        Args:
            payment_id: Payment UUID.
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).

        Returns:
            True if record was found and soft-deleted, False if not found.
        """
        stmt = (
            update(AppointmentPaymentModel)
            .where(
                AppointmentPaymentModel.id == payment_id,
                AppointmentPaymentModel.tenant_id == tenant_id,
                AppointmentPaymentModel.clinic_id == clinic_id,
                AppointmentPaymentModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session=False)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
