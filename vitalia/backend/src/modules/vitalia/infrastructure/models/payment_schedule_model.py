# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaPaymentScheduleModel.

Maps to `vitalia_payment_schedules` table.
Recurring / installment plan per booking. No deleted_at (financial record).
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


class VitaliaPaymentScheduleModel(Base):
    """Recurring / installment payment schedule.

    One row per planned installment charge (installment_n = 1, 2, 3...).
    Linked to a booking; payment_intent_id populated when charge executes.
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    """

    __tablename__ = "vitalia_payment_schedules"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    booking_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    # "mercadopago" / "stripe_connect" / "tokenized_recurring"
    gateway: Mapped[str] = mapped_column(String(32), nullable=False)
    installment_n: Mapped[int] = mapped_column(nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO 4217
    # "scheduled" / "processing" / "succeeded" / "failed" / "cancelled"
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")
    # Populated when payment is executed
    payment_intent_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    schedule_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # No deleted_at — financial record
