# cap: crm.crm-consent-optout
# story-origin: TBD
"""ActionReceiptModel — SQLAlchemy 2.0 mapped class for vitalia_action_receipts.

Infrastructure layer — ORM model only. No domain logic.

PHI dual-filter (hipaa-lite.md): every query MUST filter by tenant_id AND clinic_id.
SC-01 Action Receipts: tracks 5min undo window per AI message.

State machine:
- ACTIVE:             retracted_at=None, expires_at=future
- RETRACTED_SUCCESS:  retracted_at=<ts>, retract_succeeded=True
- RETRACTED_FALLBACK: retracted_at=<ts>, retract_succeeded=False
- EXPIRED:            retracted_at=<ts>, retract_reason='expired'
- INVALIDATED:        retract_reason='patient_replied'

OCC: updated_at used for state change tracking.

downstream-regression-na: brand-local vitalia CRM infra model
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class ActionReceiptModel(Base):
    """SQLAlchemy model for vitalia_action_receipts table.

    PHI fields:
    - clinic_id: second scope filter (HIPAA-lite dual filter)
    - message_id: references PHI message entity

    All timestamp columns use timezone=True (TIMESTAMPTZ at DB level).
    """

    __tablename__ = "vitalia_action_receipts"
    __table_args__ = (
        Index(
            "ix_vitalia_action_receipts_tenant_clinic",
            "tenant_id",
            "clinic_id",
        ),
        Index(
            "ix_vitalia_action_receipts_message_id",
            "message_id",
        ),
        Index(
            "ix_vitalia_action_receipts_expires_at",
            "expires_at",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # PHI dual-filter keys (hipaa-lite.md: tenant_id + clinic_id mandatory)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Relations
    message_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Expiry window (5min from message sent_at per ACTION_RECEIPT_WINDOW_MINUTES)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Retraction state
    retracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retract_succeeded: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    retract_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # deleted_at present for CompoundScopeRepositoryBase compatibility;
    # ActionReceipts are NOT soft-deleted (they are state machines).
    # This column stays NULL; hard delete is forbidden per hipaa-lite.md.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
