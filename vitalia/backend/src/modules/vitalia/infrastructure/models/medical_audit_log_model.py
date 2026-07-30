# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaMedicalAuditLogModel.

Maps to `vitalia_medical_audit_log` table.
HIPAA-lite 7-year retention. IMMUTABLE — NO deleted_at, append-only.
PII sanitized in payload_redacted.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaMedicalAuditLogModel(Base):
    """Medical audit log — IMMUTABLE.

    Append-only event log for HIPAA-lite compliance. Records security events,
    consent actions, cross-tenant access attempts, PII detections, and
    safety escalations. No deleted_at — 7-year retention enforced via
    separate purge job post-retention window.

    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    """

    __tablename__ = "vitalia_medical_audit_log"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    # See § 15.4 02-design-agentic.md event types
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # "info" / "medium" / "high"
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    patient_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    booking_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    # PII-sanitized payload
    payload_redacted: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    actor_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    # "clinic_owner" / "sales_agent" / "system" / "patient"
    actor_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default=func.now()
    )
    # NO deleted_at — audit log is immutable, 7-year retention via separate purge job

    __table_args__ = (
        Index(
            "ix_vitalia_audit_tenant_event_created",
            "tenant_id",
            "event_type",
            "created_at",
        ),
        Index(
            "ix_vitalia_audit_tenant_severity_created",
            "tenant_id",
            "severity",
            "created_at",
        ),
    )
