# cap: scheduling.mateo-agenda
# story-origin: TBD
"""SQLAlchemy 2.0 model — vitalia_appointment_payments.

Mirrors DDL from T-1 migration (032_f2_s1_vitalia_agenda.py).

HIPAA-lite dual filter: EVERY query MUST include tenant_id + clinic_id.
No PHI stored here (no patient.name, no DNI). appointment_id links to engine.

Optimistic lock: balance_version column (03-arch A7, SC-5 race condition).
Idempotency: external_payment_id unique index (03-arch A8).

Per 03-arch § 2.3 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class AppointmentPaymentModel(Base):
    """SQLAlchemy 2.0 model for vitalia_appointment_payments.

    Financial record: no hard deletes (deleted_at soft-delete pattern).
    balance_version: optimistic lock — incremented atomically on charge.
    external_payment_id: idempotency key (client-supplied UUID → unique constraint).
    """

    __tablename__ = "vitalia_appointment_payments"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
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
    appointment_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("vitalia_appointments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Amount in integer cents (smallest currency unit) per .claude/rules/currency-handling.md
    # Migration column: `amount INTEGER NOT NULL`
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    # ISO 4217 currency code — NEVER default to 'USD' (master-data.md)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fiscal_doc_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("vitalia_fiscal_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Optimistic lock version — starts at 1, incremented atomically on charge
    balance_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
