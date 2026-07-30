# cap: clinics.lisa.doctores
"""VitaliaAvailabilitySlotModel — SQLAlchemy 2.0 model for vitalia_availability_slots.

Maps to the table created in migration 036_f2_s8_vitalia_lisa_staff.py.
Slots are materialized by AvailabilityProjectionService (dateutil.rrule expansion).

has_confirmed_appointment: prevents deletion on block retire/delete (SC-1d, SC-3b).
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, Date, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaAvailabilitySlotModel(Base):
    """Materialized time slot projected from an AvailabilityBlock.

    slot_date: calendar date of the slot (for range queries)
    start_ts / end_ts: UTC-aware datetime boundaries
    has_confirmed_appointment: True = scheduling module booked this slot
    block_id: FK to vitalia_availability_blocks (ON DELETE CASCADE)
    """

    __tablename__ = "vitalia_availability_slots"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    doctor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    # FK to parent block (ON DELETE CASCADE — DDL in migration 036)
    block_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True, index=True)

    slot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    has_confirmed_appointment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_vitalia_availability_slots_tenant_doctor_date", "tenant_id", "doctor_id", "slot_date"),)
