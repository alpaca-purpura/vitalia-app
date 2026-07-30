# cap: fiscal.fiscal-emission-pe
# story-origin: TBD
"""SQLAlchemy 2.0 model — vitalia_fiscal_documents.

Mirrors DDL from T-1 migration (032_f2_s1_vitalia_agenda.py).

Service-blocker context: vitalia-fiscal-emission-pe is NOT yet developed (F2-S1 stub phase).
When service-blocker ships, the real provider implementations will use this model unchanged.

Charge saga compensation (03-arch A6):
  status lifecycle: pending → emitted | failed
  Payment OK + fiscal fail → retry emit standalone (no payment rollback).

HIPAA-lite dual filter: tenant_id + clinic_id on all queries.

Per 03-arch § 2.4 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class FiscalDocumentModel(Base):
    """SQLAlchemy 2.0 model for vitalia_fiscal_documents.

    Stub-safe: works with real or stub fiscal providers.
    status: 'pending' | 'emitted' | 'failed' (saga compensation state machine).
    doc_number + doc_url: None until provider confirms emission.
    """

    __tablename__ = "vitalia_fiscal_documents"

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
    appointment_payment_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
    )
    # FiscalDocType enum value: boleta | factura | factura_a | factura_b |
    # recibo | cfdi | ticket (covers PE/AR/MX territories)
    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # Provider-issued document serial number (None until emitted)
    doc_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # PDF/XML download URL (None until emitted)
    doc_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Provider identifier: nubefact_stub | nubefact | afip | sat | etc.
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    # Saga state: pending → emitted | failed
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    # Last error message for failed documents (supports retry display)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Soft delete
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
