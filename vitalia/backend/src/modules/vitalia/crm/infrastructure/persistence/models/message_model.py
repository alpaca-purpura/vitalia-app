# cap: crm.crm-consent-optout
# story-origin: TBD
"""MessageModel — SQLAlchemy 2.0 mapped class for vitalia_messages.

Infrastructure layer — ORM model only. No domain logic.

PHI dual-filter (hipaa-lite.md): every query MUST filter by tenant_id AND clinic_id.
Soft-delete: deleted_at=NULL means active; never use hard DELETE.

SC-01: AI messages get ActionReceipt for 5min undo window.
SC-02: transcription_text PHI — sanitize before traces (service layer responsibility).

downstream-regression-na: brand-local vitalia CRM infra model
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class MessageModel(Base):
    """SQLAlchemy model for vitalia_messages table.

    PHI fields:
    - transcription_text: may contain patient speech (PHI) — sanitize before traces
    - media_url: may reference PHI images/audio
    - clinic_id: second scope filter (HIPAA-lite dual filter)

    All timestamp columns use timezone=True (TIMESTAMPTZ at DB level).
    """

    __tablename__ = "vitalia_messages"
    __table_args__ = (
        Index(
            "ix_vitalia_messages_tenant_clinic",
            "tenant_id",
            "clinic_id",
        ),
        Index(
            "ix_vitalia_messages_conversation_id",
            "conversation_id",
        ),
        Index(
            "ix_vitalia_messages_external_message_id",
            "external_message_id",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # PHI dual-filter keys (hipaa-lite.md: tenant_id + clinic_id mandatory)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Relations
    conversation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)

    # External reference (WA wamid / IG msg id)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Sender
    sender_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sender_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Content
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_kind: Mapped[str | None] = mapped_column(String(50), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    media_duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_phi_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Whisper STT (SC-02)
    transcription_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcription_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Retraction state (SC-01 Action Receipts)
    retracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retracted_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    retracted_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    retract_succeeded: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Context snapshot at send time
    handler_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="ai")

    # AI cost tracking
    cache_hit_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    llm_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)

    # Delivery timeline
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
