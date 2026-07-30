# cap: crm.crm-consent-optout
# story-origin: TBD
"""ConversationModel — SQLAlchemy 2.0 mapped class for vitalia_conversations.

Infrastructure layer — ORM model only. No domain logic.

PHI dual-filter (hipaa-lite.md): every query MUST filter by tenant_id AND clinic_id.
Soft-delete: deleted_at=NULL means active; never use hard DELETE.

SC-01: Conversation is the root aggregate for inbox feature.
OCC: updated_at used for optimistic concurrency control on handler_mode updates.

downstream-regression-na: brand-local vitalia CRM infra model
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class ConversationModel(Base):
    """SQLAlchemy model for vitalia_conversations table.

    PHI columns:
    - clinic_id: second scope filter (HIPAA-lite dual filter)
    - lead_id, patient_id: references to PHI entities

    All timestamp columns use timezone=True (TIMESTAMPTZ at DB level).
    """

    __tablename__ = "vitalia_conversations"
    __table_args__ = (
        Index(
            "ix_vitalia_conversations_tenant_clinic",
            "tenant_id",
            "clinic_id",
        ),
        Index(
            "ix_vitalia_conversations_tenant_clinic_status",
            "tenant_id",
            "clinic_id",
            "status",
        ),
        Index(
            "ix_vitalia_conversations_lead_id",
            "lead_id",
        ),
        Index(
            "ix_vitalia_conversations_channel_external_id",
            "channel_external_id",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # PHI dual-filter keys (hipaa-lite.md: tenant_id + clinic_id mandatory)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Relations
    lead_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    patient_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Channel
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    channel_external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # State machine (SC-01)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    handler_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="ai")

    # Workflow flags
    proposal_required: Mapped[bool] = mapped_column(nullable=False, default=False)
    pause_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    help_needed: Mapped[bool] = mapped_column(nullable=False, default=False)
    help_needed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    unread_media_count: Mapped[int] = mapped_column(nullable=False, default=0)

    # Last message snapshot
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message_preview: Mapped[str | None] = mapped_column(String(500), nullable=True)
    messages_count: Mapped[int] = mapped_column(nullable=False, default=0)

    # CRM stage
    stage_decision: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linked_offer_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
