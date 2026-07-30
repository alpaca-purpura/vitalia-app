# cap: clinics.lisa.doctores
"""VitaliaAvailabilityBlockModel — SQLAlchemy 2.0 model for vitalia_availability_blocks.

Maps to the table created in migration 036_f2_s8_vitalia_lisa_staff.py.
D3-F extension (migration 042): days_of_week JSONB + interval INTEGER columns added.
No PII columns — availability data is scheduling metadata, not PHI.

Slots are materialized in VitaliaAvailabilitySlotModel by AvailabilityProjectionService.
"""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Date, DateTime, Index, Integer, String, Time
from sqlalchemy.dialects.postgresql import JSON as PgJSON
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaAvailabilityBlockModel(Base):
    """Availability block (recurrent or one_off) for a doctor in a clinic.

    kind='recurrent': days_of_week + interval + start_time + end_time +
                      end_condition_kind (end_date | occurrences | open_ended)
    kind='one_off':   specific_date + start_time + end_time

    D3-F primary fields (migration 042):
      days_of_week: list[int] stored as JSONB (multi-day recurrence)
      interval: int (recurrence interval in weeks; 1=weekly, 2=biweekly, N custom)

    Legacy compat fields (pre-D3-F, kept for backward compat):
      day_of_week: int | None (single weekday — backfilled from days_of_week[0])
      freq: str | None ("weekly"|"biweekly" — backfilled from interval)
    """

    __tablename__ = "vitalia_availability_blocks"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    doctor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    kind: Mapped[str] = mapped_column(String(16), nullable=False)

    # D3-F primary recurrent fields (added in migration 042)
    days_of_week: Mapped[list[int] | None] = mapped_column(PgJSON, nullable=True)
    """Multi-day weekday list stored as JSONB (0=Mon..6=Sun). NULL before migration 042."""

    # ⚠️ "interval" is a PostgreSQL reserved word — quoted in all DDL/DML (migration 042)
    interval: Mapped[int | None] = mapped_column("interval", Integer, nullable=True)
    """Recurrence interval in weeks. NULL before migration 042 backfill."""

    # Legacy recurrent fields (pre-D3-F — kept for compat, backfilled by migration 042)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    freq: Mapped[str | None] = mapped_column(String(16), nullable=True)
    end_condition_kind: Mapped[str | None] = mapped_column(String(16), nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    occurrences: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # One-off field
    specific_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Scoped-delete exclusions (Feature: occurrence-level delete)
    excluded_dates: Mapped[list[str] | None] = mapped_column(PgJSON, nullable=True)
    """List of ISO date strings ("YYYY-MM-DD") for individually excluded occurrences."""

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_vitalia_availability_blocks_tenant_clinic", "tenant_id", "clinic_id"),
        Index("ix_vitalia_availability_blocks_tenant_doctor", "tenant_id", "doctor_id"),
    )
