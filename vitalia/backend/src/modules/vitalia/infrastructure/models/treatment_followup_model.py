# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaTreatmentFollowupModel.

Maps to `vitalia_treatment_followups` table.
LangGraph workflow state per (booking, patient, doctor). Soft-delete.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaTreatmentFollowupModel(Base):
    """Treatment followup LangGraph workflow state.

    Tracks step progression through the post-procedure followup protocol
    (D0_init → D5_check → D14_check → D30_check → D90_check → completed).
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    deleted_at enables soft-delete.
    """

    __tablename__ = "vitalia_treatment_followups"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    booking_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    doctor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    # "dental_implant" / "psychology_individual" / etc.
    plan_template_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    # "D0_init"/"D5_check"/"D14_check"/"D30_check"/"D90_check"/"completed"/"paused_*"/"dropped"
    current_step: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    adherence_score: Mapped[int | None] = mapped_column(nullable=True)  # 1-5 cumulative
    paused_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # FK to Redis LangGraph checkpoint
    langgraph_checkpoint_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
