# cap: scheduling.mateo-agenda
# story-origin: TBD
"""SQLAlchemy 2.0 model — vitalia_appointment_clinic_map.

Brand-local extension for appointment metadata (03-arch A12).
Stores service_label, origin, currency_override, patient_id, doctor_id
without modifying the core vitalia_appointments record.

HIPAA-lite dual filter: tenant_id + clinic_id required on all queries.

Per 03-arch § 2.5 + vitalia/.clone/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class AppointmentClinicMapModel(Base):
    """SQLAlchemy 2.0 model for vitalia_appointment_clinic_map.

    One-to-one with vitalia_appointments (appointment_id is PK).
    Stores brand-local metadata: service_label, origin badge, currency_override.

    Architecture decision A12: brand-local FK avoids modifying engine appointment record.

    IMPORTANT — ORM FK intentionally absent (bug #8 fix, 2026-06-23):
    vitalia_appointments has NO Python SQLAlchemy model class — it is managed via
    raw Alembic migrations only (see agenda_grid_repository_impl.py lines 54-65).
    Adding ForeignKey("vitalia_appointments.id") here causes NoReferencedTableError
    at flush() because SQLAlchemy's mapper can't resolve a FK to an unmapped table.
    The DB-level FK constraint (ON DELETE CASCADE) is correctly created by migration 050
    and enforced by Postgres — no ORM-level declaration is needed or correct here.
    """

    __tablename__ = "vitalia_appointment_clinic_map"

    appointment_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    clinic_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    doctor_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    service_label: Mapped[str] = mapped_column(String(128), nullable=False)
    # AppointmentOrigin enum value: walk_in | telefono | proactivo_adrian | portal
    origin: Mapped[str] = mapped_column(String(32), nullable=False)
    # Per-appointment currency override (tenant default otherwise) — currency-handling.md
    # ISO 4217 code: PEN/ARS/MXN/USD/... — None means use tenant locale default
    currency_override: Mapped[str | None] = mapped_column(String(3), nullable=True)
    # Hold-status columns (T-BE-2 / RN-26 — added idempotently via migration 047)
    # None = no hold (manual create); 'hold_pending_payment' = pending payment within TTL;
    # 'confirmed' = payment received; 'expired' = TTL elapsed, slot released
    hold_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    # UTC expiry of the hold (None for non-hold appointments)
    hold_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # True if the hold was created by the Adrián sales agent (vs manual staff)
    hold_created_by_agent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    # ── Mirror columns (schema-mirror exception — backend-ddd.md § schema-mirror-exception) ──
    # Added by migration 050 (T-BE-2). These mirror vitalia_appointments.start_time/end_time/status
    # so that the EXCLUDE USING gist constraint can reference them on this brand-local table.
    # Domain boundary: EXCLUDE lives here (has doctor_id); engine table has no doctor_id.
    # cap: scheduling.mateo-agenda (RN-2 half-open, RN-6 CANCELLED exclusion)
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # AppointmentStatus value: SCHEDULED | CONFIRMED | CANCELLED | COMPLETED | NO_SHOW
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Soft delete (brand consistency per backend-ddd.md)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
