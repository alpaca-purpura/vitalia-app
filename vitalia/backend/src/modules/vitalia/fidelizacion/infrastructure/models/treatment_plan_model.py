# cap: treatments.treatment-followup-workflow
# story-origin: TBD
"""SQLAlchemy 2.0 model — vitalia_treatment_plans.

Mapea la tabla creada en migration 020. PHI: notes BYTEA (pgcrypto).
Dual filter: tenant_id + clinic_id obligatorio (HIPAA-lite vitalia).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TreatmentPlanModel(Base):
    """ORM model para vitalia_treatment_plans.

    PHI: notes (BYTEA pgcrypto). Dual filter: tenant_id + clinic_id.
    Soft delete: deleted_at.
    """

    __tablename__ = "vitalia_treatment_plans"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    offer_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    doctor_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    sessions_total: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions_completed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    next_session_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gap_alert_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="active")

    # PHI — cifrado pgcrypto (symmetric encryption at rest, hipaa-lite.md)
    notes: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)

    last_session_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pause_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_vitalia_treatment_plans_tenant_clinic_status",
            "tenant_id",
            "clinic_id",
            "status",
        ),
        Index(
            "ix_vitalia_treatment_plans_patient",
            "tenant_id",
            "clinic_id",
            "patient_id",
            "status",
        ),
        Index(
            "ix_vitalia_treatment_plans_gap_query",
            "tenant_id",
            "clinic_id",
            "last_session_at",
            "gap_alert_days",
        ),
    )
