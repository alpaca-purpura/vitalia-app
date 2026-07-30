# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Async repository — VitaliaPaymentIntentModel.

All queries filter by tenant_id (mandatory, per tenant-isolation.md).
Payment intents have NO deleted_at (financial record — immutable).
"""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.payment_intent_model import (
    VitaliaPaymentIntentModel,
)

logger = structlog.get_logger()


class PaymentIntentRepository:
    """Tenant-scoped async repository for VitaliaPaymentIntentModel.

    Payment intents are financial records — no soft delete (no deleted_at column).
    Status transitions are append-via-update; rows are never physically removed.
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_by_id(self, intent_id: uuid.UUID) -> VitaliaPaymentIntentModel | None:
        """Return payment intent by ID for this tenant."""
        stmt = select(VitaliaPaymentIntentModel).where(
            VitaliaPaymentIntentModel.id == intent_id,
            VitaliaPaymentIntentModel.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> VitaliaPaymentIntentModel | None:
        """Return payment intent by idempotency key for this tenant.

        Used for idempotent payment initiation — returns existing if same key.
        """
        stmt = select(VitaliaPaymentIntentModel).where(
            VitaliaPaymentIntentModel.tenant_id == self._tenant_id,
            VitaliaPaymentIntentModel.idempotency_key == idempotency_key,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_gateway_payment_id(self, gateway_payment_id: str) -> VitaliaPaymentIntentModel | None:
        """Return payment intent by gateway_payment_id (for webhook matching).

        Note: gateway_payment_id has a unique constraint but no tenant_id filter
        by design (webhooks arrive without tenant context). We still filter by
        tenant_id for safety — webhook handlers must resolve tenant first.
        """
        stmt = select(VitaliaPaymentIntentModel).where(
            VitaliaPaymentIntentModel.tenant_id == self._tenant_id,
            VitaliaPaymentIntentModel.gateway_payment_id == gateway_payment_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_booking(self, booking_id: uuid.UUID) -> list[VitaliaPaymentIntentModel]:
        """List all payment intents for a booking within this tenant."""
        stmt = (
            select(VitaliaPaymentIntentModel)
            .where(
                VitaliaPaymentIntentModel.tenant_id == self._tenant_id,
                VitaliaPaymentIntentModel.booking_id == booking_id,
            )
            .order_by(VitaliaPaymentIntentModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, intent: VitaliaPaymentIntentModel) -> None:
        """Persist a new or updated payment intent."""
        self._session.add(intent)
        await self._session.flush()
        logger.info(
            "payment_intent_saved",
            intent_id=str(intent.id),
            tenant_id=str(self._tenant_id),
            gateway=intent.gateway,
            status=intent.status,
        )

    async def update_status(
        self,
        intent_id: uuid.UUID,
        *,
        status: str,
        gateway_payment_id: str | None = None,
        failure_reason: str | None = None,
    ) -> bool:
        """Update payment intent status (succeeded / failed / refunded).

        Returns True if the row was found and updated.
        """
        values: dict = {"status": status}
        if gateway_payment_id is not None:
            values["gateway_payment_id"] = gateway_payment_id
        if failure_reason is not None:
            values["failure_reason"] = failure_reason

        stmt = (
            update(VitaliaPaymentIntentModel)
            .where(
                VitaliaPaymentIntentModel.id == intent_id,
                VitaliaPaymentIntentModel.tenant_id == self._tenant_id,
            )
            .values(**values)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        updated = result.rowcount > 0
        if updated:
            logger.info(
                "payment_intent_status_updated",
                intent_id=str(intent_id),
                tenant_id=str(self._tenant_id),
                new_status=status,
            )
        return updated
