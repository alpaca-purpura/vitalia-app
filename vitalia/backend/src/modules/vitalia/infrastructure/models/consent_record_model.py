# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — VitaliaConsentRecordModel.

Maps to `vitalia_consent_records` table.
Legal consent capture. No deleted_at — legal immutability preserved.
Status-based lifecycle: pending_signature → signed / expired / revoked.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class VitaliaConsentRecordModel(Base):
    """Legal consent record.

    Full snapshot of consent template + patient signature evidence.
    7-year legal retention. Uses status lifecycle instead of soft-delete:
    revoked state replaces deleted_at.
    tenant_id is NOT NULL + indexed (R2 tenant-isolation).
    """

    __tablename__ = "vitalia_consent_records"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    booking_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)  # nullable pre-booking
    consent_template_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    template_version: Mapped[str] = mapped_column(String(16), nullable=False)
    # Full content snapshot for legal record
    template_snapshot_md: Mapped[str] = mapped_column(Text, nullable=False)
    signed_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signed_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 compat
    signed_user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # "typed_name" / "signature_pad"
    signature_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_signature")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 24h default
    # ["whatsapp", "email"]
    delivery_channels: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # No deleted_at — legal immutability (use status=revoked instead)
