# cap: fidelizacion.re-engagement
# story-origin: TBD
"""SQLAlchemy 2.0 model — vitalia_re_engagement_events.

Mapea la tabla particionada creada en migration 021.
PK compuesta: (id, trigger_at) — requerida para particionado por RANGE.
PHI: payload_phi BYTEA (pgcrypto). Dual filter: tenant_id + clinic_id.

NOTA: La tabla está PARTITIONED BY RANGE (trigger_at). SQLAlchemy NO necesita
decoración especial — el particionado se gestiona a nivel DB (migration 021).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class ReEngagementEventModel(Base):
    """ORM model para vitalia_re_engagement_events (tabla particionada).

    PHI: payload_phi (BYTEA pgcrypto). Dual filter: tenant_id + clinic_id.
    Composite PK (id, trigger_at) requerida por PostgreSQL particionado.
    Soft delete: deleted_at.
    """

    __tablename__ = "vitalia_re_engagement_events"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, default=uuid4)
    trigger_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    pattern: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(64), nullable=False)

    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    converted_to_appointment_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    # PHI — cifrado pgcrypto (symmetric encryption at rest, hipaa-lite.md)
    payload_phi: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)

    audit_log_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # non-PHI notes
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Composite PK: requerida para tabla particionada por RANGE(trigger_at)
        # PG requiere que la PK incluya la columna de partición
        PrimaryKeyConstraint("id", "trigger_at"),
        Index(
            "ix_vitalia_re_engagement_events_pattern_patient",
            "tenant_id",
            "clinic_id",
            "patient_id",
            "pattern",
            "trigger_at",
        ),
        Index(
            "ix_vitalia_re_engagement_events_throttle",
            "tenant_id",
            "clinic_id",
            "patient_id",
            "pattern",
            "sent_at",
        ),
        Index(
            "ix_vitalia_re_engagement_events_outcome_status",
            "tenant_id",
            "clinic_id",
            "outcome",
            "trigger_at",
        ),
    )
