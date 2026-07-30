# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaPaymentIntentModel.

Maps to `vitalia_payment_intents` table.
Per-booking payment intent. No deleted_at (financial record).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaPaymentIntentModel(Base):
    """Payment intent — financial record (no soft-delete).

    Tracks the lifecycle of a payment charge per booking.
    Gateway-agnostic: supports mercadopago, stripe_connect, tokenized_recurring.
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    """

    __tablename__ = "vitalia_payment_intents"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    booking_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    # "mercadopago" / "stripe_connect" / "tokenized_recurring"
    gateway: Mapped[str] = mapped_column(String(32), nullable=False)
    gateway_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO 4217
    # "initiated" / "processing" / "succeeded" / "failed" / "refunded"
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # No deleted_at — financial record
