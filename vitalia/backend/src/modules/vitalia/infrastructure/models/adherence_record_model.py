# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaAdherenceRecordModel.

Maps to `vitalia_adherence_records` table.
Per-step adherence metric for treatment followup. No deleted_at.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaAdherenceRecordModel(Base):
    """Per-step adherence measurement for treatment followup.

    Appended once per step-checkpoint interaction (D0, D5, D14, D30, D90).
    Sentiment + classifier metadata support ML-based score calibration.
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    """

    __tablename__ = "vitalia_adherence_records"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    treatment_followup_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    # "D0_init" / "D5_check" / "D14_check" / etc.
    step_name: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)  # 1-5
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    classifier_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # No deleted_at — adherence records are measurement artifacts
