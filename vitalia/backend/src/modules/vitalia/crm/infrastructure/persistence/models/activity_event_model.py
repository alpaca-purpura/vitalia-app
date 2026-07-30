# cap: crm.crm-consent-optout
# story-origin: TBD
"""ActivityEventModel — SQLAlchemy 2.0 mapped class for vitalia_activity_events.

Infrastructure layer — ORM model only. No domain logic.

PHI dual-filter (hipaa-lite.md): every query MUST filter by tenant_id AND clinic_id.
ActivityStream: 8 last events per conversation (SC-01), ordered by occurred_at DESC.

payload_sanitized stores PHI-scrubbed event metadata (PII sanitized at service layer
before write — sanitize_payload(compliance_level='hipaa_lite')).

downstream-regression-na: brand-local vitalia CRM infra model
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class ActivityEventModel(Base):
    """SQLAlchemy model for vitalia_activity_events table.

    PHI fields:
    - clinic_id: second scope filter (HIPAA-lite dual filter)
    - payload_sanitized: JSON blob — PII already scrubbed (service enforces)

    All timestamp columns use timezone=True (TIMESTAMPTZ at DB level).
    """

    __tablename__ = "vitalia_activity_events"
    __table_args__ = (
        Index(
            "ix_vitalia_activity_events_tenant_clinic",
            "tenant_id",
            "clinic_id",
        ),
        Index(
            "ix_vitalia_activity_events_conversation_id",
            "conversation_id",
        ),
        Index(
            "ix_vitalia_activity_events_occurred_at",
            "occurred_at",
        ),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # PHI dual-filter keys (hipaa-lite.md: tenant_id + clinic_id mandatory)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # Relations
    conversation_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    source_trace_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Event classification
    event_kind: Mapped[str] = mapped_column(String(100), nullable=False)
    description_es: Mapped[str] = mapped_column(Text, nullable=False)

    # Agent attribution
    agent_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timeline
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Debugging payload (PII-sanitized — NEVER render raw in UI)
    payload_sanitized: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[assignment]

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # deleted_at present for CompoundScopeRepositoryBase compatibility;
    # ActivityEvents are append-only projections (corrections = new event with correction kind).
    # This column stays NULL; hard delete is forbidden per hipaa-lite.md.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
