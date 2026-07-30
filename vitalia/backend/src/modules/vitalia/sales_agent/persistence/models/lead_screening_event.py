# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""SQLAlchemy 2.0 ORM model — LeadScreeningEventModel.

Maps to ``lead_screening_events`` table (created in
017_vitalia_lead_screening_events.py).

PHI table per vitalia/.claude/rules/hipaa-lite.md:
  - dual filter ``tenant_id`` + ``clinic_id`` mandatory on all queries
  - ``response_text`` and ``reasoning`` must pass through
    ``sanitize_payload(..., compliance_level='hipaa_lite')`` before write
  - audit log row required on every read/write of this entity

Column shapes mirror the migration DDL exactly.
Outcome values constrained by migration 021 CHECK constraint:
  ('ok_proceed', 'derivar_doctor', 'derivar_emergencia', 'awaiting_response')
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class LeadScreeningEventModel(Base):
    """ORM mapping for ``lead_screening_events``.

    PHI table — queries MUST filter both tenant_id AND clinic_id.
    Soft-delete only (set deleted_at, never hard-delete).
    """

    __tablename__ = "lead_screening_events"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    lead_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    questions_asked: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    response_text: Mapped[str | None] = mapped_column(String, nullable=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reasoning: Mapped[str | None] = mapped_column(String, nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_lead_screening_events_tenant_clinic_lead",
            "tenant_id",
            "clinic_id",
            "lead_id",
        ),
        Index(
            "ix_lead_screening_events_tenant_vertical_outcome",
            "tenant_id",
            "vertical",
            "outcome",
        ),
    )

    def __repr__(self) -> str:
        """Return debug-friendly representation."""
        return f"<LeadScreeningEventModel id={self.id} lead_id={self.lead_id} outcome={self.outcome}>"
