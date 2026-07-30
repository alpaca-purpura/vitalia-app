# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaBookingModel.

Maps to `vitalia_bookings` table (created in 001_vitalia_initial_snapshot.py).
Tenant-scoped + soft-delete. Aggregate root for the booking flow.

Columns mirror T-be-1 migration DDL exactly.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaBookingModel(Base):
    """Booking aggregate root.

    Covers the full booking lifecycle from slot reservation through
    payment, consent capture, and completion.
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    deleted_at enables soft-delete (hard deletes forbidden per backend-ddd.md).
    """

    __tablename__ = "vitalia_bookings"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    offer_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    doctor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    consent_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    slot_iso: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False)
    # "pending_payment"/"awaiting_consent"/"confirmed_deposit"/"confirmed_full"/"cancelled"/"completed"
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_initiated")
    amount_paid: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    amount_pending: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)  # ISO 4217
    deposit_percent: Mapped[int | None] = mapped_column(nullable=True)
    booking_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_vitalia_bookings_tenant_doctor_slot",
            "tenant_id",
            "doctor_id",
            "slot_iso",
        ),
        Index("ix_vitalia_bookings_patient", "patient_id"),
        Index(
            "ix_vitalia_bookings_tenant_status_created",
            "tenant_id",
            "status",
            "created_at",
        ),
    )
